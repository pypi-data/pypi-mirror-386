"""Utilities for pyopenapi_gen.

This module contains utility classes and functions used across the code generation process.
"""

import dataclasses
import keyword
import logging
import re
from datetime import datetime
from typing import Any, Set, Type, TypeVar, cast

logger = logging.getLogger(__name__)

T = TypeVar("T")


class NameSanitizer:
    """Helper to sanitize spec names and tags into valid Python identifiers and filenames."""

    # Python built-ins and common problematic names that should be avoided in module names
    RESERVED_NAMES = {
        # Built-in types
        "type",
        "int",
        "str",
        "float",
        "bool",
        "list",
        "dict",
        "set",
        "tuple",
        "bytes",
        "object",
        "complex",
        "frozenset",
        "bytearray",
        "memoryview",
        "range",
        # Built-in functions
        "abs",
        "all",
        "any",
        "bin",
        "callable",
        "chr",
        "classmethod",
        "compile",
        "delattr",
        "dir",
        "divmod",
        "enumerate",
        "eval",
        "exec",
        "filter",
        "format",
        "getattr",
        "globals",
        "hasattr",
        "hash",
        "help",
        "hex",
        "id",
        "input",
        "isinstance",
        "issubclass",
        "iter",
        "len",
        "locals",
        "map",
        "max",
        "min",
        "next",
        "oct",
        "open",
        "ord",
        "pow",
        "print",
        "property",
        "repr",
        "reversed",
        "round",
        "setattr",
        "slice",
        "sorted",
        "staticmethod",
        "sum",
        "super",
        "vars",
        "zip",
        # Common standard library modules
        "os",
        "sys",
        "json",
        "time",
        "datetime",
        "math",
        "random",
        "string",
        "collections",
        "itertools",
        "functools",
        "typing",
        "pathlib",
        "logging",
        "urllib",
        "http",
        "email",
        "uuid",
        "hashlib",
        "base64",
        "copy",
        "re",
        # Other problematic names
        "data",
        "model",
        "models",
        "client",
        "api",
        "config",
        "utils",
        "helpers",
    }

    @staticmethod
    def sanitize_module_name(name: str) -> str:
        """Convert a raw name into a valid Python module name in snake_case, splitting camel case and PascalCase."""
        # # <<< Add Check for problematic input >>>
        # if '[' in name or ']' in name or ',' in name:
        #     logger.error(f"sanitize_module_name received potentially invalid input: '{name}'")
        #     # Optionally, return a default/error value or raise exception
        #     # For now, just log and continue
        # # <<< End Check >>>

        # Split on non-alphanumeric and camel case boundaries
        words = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+", name)
        if not words:
            # fallback: split on non-alphanumerics
            words = re.split(r"\W+", name)
        module = "_".join(word.lower() for word in words if word)
        # If it starts with a digit, prefix with underscore
        if module and module[0].isdigit():
            module = "_" + module
        # Avoid Python keywords and reserved names
        if keyword.iskeyword(module) or module in NameSanitizer.RESERVED_NAMES:
            module += "_"
        return module

    @staticmethod
    def sanitize_class_name(name: str) -> str:
        """Convert a raw name into a valid Python class name in PascalCase."""
        # Split on non-alphanumeric and camel case boundaries
        words = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+", name)
        if not words:  # Fallback if findall is empty (e.g. if name was all symbols)
            # Basic split on non-alphanumeric as a last resort if findall yields nothing
            words = [part for part in re.split(r"[^a-zA-Z0-9]+", name) if part]

        # Capitalize each word and join
        cls_name = "".join(word.capitalize() for word in words if word)

        if not cls_name:  # If name was e.g. "-" or "_"
            cls_name = "UnnamedClass"  # Or some other default

        # If it starts with a digit, prefix with underscore
        if cls_name[0].isdigit():  # Check after ensuring cls_name is not empty
            cls_name = "_" + cls_name
        # Avoid Python keywords and reserved names (case-insensitive)
        if keyword.iskeyword(cls_name.lower()) or cls_name.lower() in NameSanitizer.RESERVED_NAMES:
            cls_name += "_"
        return cls_name

    @staticmethod
    def sanitize_tag_class_name(tag: str) -> str:
        """Sanitize a tag for use as a PascalCase client class name (e.g., DataSourcesClient)."""
        words = re.split(r"[\W_]+", tag)
        return "".join(word.capitalize() for word in words if word) + "Client"

    @staticmethod
    def sanitize_tag_attr_name(tag: str) -> str:
        """Sanitize a tag for use as a snake_case attribute name (e.g., data_sources)."""
        attr = re.sub(r"[\W]+", "_", tag).lower()
        return attr.strip("_")

    @staticmethod
    def normalize_tag_key(tag: str) -> str:
        """Normalize a tag for case-insensitive uniqueness (e.g., datasources)."""
        return re.sub(r"[\W_]+", "", tag).lower()

    @staticmethod
    def sanitize_filename(name: str, suffix: str = ".py") -> str:
        """Generate a valid Python filename from raw name in snake_case."""
        module = NameSanitizer.sanitize_module_name(name)
        return module + suffix

    @staticmethod
    def sanitize_method_name(name: str) -> str:
        """Convert a raw name into a valid Python method name in snake_case, splitting camelCase and PascalCase."""
        # Remove curly braces
        name = re.sub(r"[{}]", "", name)
        # Split camelCase and PascalCase to snake_case
        name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
        name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
        # Replace non-alphanumerics with underscores
        name = re.sub(r"[^0-9a-zA-Z_]", "_", name)
        # Lowercase and collapse multiple underscores
        name = re.sub(r"_+", "_", name).strip("_").lower()
        # If it starts with a digit, prefix with underscore
        if name and name[0].isdigit():
            name = "_" + name
        # Avoid Python keywords and reserved names
        if keyword.iskeyword(name) or name in NameSanitizer.RESERVED_NAMES:
            name += "_"
        return name

    @staticmethod
    def is_valid_python_identifier(name: str) -> bool:
        """Check if a string is a valid Python identifier."""
        if not isinstance(name, str) or not name:
            return False
        # Check if it's a keyword
        if keyword.iskeyword(name):
            return False
        # Check pattern: starts with letter/underscore, then letter/digit/underscore
        return re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name) is not None


class ParamSubstitutor:
    """Helper for rendering path templates with path parameters."""

    @staticmethod
    def render_path(template: str, values: dict[str, Any]) -> str:
        """Replace placeholders in a URL path template using provided values."""
        rendered = template
        for key, val in values.items():
            rendered = rendered.replace(f"{{{key}}}", str(val))
        return rendered


class KwargsBuilder:
    """Builder for assembling HTTP request keyword arguments."""

    def __init__(self) -> None:
        self._kwargs: dict[str, Any] = {}

    def with_params(self, **params: Any) -> "KwargsBuilder":
        """Add query parameters, skipping None values."""
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            self._kwargs["params"] = filtered
        return self

    def with_json(self, body: Any) -> "KwargsBuilder":
        """Add a JSON body to the request."""
        self._kwargs["json"] = body
        return self

    def build(self) -> dict[str, Any]:
        """Return the assembled kwargs dictionary."""
        return self._kwargs


class Formatter:
    """Helper to format code using Black, falling back to unformatted content if Black is unavailable or errors."""

    def __init__(self) -> None:
        from typing import Any, Callable

        self._file_mode: Any | None = None
        self._format_str: Callable[..., str] | None = None
        try:
            from black import FileMode, format_str

            # Suppress blib2to3 debug logging that floods output during formatting
            blib2to3_logger = logging.getLogger("blib2to3")
            blib2to3_logger.setLevel(logging.WARNING)

            # Also suppress the driver logger specifically
            driver_logger = logging.getLogger("blib2to3.pgen2.driver")
            driver_logger.setLevel(logging.WARNING)

            # Initialize Black formatter
            self._file_mode = FileMode()
            self._format_str = format_str
        except ImportError:
            self._file_mode = None
            self._format_str = None

    def format(self, code: str) -> str:
        """Format the given code string with Black if possible."""
        if self._format_str is not None and self._file_mode is not None:
            try:
                formatted: str = self._format_str(code, mode=self._file_mode)
                return formatted
            except Exception:
                # On any Black formatting error, return original code
                return code
        return code


# --- Casting Helper ---


def safe_cast(expected_type: Type[T], data: Any) -> T:
    """
    Performs a cast for the type checker using object cast.
    (Validation temporarily removed).
    """
    # No validation for now
    # Cast to object first, then to expected_type
    return cast(expected_type, cast(object, data))  # type: ignore[valid-type]


class DataclassSerializer:
    """Utility for converting dataclass instances to dictionaries for API serialization.

    This enables automatic conversion of dataclass request bodies to JSON-compatible
    dictionaries in generated client code, providing a better developer experience.
    """

    @staticmethod
    def serialize(obj: Any) -> Any:
        """Convert dataclass instances to dictionaries recursively.

        Args:
            obj: The object to serialize. Can be a dataclass, list, dict, or primitive.

        Returns:
            The serialized object with dataclasses converted to dictionaries.

        Handles:
        - BaseSchema instances: Uses to_dict() method with field name mapping (e.g., snake_case -> camelCase)
        - Regular dataclass instances: Converted to dictionaries using field names
        - Lists: Recursively serialize each item
        - Dictionaries: Recursively serialize values
        - datetime: Convert to ISO format string
        - Enums: Convert to their value
        - Primitives: Return unchanged
        - None values: Excluded from output
        """
        # Track visited objects to handle circular references
        return DataclassSerializer._serialize_with_tracking(obj, set())

    @staticmethod
    def _serialize_with_tracking(obj: Any, visited: Set[int]) -> Any:
        """Internal serialization method with circular reference tracking."""
        from enum import Enum

        # Handle None values by excluding them
        if obj is None:
            return None

        # Handle circular references
        obj_id = id(obj)
        if obj_id in visited:
            # For circular references, return a simple representation
            if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
                return f"<Circular reference to {obj.__class__.__name__}>"
            return obj

        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()

        # Handle enum instances
        if isinstance(obj, Enum) and not isinstance(obj, type):
            return obj.value

        # Handle BaseSchema instances (respects field name mappings)
        # Check for BaseSchema by looking for both to_dict and _get_field_mappings methods
        if hasattr(obj, "to_dict") and hasattr(obj, "_get_field_mappings") and callable(obj.to_dict):
            visited.add(obj_id)
            try:
                # Use BaseSchema's to_dict() which handles field name mapping
                result_dict = obj.to_dict(exclude_none=True)
                # Recursively serialize nested objects in the result
                serialized_result = {}
                for key, value in result_dict.items():
                    serialized_value = DataclassSerializer._serialize_with_tracking(value, visited)
                    if serialized_value is not None:
                        serialized_result[key] = serialized_value
                return serialized_result
            finally:
                visited.discard(obj_id)

        # Handle regular dataclass instances (no field mapping)
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            visited.add(obj_id)
            try:
                result = {}
                for field in dataclasses.fields(obj):
                    value = getattr(obj, field.name)
                    # Skip None values to keep JSON clean
                    if value is not None:
                        serialized_value = DataclassSerializer._serialize_with_tracking(value, visited)
                        if serialized_value is not None:
                            result[field.name] = serialized_value
                return result
            finally:
                visited.discard(obj_id)

        # Handle lists and tuples
        if isinstance(obj, (list, tuple)):
            return [DataclassSerializer._serialize_with_tracking(item, visited) for item in obj]

        # Handle dictionaries
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                serialized_value = DataclassSerializer._serialize_with_tracking(value, visited)
                if serialized_value is not None:
                    result[key] = serialized_value
            return result

        # Handle primitive types and unknown objects
        if isinstance(obj, (str, int, float, bool)):
            return obj

        # For unknown types, try to convert to string as fallback
        try:
            # If the object has a __dict__, try to serialize it like a dataclass
            if hasattr(obj, "__dict__"):
                visited.add(obj_id)
                try:
                    result = {}
                    for key, value in obj.__dict__.items():
                        if not key.startswith("_"):  # Skip private attributes
                            serialized_value = DataclassSerializer._serialize_with_tracking(value, visited)
                            if serialized_value is not None:
                                result[key] = serialized_value
                    return result
                finally:
                    visited.discard(obj_id)
            else:
                # Fallback to string representation
                return str(obj)
        except Exception:
            # Ultimate fallback
            return str(obj)
