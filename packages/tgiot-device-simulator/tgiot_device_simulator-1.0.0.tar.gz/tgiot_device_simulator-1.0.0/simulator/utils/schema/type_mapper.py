"""Type mapping utilities for schema data generation."""

import random
from typing import Any, Callable, Dict, Optional

from faker import Faker


class TypeMapper:
    """Maps schema types to appropriate Faker methods for realistic data generation."""

    def __init__(self, fake: Faker):
        self.fake = fake

    def generate_realistic_value(
        self, key: str, schema: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate realistic values based on field name and schema type, ensuring type safety."""
        key_lower = key.lower()
        schema = schema or {}

        # 1. Check for explicit default value
        if "default" in schema:
            return schema["default"]

        # 2. Field name-based heuristics
        heuristics: list[tuple[Callable[[str], bool], Callable[[], Any]]] = [
            (lambda k: any(word in k for word in ["ip", "address"]), self.fake.ipv4),
            (lambda k: any(word in k for word in ["url", "endpoint"]), self.fake.url),
            (
                lambda k: any(word in k for word in ["name", "label"]),
                lambda: self.fake.word().capitalize(),
            ),
            (lambda k: "id" in k and len(k) <= 4, self.fake.uuid4),
        ]

        expected_type = schema.get("type", "").lower()
        type_map = {
            "string": str,
            "str": str,
            "integer": int,
            "int": int,
            "number": float,
            "float": float,
            "boolean": bool,
            "bool": bool,
        }
        expected_pytype = type_map.get(expected_type, None)

        for cond, provider in heuristics:
            if cond(key_lower):
                value = provider()
                # If no type specified, accept any; else check type
                if expected_pytype is None or isinstance(value, expected_pytype):
                    return value
                # Special case: allow int for float
                if expected_pytype is float and isinstance(value, int):
                    return float(value)
                # Otherwise, fallback to type-based
                break

        # 3. Type-based fallback
        return self.generate_by_type(key, schema)

    def generate_by_type(self, key: str, schema: Dict[str, Any]) -> Any:
        """Generate data based on schema type definition."""
        data_type = schema.get("type", "").lower()
        if data_type in ["integer", "int"]:
            return self._generate_integer(schema)
        elif data_type in ["number", "float"]:
            return self._generate_number(key, schema)
        elif data_type in ["boolean", "bool"]:
            return bool(self.fake.boolean())
        elif data_type in ["string", "str"]:
            return self._generate_string(key, schema)
        else:
            return None

    def _generate_integer(self, schema: Dict[str, Any]) -> int:
        """Generate integer value."""
        min_val = schema.get("minimum", schema.get("min", 0))
        max_val = schema.get("maximum", schema.get("max", 100))
        if min_val == 0 and max_val == 100:
            return self.fake.random_int(0, 100)
        elif min_val >= 1000 and max_val <= 9999:
            return self.fake.random_int(1000, 9999)
        else:
            return random.randint(min_val, max_val)

    def _generate_number(self, key: str, schema: Dict[str, Any]) -> float:
        """Generate float value."""
        min_val = schema.get("minimum", schema.get("min", 0.0))
        max_val = schema.get("maximum", schema.get("max", 100.0))
        if min_val == 0.0 and max_val == 1.0:
            return round(
                self.fake.pyfloat(
                    left_digits=0,
                    right_digits=3,
                    positive=True,
                    min_value=0,
                    max_value=1,
                ),
                3,
            )
        else:
            return round(random.uniform(min_val, max_val), 2)

    def _generate_string(self, key: str, schema: Dict[str, Any]) -> str:
        """Generate string value."""
        if "enum" in schema:
            return str(random.choice(schema["enum"]))
        elif "choices" in schema:
            return str(random.choice(schema["choices"]))
        format_type = schema.get("format", "").lower()
        if format_type == "email":
            return str(self.fake.email())
        elif format_type in ("uri", "url"):
            return str(self.fake.url())
        elif format_type == "uuid":
            return str(self.fake.uuid4())
        elif format_type == "datetime":
            return self.fake.date_time_between().isoformat()
        max_length = schema.get("maxLength", 20)
        if max_length <= 10:
            return self.fake.word()[:max_length]
        elif max_length <= 50:
            return self.fake.text(max_nb_chars=max_length).replace("\n", " ").strip()
        else:
            return f"generated_{key}_{self.fake.random_int(100, 999)}"
