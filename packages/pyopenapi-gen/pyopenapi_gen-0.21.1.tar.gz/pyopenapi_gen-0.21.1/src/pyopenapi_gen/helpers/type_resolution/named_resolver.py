"""Resolves IRSchema to Python named types (classes, enums)."""

import logging
import os

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.utils import NameSanitizer

logger = logging.getLogger(__name__)


class NamedTypeResolver:
    """Resolves IRSchema instances that refer to named models/enums."""

    def __init__(self, context: RenderContext, all_schemas: dict[str, IRSchema]):
        self.context = context
        self.all_schemas = all_schemas

    def _is_self_reference(self, target_module_name: str, target_class_name: str) -> bool:
        """Check if the target class is the same as the one currently being generated."""
        if not self.context.current_file:
            return False

        # Extract current module name from the file path
        current_file_name = self.context.current_file
        current_module_name = os.path.splitext(os.path.basename(current_file_name))[0]

        # For self-reference detection, we need to check if:
        # 1. The target module name matches the current module name
        # 2. The target class name is likely the class being defined in this file
        #
        # The target_class_name should match the class being generated in the current file
        # For example, if we're in tree_node.py generating TreeNode class, and we're trying
        # to reference TreeNode, then this is a self-reference
        return current_module_name == target_module_name and self._class_being_generated_matches(target_class_name)

    def _class_being_generated_matches(self, target_class_name: str) -> bool:
        """Check if the target class name matches what's being generated in the current file."""
        # This is a simple heuristic: if the file is tree_node.py, we expect TreeNode class
        # More sophisticated logic could be added by tracking what class is currently being generated
        if not self.context.current_file:
            return False

        current_file_name = self.context.current_file
        current_module_name = os.path.splitext(os.path.basename(current_file_name))[0]

        # Convert module name to expected class name (snake_case to PascalCase)
        expected_class_name = self._module_name_to_class_name(current_module_name)

        return target_class_name == expected_class_name

    def _module_name_to_class_name(self, module_name: str) -> str:
        """Convert module name (snake_case) to class name (PascalCase)."""
        # Convert snake_case to PascalCase
        # tree_node -> TreeNode
        # message -> Message
        parts = module_name.split("_")
        return "".join(word.capitalize() for word in parts)

    def resolve(self, schema: IRSchema, resolve_alias_target: bool = False) -> str | None:
        """
        Resolves an IRSchema that refers to a named model/enum, or an inline named enum.

        Args:
            schema: The IRSchema to resolve.
            resolve_alias_target: If true, the resolver should return the Python type string for the
                                 *target* of an alias. If false, it should return the alias name itself.

        Returns:
            A Python type string for the resolved schema, e.g., "MyModel", "MyModel | None".
        """

        if schema.name and schema.name in self.all_schemas:
            # This schema is a REFERENCE to a globally defined schema (e.g., in components/schemas)
            ref_schema = self.all_schemas[schema.name]  # Get the actual definition
            if ref_schema.name is None:
                raise RuntimeError(f"Schema '{schema.name}' resolved to ref_schema with None name.")

            # NEW: Use generation_name and final_module_stem from the referenced schema
            if ref_schema.generation_name is None:
                raise RuntimeError(f"Referenced schema '{ref_schema.name}' must have generation_name set.")
            if ref_schema.final_module_stem is None:
                raise RuntimeError(f"Referenced schema '{ref_schema.name}' must have final_module_stem set.")

            class_name_for_ref = ref_schema.generation_name
            module_name_for_ref = ref_schema.final_module_stem

            model_module_path_for_ref = (
                f"{self.context.get_current_package_name_for_generated_code()}.models.{module_name_for_ref}"
            )

            key_to_check = model_module_path_for_ref
            name_to_add = class_name_for_ref

            if not resolve_alias_target:
                # Check for self-reference: if we're generating the same class that we're trying to import
                is_self_reference = self._is_self_reference(module_name_for_ref, class_name_for_ref)

                if is_self_reference:
                    # For self-references, don't add import and return quoted type name
                    return f'"{name_to_add}"'
                else:
                    # For external references, add import and return unquoted type name
                    self.context.add_import(logical_module=key_to_check, name=name_to_add)
                    return name_to_add
            else:
                # self.resolve_alias_target is TRUE. We are trying to find the *actual underlying type*
                # of 'ref_schema' for use in an alias definition (e.g., MyStringAlias: TypeAlias = str).
                # Check if ref_schema is structurally a simple alias (no properties, enum, composition)
                is_structurally_simple_alias = not (
                    ref_schema.properties
                    or ref_schema.enum
                    or ref_schema.any_of
                    or ref_schema.one_of
                    or ref_schema.all_of
                )

                if is_structurally_simple_alias:
                    # It's an alias to a primitive, array, or simple object.
                    # We need to return the Python type of its target.
                    # For this, we delegate back to the main resolver, but on ref_schema's definition,
                    # and crucially, with resolve_alias_target=False for that sub-call to avoid loops
                    # and to get the structural type.
                    # Also, treat ref_schema as anonymous for this sub-resolution so it's purely structural.

                    # Construct a temporary schema that is like ref_schema but anonymous
                    # to force structural resolution by the main resolver.
                    # This is a bit of a workaround for not having direct access to other resolvers here.
                    # A better design might involve passing the main SchemaTypeResolver instance.
                    # For now, returning None effectively tells TypeHelper to do this.

                    return None  # Signal to TypeHelper to resolve ref_schema structurally.
                else:
                    # ref_schema is NOT structurally alias-like (e.g., it's a full object schema).
                    # If we are resolving an alias target, and the target is a full object schema,
                    # the "target type" IS that object schema's name.
                    # e.g. MyDataAlias = DataObject. Here, DataObject is the target.
                    # The AliasGenerator will then generate "MyDataAlias: TypeAlias = DataObject".
                    # It needs "DataObject" as the string.
                    # The import for DataObject will be handled by TypeHelper when generating that alias
                    # file itself, using the regular non-alias-target path.

                    self.context.add_import(logical_module=key_to_check, name=name_to_add)
                    return name_to_add  # Return name_to_add

        elif schema.enum:
            # This is an INLINE enum definition (not a reference to a global enum)
            enum_name: str | None = None
            if schema.name:  # If the inline enum has a name, it will be generated as a named enum class
                enum_name = NameSanitizer.sanitize_class_name(schema.name)
                module_name = NameSanitizer.sanitize_module_name(schema.name)
                model_module_path = f"{self.context.get_current_package_name_for_generated_code()}.models.{module_name}"
                self.context.add_import(logical_module=model_module_path, name=enum_name)
                return enum_name
            else:  # Inline anonymous enum, falls back to primitive type of its values
                # (Handled by PrimitiveTypeResolver if this returns None or specific primitive)
                # For now, this path might lead to PrimitiveTypeResolver via TypeHelper's main loop.
                # Let's try to return the primitive type directly if possible.
                primitive_type_of_enum = "str"  # Default for enums if type not specified
                if schema.type == "integer":
                    primitive_type_of_enum = "int"
                elif schema.type == "number":
                    primitive_type_of_enum = "float"
                # other types for enums are unusual.
                return primitive_type_of_enum
        else:
            # Not a reference to a known schema, and not an inline enum.
            # This could be an anonymous complex type, or an unresolved reference.
            # Defer to other resolvers by returning None.

            return None
