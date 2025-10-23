"""Enhanced schema-based data generator using Faker."""

import logging
from typing import Any, Dict, Optional

from faker import Faker

from .schema_reference_resolver import SchemaReferenceResolver
from .type_mapper import TypeMapper


class SchemaDataGenerator:
    """Generate realistic data based on JSON schema using Faker."""

    def __init__(self, locale: str = "en_US"):
        self.fake = Faker(locale)
        self.logger = logging.getLogger(__name__)
        self.type_mapper = TypeMapper(self.fake)
        self.schema_validator = SchemaReferenceResolver()

    def create_schema_data(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data for the full schema, resolving references as needed."""
        try:
            if not schema:
                self.logger.debug("Empty schema provided for data generation.")
                return {}

            if schema.get("type") == "object":
                return self._generate_object_with_refs(schema)
            else:
                return self.generate_from_schema("root", schema)
        except Exception as e:
            self.logger.error(f"Failed to generate complete schema data: {e}")
            return {}

    def _generate_object_with_refs(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate object with support for $ref and $defs, using SchemaValidator for reference resolution."""
        obj = {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        defs = schema.get("$defs", {})
        for prop_key, prop_schema in properties.items():
            # Handle $ref references
            resolved_schema = self.schema_validator.resolve_ref(prop_schema, defs)
            # Always include required properties, randomly include others
            if prop_key in required or self.fake.boolean(chance_of_getting_true=80):
                obj[prop_key] = self._generate_from_resolved_schema(
                    prop_key, resolved_schema, defs
                )
        return obj

    def _generate_array(
        self, key: str, schema: Dict[str, Any], defs: Optional[Dict[str, Any]] = None
    ) -> list:
        """Generate array value with proper item schema handling."""
        min_items = schema.get("minItems", 1)
        max_items = schema.get("maxItems", 3)
        array_length = self.fake.random_int(min_items, max_items)
        items_schema = schema.get("items", {})
        return [
            self._generate_from_resolved_schema(
                f"{key}_item_{i}", items_schema, defs or {}
            )
            for i in range(array_length)
        ]

    def _generate_object(
        self, schema: Dict[str, Any], defs: Optional[Dict[str, Any]] = None
    ) -> dict:
        """Generate object value with proper property handling."""
        obj = {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for prop_key, prop_schema in properties.items():
            if prop_key in required or self.fake.boolean(chance_of_getting_true=70):
                obj[prop_key] = self._generate_from_resolved_schema(
                    prop_key, prop_schema, defs or {}
                )
        return obj

    def _generate_from_resolved_schema(
        self, key: str, schema: Dict[str, Any], defs: Dict[str, Any]
    ) -> Any:
        """Generate data from a resolved schema (helper method)."""
        # Check for explicit default value
        if "default" in schema:
            return schema["default"]
        # Resolve any remaining refs
        resolved_schema = self.schema_validator.resolve_ref(schema, defs)
        # Generate value using TypeMapper
        data_type = resolved_schema.get("type", "").lower()
        if data_type in ["array", "list"]:
            return self._generate_array(key, resolved_schema, defs)
        elif data_type in ["object", "dict"]:
            return self._generate_object(resolved_schema, defs)
        else:
            return self.type_mapper.generate_realistic_value(key, resolved_schema)

    def generate_from_schema(self, key: str, schema: Dict[str, Any]) -> Any:
        """Generate realistic data based on JSON schema definition."""
        try:
            data_type = schema.get("type", "").lower()
            if data_type in ["array", "list"]:
                return self._generate_array(key, schema)
            elif data_type in ["object", "dict"]:
                return self._generate_object(schema)
            return self.type_mapper.generate_realistic_value(key, schema)
        except Exception as e:
            raise ValueError(
                f"Failed to generate realistic value for '{key}': {e}"
            ) from e
