"""Request parsing utilities for form and multipart data."""
from typing import Any, Dict, Tuple
from io import BytesIO
import multipart

# Cache for max upload size (read once from Django settings)
_MAX_UPLOAD_SIZE = None


def get_max_upload_size() -> int:
    """Get max upload size from Django settings (cached after first call)."""
    global _MAX_UPLOAD_SIZE
    if _MAX_UPLOAD_SIZE is None:
        try:
            from django.conf import settings
            _MAX_UPLOAD_SIZE = getattr(settings, 'BOLT_MAX_UPLOAD_SIZE', 10 * 1024 * 1024)  # 10MB default
        except ImportError:
            _MAX_UPLOAD_SIZE = 10 * 1024 * 1024
    return _MAX_UPLOAD_SIZE


def parse_form_data(request: Dict[str, Any], headers_map: Dict[str, str]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Parse form and multipart data from request using python "multipart" library."""
    content_type = headers_map.get("content-type", "")

    # Early return if not form data (optimization for JSON/empty requests)
    if not content_type.startswith(("application/x-www-form-urlencoded", "multipart/form-data")):
        return {}, {}

    form_map: Dict[str, Any] = {}
    files_map: Dict[str, Any] = {}

    if content_type.startswith("application/x-www-form-urlencoded"):
        from urllib.parse import parse_qs
        body_bytes: bytes = request["body"]
        form_data = parse_qs(body_bytes.decode("utf-8"))
        # parse_qs returns lists, but for single values we want the value directly
        form_map = {k: v[0] if len(v) == 1 else v for k, v in form_data.items()}
    elif content_type.startswith("multipart/form-data"):
        form_map, files_map = parse_multipart_data(request, content_type)

    return form_map, files_map


def parse_multipart_data(request: Dict[str, Any], content_type: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Parse multipart form data using python "multipart" library.

    SECURITY: Uses battle-tested multipart library with proper boundary validation,
    size limits, and header parsing.
    """

    form_map: Dict[str, Any] = {}
    files_map: Dict[str, Any] = {}

    # Parse content-type header to get boundary
    content_type_parsed, content_type_options = multipart.parse_options_header(content_type)

    if content_type_parsed != 'multipart/form-data':
        return form_map, files_map

    boundary = content_type_options.get('boundary')
    if not boundary:
        return form_map, files_map

    # SECURITY: Validate boundary (multipart does this, but explicit check)
    if not boundary or len(boundary) > 200:  # RFC 2046 suggests max 70, we allow 200
        return form_map, files_map

    # Get max upload size (cached from Django settings)
    max_size = get_max_upload_size()

    body_bytes: bytes = request["body"]

    # SECURITY: Check body size before parsing
    if len(body_bytes) > max_size:
        raise ValueError(f"Upload size {len(body_bytes)} exceeds maximum {max_size} bytes")

    # Create a file-like object from bytes
    body_file = BytesIO(body_bytes)

    # Parse using multipart library
    try:
        parser = multipart.MultipartParser(
            body_file,
            boundary=boundary.encode() if isinstance(boundary, str) else boundary,
            content_length=len(body_bytes),
            memory_limit=max_size,
            disk_limit=0,  # Don't allow disk spooling for security
            part_limit=100  # Limit number of parts
        )

        # Iterate through parts
        for part in parser:
            name = part.name
            if not name:
                continue

            # Check if it's a file or form field
            if part.filename:
                # It's a file upload
                content = part.file.read()
                file_info = {
                    "filename": part.filename,
                    "content": content,
                    "content_type": part.content_type,
                    "size": len(content)
                }

                if name in files_map:
                    if isinstance(files_map[name], list):
                        files_map[name].append(file_info)
                    else:
                        files_map[name] = [files_map[name], file_info]
                else:
                    files_map[name] = file_info
            else:
                # It's a form field
                form_map[name] = part.value

    except Exception as e:
        # Return empty maps on parse error (don't expose internal errors)
        import logging
        import traceback
        logging.warning(f"Multipart parsing failed: {e}\n{traceback.format_exc()}")
        return {}, {}

    return form_map, files_map
