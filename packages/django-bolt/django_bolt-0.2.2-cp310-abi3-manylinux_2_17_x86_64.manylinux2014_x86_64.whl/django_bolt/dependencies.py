"""Dependency injection utilities."""
import inspect
from typing import Any, Callable, Dict, List, TYPE_CHECKING
from .params import Depends as DependsMarker
from .binding import convert_primitive

if TYPE_CHECKING:
    from .typing import FieldDefinition


async def resolve_dependency(
    dep_fn: Callable,
    depends_marker: DependsMarker,
    request: Dict[str, Any],
    dep_cache: Dict[Any, Any],
    params_map: Dict[str, Any],
    query_map: Dict[str, Any],
    headers_map: Dict[str, str],
    cookies_map: Dict[str, str],
    handler_meta: Dict[Callable, Dict[str, Any]],
    compile_binder: Callable,
    http_method: str,
    path: str
) -> Any:
    """
    Resolve a dependency injection.

    Args:
        dep_fn: Dependency function to resolve
        depends_marker: Depends marker with cache settings
        request: Request dict
        dep_cache: Cache for resolved dependencies
        params_map: Path parameters
        query_map: Query parameters
        headers_map: Request headers
        cookies_map: Request cookies
        handler_meta: Metadata cache for handlers
        compile_binder: Function to compile parameter binding metadata
        http_method: HTTP method of the handler using this dependency
        path: Path of the handler using this dependency

    Returns:
        Resolved dependency value
    """
    if depends_marker.use_cache and dep_fn in dep_cache:
        return dep_cache[dep_fn]

    dep_meta = handler_meta.get(dep_fn)
    if dep_meta is None:
        # Compile dependency metadata with the actual HTTP method and path
        # Dependencies MUST be validated against HTTP method constraints
        # e.g., a dependency with Body() can't be used in GET handlers
        dep_meta = compile_binder(dep_fn, http_method, path)
        handler_meta[dep_fn] = dep_meta

    if dep_meta.get("mode") == "request_only":
        value = await dep_fn(request)
    else:
        value = await call_dependency(
            dep_fn, dep_meta, request, params_map,
            query_map, headers_map, cookies_map
        )

    if depends_marker.use_cache:
        dep_cache[dep_fn] = value

    return value


async def call_dependency(
    dep_fn: Callable,
    dep_meta: Dict[str, Any],
    request: Dict[str, Any],
    params_map: Dict[str, Any],
    query_map: Dict[str, Any],
    headers_map: Dict[str, str],
    cookies_map: Dict[str, str]
) -> Any:
    """Call a dependency function with resolved parameters."""
    dep_args: List[Any] = []
    dep_kwargs: Dict[str, Any] = {}

    # Use FieldDefinition objects directly
    for field in dep_meta["fields"]:
        if field.source == "request":
            dval = request
        else:
            dval = extract_dependency_value(field, params_map, query_map, headers_map, cookies_map)

        if field.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
            dep_args.append(dval)
        else:
            dep_kwargs[field.name] = dval

    return await dep_fn(*dep_args, **dep_kwargs)


def extract_dependency_value(
    field: "FieldDefinition",
    params_map: Dict[str, Any],
    query_map: Dict[str, Any],
    headers_map: Dict[str, str],
    cookies_map: Dict[str, str]
) -> Any:
    """Extract value for a dependency parameter using FieldDefinition.

    Args:
        field: FieldDefinition object describing the parameter
        params_map: Path parameters
        query_map: Query parameters
        headers_map: Request headers
        cookies_map: Request cookies

    Returns:
        Extracted and converted parameter value
    """
    key = field.alias or field.name

    if key in params_map:
        return convert_primitive(str(params_map[key]), field.annotation)
    elif key in query_map:
        return convert_primitive(str(query_map[key]), field.annotation)
    elif field.source == "header":
        raw = headers_map.get(key.lower())
        if raw is None:
            raise ValueError(f"Missing required header: {key}")
        return convert_primitive(str(raw), field.annotation)
    elif field.source == "cookie":
        raw = cookies_map.get(key)
        if raw is None:
            raise ValueError(f"Missing required cookie: {key}")
        return convert_primitive(str(raw), field.annotation)
    else:
        return None
