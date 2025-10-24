import inspect
import pytest
from typing import TypeVar, get_type_hints, get_args, get_origin
import asyncio

from aiware.client.async_client import AsyncAiware
from aiware.client.client import Aiware

def get_method_signature(method):
    """Extract method signature including type hints."""
    sig = inspect.signature(method)
    try:
        hints = get_type_hints(method)
    except Exception:
        # If type hints can't be resolved, use annotations directly
        hints = getattr(method, '__annotations__', {})
    
    return {
        'parameters': {
            name: {
                'annotation': hints.get(name, param.annotation),
                'default': param.default,
                'kind': param.kind
            }
            for name, param in sig.parameters.items()
        },
        'return': hints.get('return', sig.return_annotation)
    }


def normalize_type(type_hint):
    """Normalize types for comparison, handling Awaitable/Coroutine differences and generics."""
    if type_hint is inspect.Parameter.empty or type_hint is inspect.Signature.empty:
        return None
    
    origin = get_origin(type_hint)
    args = get_args(type_hint)
    
    # Handle Coroutine[Any, Any, T] -> extract T
    if origin is not None and hasattr(origin, '__name__'):
        if origin.__name__ in ('Coroutine', 'Awaitable'):
            # For async methods, extract the actual return type
            if args:
                return normalize_type(args[-1])  # Last arg is the return type
    
    # Handle TypeVar - compare by name instead of identity
    if isinstance(type_hint, TypeVar):
        return ('TypeVar', type_hint.__name__, type_hint.__constraints__, type_hint.__bound__)
    
    # For generic types, create a comparable representation
    if origin is not None:
        if args:
            # Normalize all type arguments recursively
            normalized_args = tuple(normalize_type(arg) for arg in args)
            return (origin, normalized_args)
        return origin
    
    # Handle generic aliases (like MyClass[T]) that don't have __origin__
    # These have __module__, __name__, and __args__ attributes
    if hasattr(type_hint, '__args__') and hasattr(type_hint, '__origin__'):
        origin = type_hint.__origin__
        args = type_hint.__args__
        normalized_args = tuple(normalize_type(arg) for arg in args)
        # Use the qualified name for better comparison
        if hasattr(origin, '__module__') and hasattr(origin, '__qualname__'):
            origin_repr = f"{origin.__module__}.{origin.__qualname__}"
            return (origin_repr, normalized_args)
        return (origin, normalized_args)
    
    # For regular classes, use module + qualname for comparison
    if hasattr(type_hint, '__module__') and hasattr(type_hint, '__qualname__'):
        return f"{type_hint.__module__}.{type_hint.__qualname__}"
    
    # Handle string annotations (forward references)
    if isinstance(type_hint, str):
        return type_hint
    
    return type_hint


def get_public_methods(cls):
    """Get all public methods (not starting with _) from a class."""
    methods = {}
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        if not name.startswith('_'):
            methods[name] = method
    return methods


def compare_signatures(sync_sig, async_sig, method_name):
    """Compare two method signatures, accounting for async differences."""
    errors = []
    
    # Compare parameters
    sync_params = sync_sig['parameters']
    async_params = async_sig['parameters']
    
    if set(sync_params.keys()) != set(async_params.keys()):
        errors.append(
            f"Parameter names differ: sync has {set(sync_params.keys())}, "
            f"async has {set(async_params.keys())}"
        )
        return errors
    
    for param_name in sync_params:
        sync_param = sync_params[param_name]
        async_param = async_params[param_name]
        
        # Compare annotations
        sync_type = normalize_type(sync_param['annotation'])
        async_type = normalize_type(async_param['annotation'])
        
        if sync_type != async_type:
            errors.append(
                f"Parameter '{param_name}' type differs: "
                f"sync={sync_type}, async={async_type}"
            )
        
        # Compare defaults
        if sync_param['default'] != async_param['default']:
            errors.append(
                f"Parameter '{param_name}' default differs: "
                f"sync={sync_param['default']}, async={async_param['default']}"
            )
        
        # Compare parameter kind (positional, keyword, etc.)
        if sync_param['kind'] != async_param['kind']:
            errors.append(
                f"Parameter '{param_name}' kind differs: "
                f"sync={sync_param['kind']}, async={async_param['kind']}"
            )
    
    # Compare return types (normalize for async)
    sync_return = normalize_type(sync_sig['return'])
    async_return = normalize_type(async_sig['return'])
    
    if sync_return != async_return:
        errors.append(
            f"Return type differs: sync={sync_return}, async={async_return}"
        )
    
    return errors


def assert_sync_async_method_parity(sync_class, async_class, exclude_methods=None, allow_sync_in_async=False):
    """
    Test that sync and async versions of a class have matching methods.
    
    Args:
        sync_class: The synchronous version of the class
        async_class: The asynchronous version of the class
        exclude_methods: Optional set/list of method names to exclude from comparison
        allow_sync_in_async: If True, allows async class to have sync methods alongside async ones
    
    Usage:
        test_sync_async_method_parity(MyClient, AsyncMyClient)
        test_sync_async_method_parity(MyClient, AsyncMyClient, exclude_methods={'close', 'connect'})
        test_sync_async_method_parity(MyClient, AsyncMyClient, allow_sync_in_async=True)
    """
    exclude_methods = set(exclude_methods or [])
    
    sync_methods = get_public_methods(sync_class)
    async_methods = get_public_methods(async_class)
    
    # Remove excluded methods
    for method_name in exclude_methods:
        sync_methods.pop(method_name, None)
        async_methods.pop(method_name, None)
    
    sync_method_names = set(sync_methods.keys())
    async_method_names = set(async_methods.keys())
    
    # Check for missing methods
    missing_in_async = sync_method_names - async_method_names
    missing_in_sync = async_method_names - sync_method_names
    
    errors = []
    
    if missing_in_async:
        errors.append(
            f"Methods in sync class but missing in async class: {missing_in_async}"
        )
    
    if missing_in_sync:
        errors.append(
            f"Methods in async class but missing in sync class: {missing_in_sync}"
        )
    
    # Check that async methods are actually async
    for name in async_method_names:
        is_async = asyncio.iscoroutinefunction(async_methods[name])
        
        if not is_async and not allow_sync_in_async:
            errors.append(
                f"Method '{name}' in async class is not an async method. "
                f"Use allow_sync_in_async=True if this is intentional."
            )
    
    # Check that sync methods are not async
    for name in sync_method_names:
        if asyncio.iscoroutinefunction(sync_methods[name]):
            errors.append(
                f"Method '{name}' in sync class should not be an async method"
            )
    
    # Compare signatures for common methods
    common_methods = sync_method_names & async_method_names
    
    for method_name in common_methods:
        sync_method = sync_methods[method_name]
        async_method = async_methods[method_name]
        
        # If async class has a sync method and we allow it, compare directly
        is_async_method = asyncio.iscoroutinefunction(async_method)
        
        if not is_async_method and allow_sync_in_async:
            # Both should be sync, compare as-is
            sync_sig = get_method_signature(sync_method)
            async_sig = get_method_signature(async_method)
            
            sig_errors = compare_signatures(sync_sig, async_sig, method_name)
        else:
            # Normal async comparison
            sync_sig = get_method_signature(sync_method)
            async_sig = get_method_signature(async_method)
            
            sig_errors = compare_signatures(sync_sig, async_sig, method_name)
        
        if sig_errors:
            errors.append(
                f"Method '{method_name}' signature mismatch:\n  " + 
                "\n  ".join(sig_errors)
            )
    
    # Assert all checks passed
    if errors:
        pytest.fail(
            f"\n\nSync/Async parity check failed for {sync_class.__name__} "
            f"and {async_class.__name__}:\n\n" + 
            "\n\n".join(errors)
        )


# Actual test function
def test_client_method_signature_parity():
    """Test that Aiware and AsyncAiware have matching methods."""
    assert_sync_async_method_parity(Aiware, AsyncAiware, exclude_methods={"execute_ws"}, allow_sync_in_async=True)
