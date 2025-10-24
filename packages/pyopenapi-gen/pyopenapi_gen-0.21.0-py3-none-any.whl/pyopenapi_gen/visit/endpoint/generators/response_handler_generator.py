"""
Helper class for generating response handling logic for an endpoint method.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, TypedDict

from pyopenapi_gen.core.http_status_codes import get_exception_class_name
from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.helpers.endpoint_utils import (
    _get_primary_response,
)
from pyopenapi_gen.types.services.type_service import UnifiedTypeService
from pyopenapi_gen.types.strategies.response_strategy import ResponseStrategy

if TYPE_CHECKING:
    from pyopenapi_gen import IROperation, IRResponse, IRSchema
    from pyopenapi_gen.context.render_context import RenderContext
else:
    # For runtime, we need to import for TypedDict
    from pyopenapi_gen import IRResponse, IRSchema

logger = logging.getLogger(__name__)


class StatusCase(TypedDict):
    """Type definition for status code case data."""

    status_code: int
    type: str  # 'primary_success', 'success', or 'error'
    return_type: str
    response_ir: IRResponse


class DefaultCase(TypedDict):
    """Type definition for default case data."""

    response_ir: IRResponse
    return_type: str


class EndpointResponseHandlerGenerator:
    """Generates the response handling logic for an endpoint method."""

    def __init__(self, schemas: dict[str, Any] | None = None) -> None:
        self.schemas: dict[str, Any] = schemas or {}

    def _is_type_alias_to_array(self, type_name: str) -> bool:
        """
        Check if a type name corresponds to a type alias that resolves to a List/array type.

        This helps distinguish between:
        - Type aliases: AgentHistoryListResponse = List[AgentHistory] (should use array deserialization)
        - Dataclasses: class AgentHistoryListResponse(BaseSchema): ... (should use .from_dict())

        Args:
            type_name: The Python type name (e.g., "AgentHistoryListResponse")

        Returns:
            True if this is a type alias that resolves to List[SomeType]
        """
        # Extract base type name without generics
        base_type = type_name
        if "[" in base_type:
            base_type = base_type[: base_type.find("[")]

        # Look up the schema for this type name
        if base_type in self.schemas:
            schema = self.schemas[base_type]
            # Check if it's a type alias using ModelVisitor's logic:
            # - Has a name
            # - No properties (not an object with fields)
            # - Not an enum
            # - Type is not "object" (which would be a dataclass)
            # - Type is "array" (indicating it's an array type alias)
            is_type_alias = bool(
                getattr(schema, "name", None)
                and not getattr(schema, "properties", None)
                and not getattr(schema, "enum", None)
                and getattr(schema, "type", None) != "object"
            )
            is_array_type = getattr(schema, "type", None) == "array"
            return is_type_alias and is_array_type

        return False

    def _is_type_alias_to_primitive(self, type_name: str) -> bool:
        """
        Check if a type name corresponds to a type alias that resolves to a primitive type.

        This helps distinguish between:
        - Type aliases: StringAlias = str (should use cast())
        - Dataclasses: class MyModel(BaseSchema): ... (should use .from_dict())

        Args:
            type_name: The Python type name (e.g., "StringAlias")

        Returns:
            True if this is a type alias that resolves to a primitive type (str, int, float, bool)
        """
        # Extract base type name without generics
        base_type = type_name
        if "[" in base_type:
            base_type = base_type[: base_type.find("[")]

        # Look up the schema for this type name
        if base_type in self.schemas:
            schema = self.schemas[base_type]
            # Check if it's a type alias using ModelVisitor's logic:
            # - Has a name
            # - No properties (not an object with fields)
            # - Not an enum
            # - Type is not "object" (which would be a dataclass)
            # - Type is a primitive (string, integer, number, boolean)
            is_type_alias = bool(
                getattr(schema, "name", None)
                and not getattr(schema, "properties", None)
                and not getattr(schema, "enum", None)
                and getattr(schema, "type", None) != "object"
            )
            is_primitive_type = getattr(schema, "type", None) in ("string", "integer", "number", "boolean")
            return is_type_alias and is_primitive_type

        return False

    def _should_use_base_schema(self, type_name: str) -> bool:
        """
        Determine if a type should use BaseSchema deserialization.

        Args:
            type_name: The Python type name (e.g., "User", "List[User]", "User | None")

        Returns:
            True if the type should use BaseSchema .from_dict() deserialization
        """
        # Extract the base type name from complex types
        base_type = type_name

        # Handle List[Type], Type | None, etc.
        if "[" in base_type and "]" in base_type:
            # Extract the inner type from List[Type], Type | None, etc.
            start_bracket = base_type.find("[")
            end_bracket = base_type.rfind("]")
            inner_type = base_type[start_bracket + 1 : end_bracket]

            # For Union types like User | None -> Union[User, None], take the first type
            if ", " in inner_type:
                inner_type = inner_type.split(", ")[0]

            base_type = inner_type.strip()

        # Skip primitive types and built-ins (both uppercase and lowercase)
        if base_type in {
            "str",
            "int",
            "float",
            "bool",
            "bytes",
            "None",
            "Any",
            "Dict",
            "List",
            "dict",
            "list",
            "tuple",
        }:
            return False

        # Skip typing constructs
        # Note: Modern Python 3.10+ uses | None instead of Optional[X]
        if base_type.startswith(("dict[", "List[", "Union[", "Tuple[", "dict[", "list[", "tuple[")):
            return False

        # Check if this is a type alias (array or non-array) - these should NOT use BaseSchema
        if self._is_type_alias_to_array(type_name) or self._is_type_alias_to_primitive(type_name):
            return False

        # All custom model types now inherit from BaseSchema for automatic field mapping
        # Check if it's a model type (contains a dot indicating it's from models package)
        # or if it's a simple class name that's likely a generated model (starts with uppercase)
        return "." in base_type or (
            base_type[0].isupper() and base_type not in {"Dict", "List", "Union", "Tuple", "dict", "list", "tuple"}
        )

    def _get_base_schema_deserialization_code(self, return_type: str, data_expr: str) -> str:
        """
        Generate BaseSchema deserialization code for a given type.

        Args:
            return_type: The return type (e.g., "User", "List[User]", "list[User]")
            data_expr: The expression containing the raw data to deserialize

        Returns:
            Code string for deserializing the data using BaseSchema .from_dict()
        """
        if return_type.startswith("List[") or return_type.startswith("list["):
            # Handle List[Model] or list[Model] types
            if return_type.startswith("List["):
                item_type = return_type[5:-1]  # Remove 'List[' and ']'
            else:  # starts with "list["
                item_type = return_type[5:-1]  # Remove 'list[' and ']'
            return f"[{item_type}.from_dict(item) for item in {data_expr}]"
        elif return_type.startswith("Optional["):
            # SANITY CHECK: Unified type system should never produce Optional[X]
            logger.error(
                f"❌ ARCHITECTURE VIOLATION: Received legacy Optional[X] type in response handler: {return_type}. "
                f"Unified type system must generate X | None directly."
            )
            # Defensive conversion (but this indicates a serious bug upstream)
            inner_type = return_type[9:-1]  # Remove 'Optional[' and ']'
            logger.warning(f"⚠️ Converting to modern syntax internally for: {inner_type} | None")

            # Check if inner type is also a list
            if inner_type.startswith("List[") or inner_type.startswith("list["):
                list_code = self._get_base_schema_deserialization_code(inner_type, data_expr)
                return f"{list_code} if {data_expr} is not None else None"
            else:
                return f"{inner_type}.from_dict({data_expr}) if {data_expr} is not None else None"
        elif " | None" in return_type or return_type.endswith("| None"):
            # Handle Model | None types (modern Python 3.10+ syntax)
            # Extract base type from "X | None" pattern
            if " | None" in return_type:
                inner_type = return_type.replace(" | None", "").strip()
            else:
                inner_type = return_type.replace("| None", "").strip()

            # Check if inner type is also a list
            if inner_type.startswith("List[") or inner_type.startswith("list["):
                list_code = self._get_base_schema_deserialization_code(inner_type, data_expr)
                return f"{list_code} if {data_expr} is not None else None"
            else:
                return f"{inner_type}.from_dict({data_expr}) if {data_expr} is not None else None"
        else:
            # Handle simple Model types only - this should not be called for list types
            if "[" in return_type and "]" in return_type:
                # This is a complex type that we missed - should not happen
                raise ValueError(f"Unsupported complex type for BaseSchema deserialization: {return_type}")

            # Safety check: catch the specific issue we're debugging
            if return_type.startswith("list[") or return_type.startswith("List["):
                raise ValueError(
                    f"CRITICAL BUG: List type {return_type} reached simple type handler! This should never happen."
                )

            return f"{return_type}.from_dict({data_expr})"

    def _get_extraction_code(
        self,
        return_type: str,
        context: RenderContext,
        op: IROperation,
        response_ir: IRResponse | None = None,
    ) -> str:
        """Determines the code snippet to extract/transform the response body."""
        # Handle None, StreamingResponse, Iterator, etc.
        if return_type is None or return_type == "None":
            return "None"  # This will be directly used in the return statement

        # Handle streaming responses
        if return_type.startswith("AsyncIterator["):
            # Check if it's a bytes stream or other type of stream
            if return_type == "AsyncIterator[bytes]":
                context.add_import(f"{context.core_package_name}.streaming_helpers", "iter_bytes")
                return "iter_bytes(response)"
            elif "dict[str, Any]" in return_type or "dict" in return_type.lower():
                # For event streams that return Dict objects
                context.add_import(f"{context.core_package_name}.streaming_helpers", "iter_sse_events_text")
                return "sse_json_stream_marker"  # Special marker handled by _write_parsed_return
            else:
                # Model streaming - likely an SSE model stream
                # Extract the model type and check if content type is text/event-stream
                model_type = return_type[13:-1]  # Remove 'AsyncIterator[' and ']'
                if response_ir and "text/event-stream" in response_ir.content:
                    context.add_import(f"{context.core_package_name}.streaming_helpers", "iter_sse_events_text")
                    return "sse_json_stream_marker"  # Special marker for SSE streaming

                # Default to bytes streaming for other types
                context.add_import(f"{context.core_package_name}.streaming_helpers", "iter_bytes")
                return "iter_bytes(response)"

        # Special case for "data: Any" unwrapping when the actual schema has no fields/properties
        if return_type in {"dict[str, Any]", "dict[str, object]", "object", "Any"}:
            context.add_import("typing", "Dict")
            context.add_import("typing", "Any")

        if return_type == "str":
            return "response.text"
        elif return_type == "bytes":
            return "response.content"
        elif return_type == "Any":
            context.add_import("typing", "Any")
            return "response.json()  # Type is Any"
        elif return_type == "None":
            return "None"  # This will be handled by generate_response_handling directly
        else:  # Includes schema-defined models, List[], dict[], Optional[]
            context.add_typing_imports_for_type(return_type)  # Ensure model itself is imported

            # Check if we should use BaseSchema deserialization instead of cast()
            use_base_schema = self._should_use_base_schema(return_type)

            if not use_base_schema:
                # Fallback to cast() for non-BaseSchema types
                context.add_import("typing", "cast")

            # Direct deserialization using schemas as-is (no unwrapping)
            if use_base_schema:
                deserialization_code = self._get_base_schema_deserialization_code(return_type, "response.json()")
                return deserialization_code
            else:
                return f"cast({return_type}, response.json())"

    def generate_response_handling(
        self,
        writer: CodeWriter,
        op: IROperation,
        context: RenderContext,
        strategy: ResponseStrategy,
    ) -> None:
        """Writes the response parsing and return logic to the CodeWriter, using the unified response strategy."""
        writer.write_line("# Check response status code and handle accordingly")

        # Generate the match statement for status codes
        writer.write_line("match response.status_code:")
        writer.indent()

        # Handle the primary success response first
        primary_success_ir = _get_primary_response(op)
        processed_primary_success = False
        if (
            primary_success_ir
            and primary_success_ir.status_code.isdigit()
            and primary_success_ir.status_code.startswith("2")
        ):
            status_code_val = int(primary_success_ir.status_code)
            writer.write_line(f"case {status_code_val}:")
            writer.indent()

            if strategy.return_type == "None":
                writer.write_line("return None")
            else:
                self._write_strategy_based_return(writer, strategy, context)

            writer.dedent()
            processed_primary_success = True

        # Handle other responses (exclude primary only if it was actually processed)
        other_responses = [r for r in op.responses if not (processed_primary_success and r == primary_success_ir)]
        for resp_ir in other_responses:
            if resp_ir.status_code.isdigit():
                status_code_val = int(resp_ir.status_code)
                writer.write_line(f"case {status_code_val}:")
                writer.indent()

                if resp_ir.status_code.startswith("2"):
                    # Other 2xx success responses - resolve each response individually
                    if not resp_ir.content:
                        writer.write_line("return None")
                    else:
                        # Resolve the specific return type for this response
                        resp_schema = self._get_response_schema(resp_ir)
                        if resp_schema:
                            type_service = UnifiedTypeService(self.schemas)
                            response_type = type_service.resolve_schema_type(resp_schema, context)
                            if self._should_use_base_schema(response_type):
                                deserialization_code = self._get_base_schema_deserialization_code(
                                    response_type, "response.json()"
                                )
                                writer.write_line(f"return {deserialization_code}")
                                context.add_typing_imports_for_type(response_type)
                            else:
                                context.add_import("typing", "cast")
                                writer.write_line(f"return cast({response_type}, response.json())")
                        else:
                            writer.write_line("return None")
                else:
                    # Error responses - use human-readable exception names
                    error_class_name = get_exception_class_name(status_code_val)
                    context.add_import(f"{context.core_package_name}", error_class_name)
                    writer.write_line(f"raise {error_class_name}(response=response)")

                writer.dedent()

        # Handle default case
        default_response = next((r for r in op.responses if r.status_code == "default"), None)
        if default_response:
            writer.write_line("case _:  # Default response")
            writer.indent()
            if default_response.content and strategy.return_type != "None":
                self._write_strategy_based_return(writer, strategy, context)
            else:
                context.add_import(f"{context.core_package_name}.exceptions", "HTTPError")
                writer.write_line(
                    'raise HTTPError(response=response, message="Default error", status_code=response.status_code)'
                )
            writer.dedent()
        else:
            # Final catch-all
            writer.write_line("case _:")
            writer.indent()
            context.add_import(f"{context.core_package_name}.exceptions", "HTTPError")
            writer.write_line(
                'raise HTTPError(response=response, message="Unhandled status code", status_code=response.status_code)'
            )
            writer.dedent()

        writer.dedent()  # End of match statement

        # All code paths should be covered by the match statement above
        writer.write_line("# All paths above should return or raise - this should never execute")
        context.add_import("typing", "NoReturn")
        writer.write_line("raise RuntimeError('Unexpected code path')  # pragma: no cover")
        writer.write_line("")  # Add a blank line for readability

    def _write_strategy_based_return(
        self,
        writer: CodeWriter,
        strategy: ResponseStrategy,
        context: RenderContext,
    ) -> None:
        """Write the return statement based on the response strategy.

        This method implements the strategy pattern for response handling,
        ensuring consistent behavior between signature and implementation.
        """
        if strategy.is_streaming:
            # Handle streaming responses
            if "AsyncIterator[bytes]" in strategy.return_type:
                context.add_import(f"{context.core_package_name}.streaming_helpers", "iter_bytes")
                writer.write_line("async for chunk in iter_bytes(response):")
                writer.indent()
                writer.write_line("yield chunk")
                writer.dedent()
                writer.write_line("return  # Explicit return for async generator")
            else:
                # Handle other streaming types
                context.add_plain_import("json")
                context.add_import(f"{context.core_package_name}.streaming_helpers", "iter_sse_events_text")
                writer.write_line("async for chunk in iter_sse_events_text(response):")
                writer.indent()
                writer.write_line("yield json.loads(chunk)")
                writer.dedent()
                writer.write_line("return  # Explicit return for async generator")
            return

        # Handle responses using the schema as-is from the OpenAPI spec (no unwrapping)
        if strategy.return_type.startswith("Union["):
            # Special handling for Union types with try/except fallback
            self._write_union_response_handling(writer, context, strategy.return_type, "response.json()")
        elif self._should_use_base_schema(strategy.return_type):
            deserialization_code = self._get_base_schema_deserialization_code(strategy.return_type, "response.json()")
            writer.write_line(f"return {deserialization_code}")
        else:
            context.add_import("typing", "cast")
            writer.write_line(f"return cast({strategy.return_type}, response.json())")

    def _get_response_schema(self, response_ir: IRResponse) -> IRSchema | None:
        """Extract the schema from a response IR."""
        if not response_ir.content:
            return None

        # Prefer application/json, then first available content type
        content_types = list(response_ir.content.keys())
        preferred_content_type = next((ct for ct in content_types if ct == "application/json"), None)
        if not preferred_content_type:
            preferred_content_type = content_types[0] if content_types else None

        if preferred_content_type:
            return response_ir.content.get(preferred_content_type)

        return None

    def _write_union_response_handling(
        self, writer: CodeWriter, context: RenderContext, return_type: str, data_expr: str
    ) -> None:
        """Write try/except logic for Union types."""
        # Parse Union[TypeA, TypeB] to extract the types
        if not return_type.startswith("Union[") or not return_type.endswith("]"):
            raise ValueError(f"Invalid Union type format: {return_type}")

        union_content = return_type[6:-1]  # Remove 'Union[' and ']'
        types = [t.strip() for t in union_content.split(",")]

        if len(types) < 2:
            raise ValueError(f"Union type must have at least 2 types: {return_type}")

        # Add Union import
        context.add_import("typing", "Union")

        # Generate try/except blocks for each type
        first_type = types[0]
        remaining_types = types[1:]

        # Try the first type
        writer.write_line("try:")
        writer.indent()
        if self._should_use_base_schema(first_type):
            context.add_typing_imports_for_type(first_type)
            deserialization_code = self._get_base_schema_deserialization_code(first_type, data_expr)
            writer.write_line(f"return {deserialization_code}")
        else:
            context.add_import("typing", "cast")
            writer.write_line(f"return cast({first_type}, {data_expr})")
        writer.dedent()

        # Add except blocks for remaining types
        for i, type_name in enumerate(remaining_types):
            is_last = i == len(remaining_types) - 1
            if is_last:
                writer.write_line("except Exception:  # Attempt to parse as the final type")
            else:
                writer.write_line("except Exception:  # Attempt to parse as the next type")
            writer.indent()
            if self._should_use_base_schema(type_name):
                context.add_typing_imports_for_type(type_name)
                deserialization_code = self._get_base_schema_deserialization_code(type_name, data_expr)
                if is_last:
                    writer.write_line(f"return {deserialization_code}")
                else:
                    writer.write_line("try:")
                    writer.indent()
                    writer.write_line(f"return {deserialization_code}")
                    writer.dedent()
            else:
                context.add_import("typing", "cast")
                writer.write_line(f"return cast({type_name}, {data_expr})")
            writer.dedent()
