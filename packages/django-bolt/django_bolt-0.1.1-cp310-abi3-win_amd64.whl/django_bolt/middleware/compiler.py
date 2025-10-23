"""Middleware compilation utilities."""
from typing import Any, Callable, Dict, List, Optional, Set
from ..auth.backends import get_default_authentication_classes
from ..auth.guards import get_default_permission_classes


def compile_middleware_meta(
    handler: Callable,
    method: str,
    path: str,
    global_middleware: List[Any],
    global_middleware_config: Dict[str, Any],
    guards: Optional[List[Any]] = None,
    auth: Optional[List[Any]] = None
) -> Optional[Dict[str, Any]]:
    """Compile middleware metadata for a handler, including guards and auth."""
    # Check for handler-specific middleware
    handler_middleware = []
    skip_middleware: Set[str] = set()

    if hasattr(handler, '__bolt_middleware__'):
        handler_middleware = handler.__bolt_middleware__

    if hasattr(handler, '__bolt_skip_middleware__'):
        skip_middleware = handler.__bolt_skip_middleware__

    # Merge global and handler middleware
    all_middleware = []

    # Add global middleware first
    for mw in global_middleware:
        mw_dict = middleware_to_dict(mw)
        if mw_dict and mw_dict.get('type') not in skip_middleware:
            all_middleware.append(mw_dict)

    # Add global config-based middleware
    if global_middleware_config:
        for mw_type, config in global_middleware_config.items():
            if mw_type not in skip_middleware:
                mw_dict = {'type': mw_type}
                mw_dict.update(config)
                all_middleware.append(mw_dict)

    # Add handler-specific middleware
    for mw in handler_middleware:
        mw_dict = middleware_to_dict(mw)
        if mw_dict:
            all_middleware.append(mw_dict)

    # Compile authentication backends
    auth_backends = []
    if auth is not None:
        # Per-route auth override
        for auth_backend in auth:
            if hasattr(auth_backend, 'to_metadata'):
                auth_backends.append(auth_backend.to_metadata())
    else:
        # Use global default authentication classes
        for auth_backend in get_default_authentication_classes():
            if hasattr(auth_backend, 'to_metadata'):
                auth_backends.append(auth_backend.to_metadata())

    # Compile guards/permissions
    guard_list = []
    if guards is not None:
        # Per-route guards override
        for guard in guards:
            # Check if it's an instance with to_metadata method
            if hasattr(guard, 'to_metadata') and callable(getattr(guard, 'to_metadata', None)):
                try:
                    # Try calling as instance method
                    guard_list.append(guard.to_metadata())
                except TypeError:
                    # If it fails, might be a class, try instantiating
                    try:
                        instance = guard()
                        guard_list.append(instance.to_metadata())
                    except Exception:
                        pass
            elif isinstance(guard, type):
                # It's a class reference, instantiate it
                try:
                    instance = guard()
                    if hasattr(instance, 'to_metadata'):
                        guard_list.append(instance.to_metadata())
                except Exception:
                    pass
    else:
        # Use global default permission classes
        for guard in get_default_permission_classes():
            if hasattr(guard, 'to_metadata'):
                guard_list.append(guard.to_metadata())

    # Only include metadata if something is configured
    # Note: include result even when only skip flags are present so Rust can
    #       honor route-level skips like `compression`.
    if not all_middleware and not auth_backends and not guard_list and not skip_middleware:
        return None

    result = {
        'method': method,
        'path': path
    }

    if all_middleware:
        result['middleware'] = all_middleware

    # Always include skip flags if present (even without middleware/auth/guards)
    if skip_middleware:
        result['skip'] = list(skip_middleware)

    if auth_backends:
        result['auth_backends'] = auth_backends

    if guard_list:
        result['guards'] = guard_list

    return result


def middleware_to_dict(mw: Any) -> Optional[Dict[str, Any]]:
    """Convert middleware specification to dictionary."""
    if isinstance(mw, dict):
        return mw
    elif hasattr(mw, '__dict__'):
        # Convert middleware object to dict
        return {
            'type': mw.__class__.__name__.lower().replace('middleware', ''),
            **mw.__dict__
        }
    return None
