import unittest
from unittest.mock import MagicMock
from smartmove.core.telemetry import TelemetryProcessor
from smartmove.domain.enums import VehicleState

class TestTelemetryProcessor(unittest.TestCase):
    """
    Direct unit tests for TelemetryProcessor.
    Using flexible assertions to avoid memory address mismatch with Mocks and Enums.
    """

    def setUp(self):
        """Setup the telemetry processor with a mocked controller and vehicle."""
        self.mock_controller = MagicMock()
        self.processor = TelemetryProcessor(self.mock_controller)
        
        # Setup a mock vehicle with a threading lock context manager
        self.vehicle = MagicMock()
        self.vehicle.lock = MagicMock()
        self.vehicle.lock.__enter__ = MagicMock()
        self.vehicle.lock.__exit__ = MagicMock()

    def test_process_updates_attributes(self):
        """Test that vehicle attributes are updated correctly under normal conditions."""
        data = {
            "gps": (59.3293, 18.0686),
            "battery": 85,
            "temperature": 25
        }
        
        self.processor.process(self.vehicle, data)
        
        self.assertEqual(self.vehicle.gps, (59.3293, 18.0686))
        self.assertEqual(self.vehicle.battery, 85)
        self.assertEqual(self.vehicle.temperature, 25)
        self.mock_controller.transition_vehicle.assert_not_called()

    def test_process_overheating_triggers_lock(self):
        """Test that temperature > 60 triggers an EMERGENCY_LOCK."""
        data = {
            "gps": (0, 0),
            "battery": 50,
            "temperature": 65 
        }
        
        self.processor.process(self.vehicle, data)
        
        # FIX: Instead of assert_called_with, we check the arguments manually 
        # to avoid the Enum/Mock identity bug.
        args, kwargs = self.mock_controller.transition_vehicle.call_args
        self.assertEqual(args[0], self.vehicle)
        self.assertEqual(args[1].value, VehicleState.EMERGENCY_LOCK.value)
        self.assertEqual(args[2], "Overheating")

    def test_process_low_battery_triggers_maintenance(self):
        """Test that battery < 5 triggers MAINTENANCE."""
        data = {
            "gps": (0, 0),
            "battery": 3,
            "temperature": 20
        }
        
        self.processor.process(self.vehicle, data)
        
        # FIX: Accessing call_args directly is the safest way to compare Enums in tests
        args, kwargs = self.mock_controller.transition_vehicle.call_args
        self.assertEqual(args[0], self.vehicle)
        self.assertEqual(args[1].value, VehicleState.MAINTENANCE.value)
        self.assertEqual(args[2], "Battery critical")

if __name__ == "__main__":
    unittest.main()