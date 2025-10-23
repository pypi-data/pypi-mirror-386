"""Schema validation and resolution utilities."""

import logging
from typing import Any, Dict


class SchemaReferenceResolver:
    """Handles only schema reference resolution."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def resolve_ref(
        self, schema: Dict[str, Any], defs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve $ref references in schema."""
        if isinstance(schema, dict) and "$ref" in schema:
            ref_path = schema["$ref"]
            if ref_path.startswith("#/$defs/"):
                def_name = ref_path.replace("#/$defs/", "")
                if def_name in defs:
                    resolved = defs[def_name].copy()
                    # Recursively resolve any nested refs
                    return self._resolve_nested_refs(resolved, defs)
        return schema

    def _resolve_nested_refs(
        self, schema: Dict[str, Any], defs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recursively resolve nested $ref references."""
        result = {}
        for key, value in schema.items():
            if key == "$ref" and isinstance(value, str):
                # This is a reference, resolve it
                if value.startswith("#/$defs/"):
                    def_name = value.replace("#/$defs/", "")
                    if def_name in defs:
                        # Replace the $ref with the actual definition
                        resolved = defs[def_name].copy()
                        result.update(self._resolve_nested_refs(resolved, defs))
                        continue

            if isinstance(value, dict):
                result[key] = self._resolve_nested_refs(value, defs)
            elif isinstance(value, list):
                result[key] = [
                    self._resolve_nested_refs(item, defs)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
