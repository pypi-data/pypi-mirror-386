"""Error handlers for Django-Bolt.

Provides default exception handlers that convert Python exceptions into
structured HTTP error responses.
"""

import msgspec
import traceback
from typing import Any, Dict, List, Tuple, Optional
from . import _json
from .exceptions import (
    HTTPException,
    RequestValidationError,
    ResponseValidationError,
    ValidationException,
    InternalServerError,
)


def format_error_response(
    status_code: int,
    detail: Any,
    headers: Optional[Dict[str, str]] = None,
    extra: Optional[Dict[str, Any] | List[Any]] = None,
) -> Tuple[int, List[Tuple[str, str]], bytes]:
    """Format an error response.

    Args:
        status_code: HTTP status code
        detail: Error detail (string or structured data)
        headers: Optional HTTP headers
        extra: Optional extra data to include in response

    Returns:
        Tuple of (status_code, headers, body)
    """
    error_body: Dict[str, Any] = {"detail": detail}

    if extra is not None:
        error_body["extra"] = extra

    body_bytes = _json.encode(error_body)

    response_headers = [("content-type", "application/json")]
    if headers:
        response_headers.extend(headers.items())

    return status_code, response_headers, body_bytes


def http_exception_handler(exc: HTTPException) -> Tuple[int, List[Tuple[str, str]], bytes]:
    """Handle HTTPException and convert to error response.

    Args:
        exc: HTTPException instance

    Returns:
        Tuple of (status_code, headers, body)
    """
    return format_error_response(
        status_code=exc.status_code,
        detail=exc.detail,
        headers=exc.headers,
        extra=exc.extra,
    )


def msgspec_validation_error_to_dict(error: msgspec.ValidationError) -> List[Dict[str, Any]]:
    """Convert msgspec ValidationError to structured error list.

    Args:
        error: msgspec.ValidationError instance

    Returns:
        List of error dictionaries with 'loc', 'msg', 'type' fields
    """
    # msgspec.ValidationError doesn't provide structured error info like pydantic
    # We'll do our best to parse the error message
    error_msg = str(error)

    # Try to extract field path from error message
    # Example: "Expected `int`, got `str` - at `$[0].age`"
    # Example: "Object missing required field `name`"

    errors = []

    # Check if error message contains field location
    if " - at `" in error_msg:
        msg_part, loc_part = error_msg.split(" - at `", 1)
        loc_path = loc_part.rstrip("`")
        # Parse location like $[0].age into ["body", 0, "age"]
        loc_parts = ["body"]
        # Simple parsing - can be improved
        loc_parts.append(loc_path.replace("$", "").replace("[", ".").replace("]", "").strip("."))
    elif "missing required field" in error_msg.lower():
        # Extract field name from message
        import re
        match = re.search(r"`(\w+)`", error_msg)
        field = match.group(1) if match else "unknown"
        errors.append({
            "loc": ["body", field],
            "msg": error_msg,
            "type": "missing_field",
        })
        return errors
    else:
        # Generic error without location
        errors.append({
            "loc": ["body"],
            "msg": error_msg,
            "type": "validation_error",
        })
        return errors

    errors.append({
        "loc": loc_parts if isinstance(loc_parts, list) else ["body"],
        "msg": error_msg.split(" - at `")[0] if " - at `" in error_msg else error_msg,
        "type": "validation_error",
    })

    return errors


def request_validation_error_handler(
    exc: RequestValidationError,
) -> Tuple[int, List[Tuple[str, str]], bytes]:
    """Handle RequestValidationError and convert to 422 response.

    Args:
        exc: RequestValidationError instance

    Returns:
        Tuple of (status_code, headers, body)
    """
    errors = exc.errors()

    # Convert errors to structured format if needed
    formatted_errors = []
    for error in errors:
        if isinstance(error, dict):
            formatted_errors.append(error)
        elif isinstance(error, msgspec.ValidationError):
            formatted_errors.extend(msgspec_validation_error_to_dict(error))
        else:
            # Generic error
            formatted_errors.append({
                "loc": ["body"],
                "msg": str(error),
                "type": "validation_error",
            })

    return format_error_response(
        status_code=422,
        detail=formatted_errors,
    )


def response_validation_error_handler(
    exc: ResponseValidationError,
) -> Tuple[int, List[Tuple[str, str]], bytes]:
    """Handle ResponseValidationError and convert to 500 response.

    Args:
        exc: ResponseValidationError instance

    Returns:
        Tuple of (status_code, headers, body)
    """
    # Log the error (if logging is configured)
    errors = exc.errors()

    formatted_errors = []
    for error in errors:
        if isinstance(error, dict):
            formatted_errors.append(error)
        elif isinstance(error, msgspec.ValidationError):
            formatted_errors.extend(msgspec_validation_error_to_dict(error))
        else:
            formatted_errors.append({
                "loc": ["response"],
                "msg": str(error),
                "type": "validation_error",
            })

    return format_error_response(
        status_code=500,
        detail="Response validation error",
        extra={"validation_errors": formatted_errors},
    )


def generic_exception_handler(
    exc: Exception,
    debug: bool = False,
    request: Optional[Any] = None,  # noqa: ARG001 - kept for API compatibility
) -> Tuple[int, List[Tuple[str, str]], bytes]:
    """Handle generic exceptions and convert to 500 response.

    Args:
        exc: Exception instance
        debug: Whether to include traceback in response
        request: Optional request dict or Django request object for ExceptionReporter

    Returns:
        Tuple of (status_code, headers, body)
    """
    detail = "Internal Server Error"
    extra = None

    if debug:
        # Try to use Django's ExceptionReporter HTML page
        try:
            from django.views.debug import ExceptionReporter

            # ExceptionReporter works fine with None request (avoids URL resolution issues)
            reporter = ExceptionReporter(None, type(exc), exc, exc.__traceback__)
            html_content = reporter.get_traceback_html()

            # Return HTML response instead of JSON
            return (
                500,
                [("content-type", "text/html; charset=utf-8")],
                html_content.encode("utf-8")
            )
        except Exception:
            # Fallback to standard traceback formatting in JSON
            pass

        # Fallback to JSON with traceback
        tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
        # Split into individual lines for better JSON display, stripping trailing newlines
        tb_formatted = [line.rstrip('\n') for line in ''.join(tb_lines).split('\n') if line.strip()]
        extra = {
            "exception": str(exc),
            "exception_type": type(exc).__name__,
            "traceback": tb_formatted,
        }
        detail = f"{type(exc).__name__}: {str(exc)}"

    return format_error_response(
        status_code=500,
        detail=detail,
        extra=extra,
    )


def handle_exception(
    exc: Exception,
    debug: Optional[bool] = None,
    request: Optional[Any] = None,
) -> Tuple[int, List[Tuple[str, str]], bytes]:
    """Main exception handler that routes to specific handlers.

    Args:
        exc: Exception instance
        debug: Whether to include debug information. If None, will check Django DEBUG setting.
              If explicitly False, will not show debug info even if Django DEBUG=True.
        request: Optional request object for Django ExceptionReporter

    Returns:
        Tuple of (status_code, headers, body)
    """
    # Check Django's DEBUG setting dynamically only if debug is not explicitly set
    if debug is None:
        try:
            from django.conf import settings
            if settings.configured:
                debug = settings.DEBUG
            else:
                debug = False
        except (ImportError, AttributeError):
            debug = False

    if isinstance(exc, HTTPException):
        return http_exception_handler(exc)
    elif isinstance(exc, RequestValidationError):
        return request_validation_error_handler(exc)
    elif isinstance(exc, ResponseValidationError):
        return response_validation_error_handler(exc)
    elif isinstance(exc, ValidationException):
        # Generic validation exception
        return request_validation_error_handler(
            RequestValidationError(exc.errors())
        )
    elif isinstance(exc, msgspec.ValidationError):
        # Direct msgspec validation error
        errors = msgspec_validation_error_to_dict(exc)
        return format_error_response(
            status_code=422,
            detail=errors,
        )
    elif isinstance(exc, FileNotFoundError):
        # FileNotFoundError from FileResponse - return 404
        return format_error_response(
            status_code=404,
            detail=str(exc) or "File not found",
        )
    elif isinstance(exc, PermissionError):
        # PermissionError from FileResponse path validation - return 403
        return format_error_response(
            status_code=403,
            detail=str(exc) or "Permission denied",
        )
    else:
        # Generic exception
        return generic_exception_handler(exc, debug=debug, request=request)
