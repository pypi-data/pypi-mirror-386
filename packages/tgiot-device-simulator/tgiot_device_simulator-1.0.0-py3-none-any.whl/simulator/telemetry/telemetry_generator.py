"""Schema-based telemetry generator."""

import logging
from typing import Any, Dict, List

from simulator.config.config_manager import ConfigManager
from simulator.config.schemas import DeviceSchema
from simulator.utils.schema.schema_generator import SchemaDataGenerator

from .message_generators import (
    AlertsGenerator,
    D2CStatusGenerator,
    FwDebugGenerator,
    MeasurementGenerator,
)


class TelemetryGenerator:
    """Main telemetry generator that coordinates schema-based and mock generation."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.schema = None
        self.schema_generator = SchemaDataGenerator()

        # Initialize message generators
        self.alerts_generator = AlertsGenerator(config_manager)
        self.d2c_status_generator = D2CStatusGenerator(
            config_manager, self.alerts_generator
        )
        self.measurement_generator = MeasurementGenerator(config_manager)
        self.sw_logs_generator = FwDebugGenerator(config_manager)

    def generate_telemetry(
        self, message_type: str, device_schema: DeviceSchema
    ) -> List[Dict[str, Any]]:
        """Generate telemetry messages of the specified type."""
        try:
            if message_type == "state":
                return [self.d2c_status_generator.generate_message(device_schema)]
            elif message_type == "measurement":
                return [self.measurement_generator.generate_message(device_schema)]
            elif message_type == "events":
                return [self.alerts_generator.generate_message(device_schema)]
            elif message_type == "sw_logs":
                return [self.sw_logs_generator.generate_message(device_schema)]

            # default message
            if hasattr(device_schema, "to_dict"):
                schema_dict = device_schema.to_dict()
            else:
                schema_dict = device_schema
            msg = self.schema_generator.create_schema_data(schema_dict)
            return [msg]
        except Exception as e:
            self.logger.error(f"Error generating {message_type} telemetry: {e}")
            return []
