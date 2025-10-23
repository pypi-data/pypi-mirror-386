from __future__ import annotations

import inspect
import msgspec
from typing import TYPE_CHECKING, Any, Dict, List, Optional, get_type_hints, get_origin, get_args, Annotated

from ..typing import is_msgspec_struct, is_optional
from ..params import Param
from .spec import (
    OpenAPI,
    Operation,
    PathItem,
    Parameter,
    RequestBody,
    OpenAPIResponse,
    OpenAPIMediaType,
    Schema,
    Reference,
    SecurityRequirement,
    Tag,
)

if TYPE_CHECKING:
    from ..api import BoltAPI
    from .config import OpenAPIConfig

__all__ = ("SchemaGenerator",)


class SchemaGenerator:
    """Generate OpenAPI schema from BoltAPI routes."""

    def __init__(self, api: BoltAPI, config: OpenAPIConfig) -> None:
        """Initialize schema generator.

        Args:
            api: BoltAPI instance to generate schema for.
            config: OpenAPI configuration.
        """
        self.api = api
        self.config = config
        self.schemas: Dict[str, Schema] = {}  # Component schemas registry

    def generate(self) -> OpenAPI:
        """Generate complete OpenAPI schema.

        Returns:
            OpenAPI schema object.
        """
        openapi = self.config.to_openapi_schema()

        # Generate path items from routes and collect tags
        paths: Dict[str, PathItem] = {}
        collected_tags: set[str] = set()

        for method, path, handler_id, handler in self.api._routes:
            # Skip OpenAPI docs routes (always excluded)
            if path.startswith(self.config.path):
                continue

            # Skip paths based on exclude_paths configuration
            should_exclude = False
            for exclude_prefix in self.config.exclude_paths:
                if path.startswith(exclude_prefix):
                    should_exclude = True
                    break

            if should_exclude:
                continue

            if path not in paths:
                paths[path] = PathItem()

            # Get handler metadata
            meta = self.api._handler_meta.get(handler, {})

            # Create operation
            operation = self._create_operation(
                handler=handler,
                method=method,
                path=path,
                meta=meta,
                handler_id=handler_id,
            )

            # Collect tags from operation
            if operation.tags:
                collected_tags.update(operation.tags)

            # Add operation to path item
            method_lower = method.lower()
            setattr(paths[path], method_lower, operation)

        openapi.paths = paths

        # Add component schemas
        if self.schemas:
            openapi.components.schemas = self.schemas

        # Collect and merge tags
        openapi.tags = self._collect_tags(collected_tags)

        return openapi

    def _create_operation(
        self,
        handler: Any,
        method: str,
        path: str,
        meta: Dict[str, Any],
        handler_id: int,
    ) -> Operation:
        """Create OpenAPI Operation for a route handler.

        Args:
            handler: Handler function.
            method: HTTP method.
            path: Route path.
            meta: Handler metadata from BoltAPI.
            handler_id: Handler ID.

        Returns:
            Operation object.
        """
        # Prefer explicit metadata over docstring extraction
        summary = meta.get("openapi_summary")
        description = meta.get("openapi_description")

        # Fallback to docstring if not explicitly set
        if (summary is None or description is None) and self.config.use_handler_docstrings and handler.__doc__:
            doc = inspect.cleandoc(handler.__doc__)
            lines = doc.split("\n", 1)
            if summary is None:
                summary = lines[0]
            if description is None and len(lines) > 1:
                description = lines[1].strip()

        # Extract parameters
        parameters = self._extract_parameters(meta, path)

        # Extract request body
        request_body = self._extract_request_body(meta)

        # Extract responses (pass handler_id for auth error responses)
        responses = self._extract_responses(meta, handler_id)

        # Extract security requirements
        security = self._extract_security(handler_id)

        # Prefer explicit tags over auto-extracted tags
        tags = meta.get("openapi_tags")
        if tags is None:
            # Fallback to auto-extraction from handler module or class name
            tags = self._extract_tags(handler)

        operation = Operation(
            summary=summary,
            description=description,
            parameters=parameters or None,
            request_body=request_body,
            responses=responses,
            security=security,
            tags=tags,
            operation_id=f"{method.lower()}_{handler.__name__}",
        )

        return operation

    def _extract_parameters(
        self, meta: Dict[str, Any], path: str
    ) -> List[Parameter]:
        """Extract OpenAPI parameters from handler metadata.

        Args:
            meta: Handler metadata.
            path: Route path.

        Returns:
            List of Parameter objects.
        """
        parameters: List[Parameter] = []
        fields = meta.get("fields", [])

        for field in fields:
            # Access FieldDefinition attributes directly
            source = field.source
            name = field.name
            alias = field.alias or name
            annotation = field.annotation
            default = field.default

            # Skip request, body, form, file, and dependency parameters
            if source in ("request", "body", "form", "file", "dependency"):
                continue

            # Map source to OpenAPI parameter location
            param_in = {
                "path": "path",
                "query": "query",
                "header": "header",
                "cookie": "cookie",
            }.get(source)

            if not param_in:
                continue

            # Determine if required
            required = (
                param_in == "path"  # Path params always required
                or (default == inspect.Parameter.empty and not is_optional(annotation))
            )

            # Get schema for parameter type
            schema = self._type_to_schema(annotation)

            parameter = Parameter(
                name=alias,
                param_in=param_in,
                required=required,
                schema=schema,
                description=f"Parameter {alias}",
            )
            parameters.append(parameter)

        return parameters

    def _extract_request_body(self, meta: Dict[str, Any]) -> Optional[RequestBody]:
        """Extract OpenAPI RequestBody from handler metadata.

        Args:
            meta: Handler metadata.

        Returns:
            RequestBody object or None.
        """
        body_param = meta.get("body_struct_param")
        body_type = meta.get("body_struct_type")

        if not body_param or not body_type:
            # Check for form/file fields
            fields = meta.get("fields", [])
            form_fields = [f for f in fields if f.source in ("form", "file")]

            if form_fields:
                # Multipart form data
                properties = {}
                required = []
                for field in form_fields:
                    # Access FieldDefinition attributes directly
                    name = field.alias or field.name
                    annotation = field.annotation
                    default = field.default
                    source = field.source

                    if source == "file":
                        # File upload
                        schema = Schema(type="string", format="binary")
                    else:
                        schema = self._type_to_schema(annotation)

                    properties[name] = schema

                    if default == inspect.Parameter.empty and not is_optional(annotation):
                        required.append(name)

                schema = Schema(
                    type="object",
                    properties=properties,
                    required=required or None,
                )

                return RequestBody(
                    description="Form data",
                    content={
                        "multipart/form-data": OpenAPIMediaType(schema=schema),
                        "application/x-www-form-urlencoded": OpenAPIMediaType(schema=schema),
                    },
                    required=bool(required),
                )

            return None

        # JSON request body
        schema = self._type_to_schema(body_type, register_component=True)

        return RequestBody(
            description=f"Request body for {body_param}",
            content={
                "application/json": OpenAPIMediaType(schema=schema),
            },
            required=True,
        )

    def _extract_responses(
        self, meta: Dict[str, Any], handler_id: int
    ) -> Dict[str, OpenAPIResponse]:
        """Extract OpenAPI responses from handler metadata.

        Args:
            meta: Handler metadata.
            handler_id: Handler ID for checking authentication requirements.

        Returns:
            Dictionary mapping status codes to Response objects.
        """
        responses: Dict[str, OpenAPIResponse] = {}

        # Get response type
        response_type = meta.get("response_type")
        default_status = meta.get("default_status_code", 200)

        # Add successful response
        if response_type and response_type != inspect._empty:
            schema = self._type_to_schema(response_type, register_component=True)

            responses[str(default_status)] = OpenAPIResponse(
                description="Successful response",
                content={
                    "application/json": OpenAPIMediaType(schema=schema),
                },
            )
        else:
            # Default response
            responses["200"] = OpenAPIResponse(
                description="Successful response",
                content={
                    "application/json": OpenAPIMediaType(
                        schema=Schema(type="object")
                    ),
                },
            )

        # Add common error responses if enabled in config
        if self.config.include_error_responses:
            # Check if request body is present (for 422 validation errors)
            has_request_body = meta.get("body_struct_param") or any(
                f.source in ("body", "form", "file")
                for f in meta.get("fields", [])
            )

            if has_request_body:
                # 422 Unprocessable Entity - validation errors
                responses["422"] = OpenAPIResponse(
                    description="Validation Error - Request data failed validation",
                    content={
                        "application/json": OpenAPIMediaType(
                            schema=self._get_validation_error_schema()
                        ),
                    },
                )

        return responses

    def _get_validation_error_schema(self) -> Schema:
        """Get schema for 422 validation error responses.

        FastAPI-compatible format: {"detail": [array of validation errors]}

        Returns:
            Schema for validation errors matching FastAPI format.
        """
        return Schema(
            type="object",
            properties={
                "detail": Schema(
                    type="array",
                    description="List of validation errors",
                    items=Schema(
                        type="object",
                        properties={
                            "type": Schema(
                                type="string",
                                description="Error type",
                                example="validation_error",
                            ),
                            "loc": Schema(
                                type="array",
                                description="Location of the error (field path)",
                                items=Schema(
                                    one_of=[
                                        Schema(type="string"),
                                        Schema(type="integer"),
                                    ]
                                ),
                                example=["body", "is_active"],
                            ),
                            "msg": Schema(
                                type="string",
                                description="Error message",
                                example="Expected `bool`, got `int`",
                            ),
                            "input": Schema(
                                description="The input value that caused the error (optional)",
                            ),
                        },
                        required=["type", "loc", "msg"],
                    ),
                ),
            },
            required=["detail"],
        )

    def _extract_security(self, handler_id: int) -> Optional[List[SecurityReq]]:
        """Extract security requirements from handler middleware.

        Args:
            handler_id: Handler ID.

        Returns:
            List of SecurityRequirement objects or None.
        """
        middleware_meta = self.api._handler_middleware.get(handler_id, {})
        auth_config = middleware_meta.get("auth")

        if not auth_config:
            return None

        # Convert auth backends to security requirements
        security: List[SecurityReq] = []
        for auth_backend in auth_config:
            backend_name = auth_backend.__class__.__name__

            if "JWT" in backend_name:
                security.append({"BearerAuth": []})
            elif "APIKey" in backend_name:
                security.append({"ApiKeyAuth": []})
            elif "Session" in backend_name:
                security.append({"SessionAuth": []})

        return security or None

    def _extract_tags(self, handler: Any) -> Optional[List[str]]:
        """Extract tags for grouping operations.

        Args:
            handler: Handler function.

        Returns:
            List of tag names or None.
        """
        # Use module name as tag
        if hasattr(handler, "__module__"):
            module_parts = handler.__module__.split(".")
            if len(module_parts) > 0:
                # Use last part of module name (e.g., "users" from "myapp.api.users")
                tag = module_parts[-1]
                if tag == "api" and len(module_parts) > 1:
                    # If last part is "api", use the second-to-last part
                    # e.g., "users.api" -> "users"
                    tag = module_parts[-2]
                if tag != "api":  # Skip generic "api" tag
                    return [tag.capitalize()]

        return None

    def _collect_tags(self, collected_tag_names: set[str]) -> Optional[List[Tag]]:
        """Collect and merge tags from operations with config tags.

        Args:
            collected_tag_names: Set of tag names collected from operations.

        Returns:
            List of Tag objects or None if no tags.
        """
        if not collected_tag_names and not self.config.tags:
            return None

        # Start with existing tags from config
        tag_objects: Dict[str, Tag] = {}
        if self.config.tags:
            for tag in self.config.tags:
                tag_objects[tag.name] = tag

        # Add tags from operations (if not already defined in config)
        for tag_name in sorted(collected_tag_names):
            if tag_name not in tag_objects:
                # Create Tag object with just the name (no description)
                tag_objects[tag_name] = Tag(name=tag_name)

        # Return sorted list of Tag objects
        return list(tag_objects.values()) if tag_objects else None

    def _type_to_schema(
        self, type_annotation: Any, register_component: bool = False
    ) -> Schema | Reference:
        """Convert Python type annotation to OpenAPI Schema.

        Args:
            type_annotation: Python type annotation.
            register_component: Whether to register complex types as components.

        Returns:
            Schema or Reference object.
        """
        # Handle None/empty
        if type_annotation is None or type_annotation == inspect._empty:
            return Schema(type="object")

        # Handle msgspec type info objects (IntType, StrType, BoolType, etc.)
        type_name = type(type_annotation).__name__
        if hasattr(type_annotation, '__class__') and type_name.endswith('Type'):
            # Map msgspec type objects to OpenAPI schemas
            msgspec_type_map = {
                'IntType': Schema(type="integer"),
                'StrType': Schema(type="string"),
                'FloatType': Schema(type="number"),
                'BoolType': Schema(type="boolean"),
                'BytesType': Schema(type="string", format="binary"),
                'DateTimeType': Schema(type="string", format="date-time"),
                'DateType': Schema(type="string", format="date"),
                'TimeType': Schema(type="string", format="time"),
                'UUIDType': Schema(type="string", format="uuid"),
            }
            if type_name in msgspec_type_map:
                return msgspec_type_map[type_name]
            # For list/array types from msgspec
            if type_name == 'ListType':
                item_type = getattr(type_annotation, 'item_type', None)
                if item_type:
                    item_schema = self._type_to_schema(item_type, register_component=register_component)
                    return Schema(type="array", items=item_schema)
                return Schema(type="array", items=Schema(type="object"))
            # For dict types from msgspec
            if type_name == 'DictType':
                return Schema(type="object", additional_properties=True)

        # Unwrap Optional
        origin = get_origin(type_annotation)
        args = get_args(type_annotation)

        if origin is Annotated:
            # Unwrap Annotated[T, ...]
            type_annotation = args[0]
            origin = get_origin(type_annotation)
            args = get_args(type_annotation)

        # Handle Optional[T] -> T
        if is_optional(type_annotation):
            # Get the non-None type
            non_none_args = [arg for arg in args if arg is not type(None)]
            if non_none_args:
                type_annotation = non_none_args[0]
                origin = get_origin(type_annotation)
                args = get_args(type_annotation)

        # Handle msgspec.Struct
        if is_msgspec_struct(type_annotation):
            if register_component:
                return self._struct_to_component_schema(type_annotation)
            else:
                return self._struct_to_schema(type_annotation)

        # Handle list/List
        if origin in (list, List):
            item_type = args[0] if args else Any
            item_schema = self._type_to_schema(item_type, register_component=register_component)
            return Schema(type="array", items=item_schema)

        # Handle dict/Dict
        if origin in (dict, Dict):
            return Schema(type="object", additional_properties=True)

        # Handle primitive types
        type_map = {
            str: Schema(type="string"),
            int: Schema(type="integer"),
            float: Schema(type="number"),
            bool: Schema(type="boolean"),
            bytes: Schema(type="string", format="binary"),
        }

        for py_type, schema in type_map.items():
            if type_annotation == py_type:
                return schema

        # Default to generic object
        return Schema(type="object")

    def _struct_to_schema(self, struct_type: type) -> Schema:
        """Convert msgspec.Struct to inline OpenAPI Schema.

        Args:
            struct_type: msgspec.Struct type.

        Returns:
            Schema object.
        """
        struct_info = msgspec.inspect.type_info(struct_type)
        properties = {}
        required = []

        for field in struct_info.fields:
            field_name = field.encode_name
            field_type = field.type

            # Get schema for field type
            field_schema = self._type_to_schema(field_type, register_component=False)
            properties[field_name] = field_schema

            # Check if required
            if field.required and field.default == msgspec.NODEFAULT:
                required.append(field_name)

        return Schema(
            type="object",
            properties=properties,
            required=required or None,
        )

    def _struct_to_component_schema(self, struct_type: type) -> Reference:
        """Convert msgspec.Struct to component schema and return reference.

        Args:
            struct_type: msgspec.Struct type.

        Returns:
            Reference to component schema.
        """
        schema_name = struct_type.__name__

        # Check if already registered
        if schema_name not in self.schemas:
            # Register the schema
            self.schemas[schema_name] = self._struct_to_schema(struct_type)

        return Reference(ref=f"#/components/schemas/{schema_name}")
