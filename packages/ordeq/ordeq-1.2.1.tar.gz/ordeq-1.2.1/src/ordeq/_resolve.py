"""Resolve packages and modules to nodes and IOs."""

import importlib
import pkgutil
from collections.abc import Callable, Generator, Iterable, Sequence
from types import ModuleType
from typing import Any

from ordeq._hook import NodeHook, RunHook
from ordeq._io import IO, Input, Output
from ordeq._nodes import Node, get_node


def _is_module(obj: object) -> bool:
    return isinstance(obj, ModuleType)


def _is_package(module: ModuleType) -> bool:
    return hasattr(module, "__path__")


def _is_io(obj: object) -> bool:
    return isinstance(obj, (IO, Input, Output))


def _get_io_sequence(value: Any) -> list[Input | Output | IO]:
    if _is_io(value):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [io for v in value for io in _get_io_sequence(v)]
    if isinstance(value, dict):
        return [io for v in value.values() for io in _get_io_sequence(v)]
    return []


def _is_io_sequence(value: Any) -> bool:
    return bool(_get_io_sequence(value))


def _is_node(obj: object) -> bool:
    return (
        callable(obj)
        and hasattr(obj, "__ordeq_node__")
        and isinstance(obj.__ordeq_node__, Node)
    )


def _resolve_string_to_module(name: str) -> ModuleType:
    return importlib.import_module(name)


def _resolve_packages_to_modules(
    modules: Iterable[tuple[str, ModuleType]],
) -> Generator[tuple[str, ModuleType], None, None]:
    for name, module in modules:
        yield name, module
        if _is_package(module):
            submodules = (
                importlib.import_module(f".{name}", package=module.__name__)
                for _, name, _ in pkgutil.iter_modules(module.__path__)
            )
            yield from _resolve_packages_to_modules(
                (mod.__name__, mod) for mod in submodules
            )


def _resolve_runnables_to_modules(
    *runnables: str | ModuleType,
) -> Generator[tuple[str, ModuleType], None, None]:
    modules = {}
    for runnable in runnables:
        if isinstance(runnable, ModuleType):
            modules[runnable.__name__] = runnable
        elif isinstance(runnable, str):
            mod = _resolve_string_to_module(runnable)
            modules[mod.__name__] = mod
        else:
            raise TypeError(
                f"{runnable} is not something we can run. "
                f"Expected a module or a string, got {type(runnable)}"
            )

    # Then, for each module or package, if it's a package, resolve to all its
    # submodules recursively
    return _resolve_packages_to_modules(modules.items())


def _resolve_module_to_nodes(module: ModuleType) -> set[Node]:
    """Gathers all nodes defined in a module.

    Args:
        module: the module to gather nodes from

    Returns:
        the nodes defined in the module

    """

    return {get_node(obj) for obj in vars(module).values() if _is_node(obj)}


def _resolve_module_to_ios(
    module: ModuleType,
) -> dict[tuple[str, str], IO | Input | Output]:
    """Find all `IO` objects defined in the provided module

    Args:
        module: the Python module object

    Returns:
        a dict of `IO` objects with their fully-qualified name as key
    """
    return {
        (module.__name__, name): obj
        for name, obj in vars(module).items()
        if _is_io(obj)
    }


def _resolve_node_reference(ref: str) -> Node:
    """Resolves a node reference string of the form 'module:node_name'.

    Args:
        ref: Reference string, e.g. 'my_package.my_module:my_node'

    Returns:
        The resolved Node object

    Raises:
        ValueError: if the node cannot be found in the module
    """

    if ":" not in ref:
        raise ValueError(f"Invalid node reference: '{ref}'.")
    module_name, _, node_name = ref.partition(":")
    module = _resolve_string_to_module(module_name)
    node_obj = getattr(module, node_name, None)
    if node_obj is None or not _is_node(node_obj):
        raise ValueError(
            f"Node '{node_name}' not found in module '{module_name}'"
        )
    return get_node(node_obj)


def _resolve_hook_reference(ref: str) -> NodeHook | RunHook:
    """Resolves a hook reference string of the form 'package.module:hook_name'.

    Args:
        ref: Reference string, e.g. 'my_package.my_module:my_hook'

    Returns:
        The resolved Hook object.

    Raises:
        ValueError: if the hook cannot be found or is not a valid Hook object.
    """

    if ":" not in ref:
        raise ValueError(f"Invalid hook reference: '{ref}'.")
    module_name, _, hook_name = ref.partition(":")
    module = _resolve_string_to_module(module_name)
    hook_obj = getattr(module, hook_name, None)
    if hook_obj is None or not isinstance(hook_obj, (NodeHook, RunHook)):
        raise ValueError(
            f"Hook '{hook_name}' not found in module '{module_name}'"
        )
    return hook_obj


def _resolve_hooks(
    *hooks: str | NodeHook | RunHook,
) -> tuple[list[RunHook], list[NodeHook]]:
    """Resolves a hook which can be a reference string or a Hook object.

    Args:
        hooks: References to hooks, or hook objects

    Returns:
        A tuple of lists with node hooks and run hooks

    """

    run_hooks = []
    node_hooks = []
    for hook in hooks:
        if isinstance(hook, NodeHook):
            node_hooks.append(hook)
        elif isinstance(hook, RunHook):
            run_hooks.append(hook)
        elif isinstance(hook, str):
            resolved_hook = _resolve_hook_reference(hook)
            if isinstance(resolved_hook, NodeHook):
                node_hooks.append(resolved_hook)
            elif isinstance(resolved_hook, RunHook):
                run_hooks.append(resolved_hook)
    return run_hooks, node_hooks


def _resolve_runnables_to_nodes_and_modules(
    *runnables: str | ModuleType | Callable,
) -> tuple[set[Node], set[ModuleType]]:
    """Collects nodes and modules from the provided runnables.

    Args:
        runnables: modules, packages, node references or callables to gather
            nodes from

    Returns:
        the nodes and modules collected from the runnables

    Raises:
        TypeError: if a runnable is not a module and not a node
    """
    modules_and_strs: list[ModuleType | str] = []
    nodes = set()
    for runnable in runnables:
        if isinstance(runnable, ModuleType) or (
            isinstance(runnable, str) and ":" not in runnable
        ):
            modules_and_strs.append(runnable)
        elif callable(runnable):
            nodes.add(get_node(runnable))
        elif isinstance(runnable, str):
            nodes.add(_resolve_node_reference(runnable))
        else:
            raise TypeError(
                f"{runnable} is not something we can run. "
                f"Expected a module or a node, got {type(runnable)}"
            )

    modules = set(
        dict(_resolve_runnables_to_modules(*modules_and_strs)).values()
    )
    return nodes, modules


def _resolve_runnables_to_nodes(
    *runnables: ModuleType | Callable | str,
) -> set[Node]:
    """Collects nodes from the provided runnables.

    Args:
        runnables: modules, packages, node references or callables to gather
            nodes from

    Returns:
        the nodes collected from the runnables

    """
    nodes, modules = _resolve_runnables_to_nodes_and_modules(*runnables)
    for module in modules:
        nodes.update(_resolve_module_to_nodes(module))
    return nodes


def _check_missing_ios(
    nodes: set[Node], ios: dict[str, IO | Input | Output]
) -> None:
    missing_ios: set[IO | Input | Output] = set()
    for node in nodes:
        for inp in node.inputs:
            if inp not in ios.values():
                missing_ios.add(inp)
        for out in node.outputs:
            if out not in ios.values():
                missing_ios.add(out)

    if missing_ios:
        raise ValueError(
            f"The following IOs are used by nodes but not defined: "
            f"{missing_ios}. Please include the module defining them in "
            f"the runnables."
        )


def _resolve_runnables_to_nodes_and_ios(
    *runnables: str | ModuleType | Callable,
) -> tuple[set[Node], dict[tuple[str, str], IO | Input | Output]]:
    """Collects nodes and IOs from the provided runnables.

    Args:
        runnables: modules, packages, node references or callables to gather
            nodes and IOs from

    Returns:
        a tuple of nodes and IOs collected from the runnables
    """

    ios = {}
    nodes, modules = _resolve_runnables_to_nodes_and_modules(*runnables)
    for node in nodes:
        mod = _resolve_string_to_module(node.func.__module__)
        ios.update(_resolve_module_to_ios(mod))

    for module in modules:
        nodes.update(_resolve_module_to_nodes(module))
        ios.update(_resolve_module_to_ios(module))

    return nodes, ios
