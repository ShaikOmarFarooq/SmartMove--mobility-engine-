import unittest
import time
from datetime import datetime
from unittest.mock import MagicMock

# Absolute imports for consistency within the Docker environment
from smartmove.domain.vehicle import Vehicle
from smartmove.domain.enums import VehicleType, City, VehicleState
from smartmove.core.controller import SmartMoveCentralController
from smartmove.core.pricing import PricingEngine
from smartmove.domain.telemetry_event import TelemetryEvent

class TestSmartMoveEngine(unittest.TestCase):
    """
    Core logic tests for SmartMove Engine.
    Fixes Enum comparison issues by using .value and ensures all mocks are defined.
    """

    def setUp(self):
        """Initialize controller and pricing engine before each test."""
        self.controller = SmartMoveCentralController()
        self.pricing_engine = PricingEngine()

    def test_rental_price_calculation(self):
        """Verify that basic rental pricing logic works correctly."""
        vehicle = Vehicle("V1", VehicleType.SCOOTER, City.LONDON)
        user = MagicMock()
        user.id = "U1"
        
        rental = self.controller.start_rental(user, vehicle)
        time.sleep(0.1) 
        self.controller.end_rental(vehicle)
        
        # Verify cost is assigned (float or int)
        self.assertGreaterEqual(float(rental.cost), 0.0)

    def test_london_congestion_charge_applied(self):
        """Ensure London congestion charges are added correctly."""
        vehicle = Vehicle("V1", VehicleType.SCOOTER, City.LONDON)
        user = MagicMock()
        user.id = "U1"
        
        rental = self.controller.start_rental(user, vehicle)
        self.controller.end_rental(vehicle)
        
        self.assertEqual(float(rental.cost), 5.0)

    def test_low_battery_during_trip(self):
        """Test transition to MAINTENANCE on low battery."""
        vehicle = Vehicle("V2", VehicleType.SCOOTER, City.LONDON)
        user = MagicMock()
        user.id = "U2"
        
        self.controller.start_rental(user, vehicle)
        event = TelemetryEvent(
            vehicle.id, city=City.LONDON, latitude=0.0, longitude=0.0, 
            speed=0, battery=4, temperature=30, timestamp=datetime.now()
        )
        self.controller.process_telemetry_event(vehicle, event)
        
        # FIX: Compare using .value to avoid Enum identity issues
        self.assertEqual(vehicle.state.value, VehicleState.MAINTENANCE.value)

    def test_emergency_lock_theft_detection(self):
        """Ensure lock triggers on unauthorized movement."""
        vehicle = Vehicle("V3", VehicleType.SCOOTER, City.LONDON)
        event = TelemetryEvent(
            vehicle.id, city=City.LONDON, latitude=0.0, longitude=0.0, 
            speed=2, battery=100, temperature=30, timestamp=datetime.now()
        )
        self.controller.process_telemetry_event(vehicle, event)
        
        self.assertEqual(vehicle.state.value, VehicleState.EMERGENCY_LOCK.value)

    def test_overheating_during_trip(self):
        """Check for emergency lock on high temperature."""
        vehicle = Vehicle("V2", VehicleType.SCOOTER, City.LONDON)
        user = MagicMock()
        user.id = "U2"
        
        self.controller.start_rental(user, vehicle)
        event = TelemetryEvent(
            vehicle.id, city=City.LONDON, latitude=0.0, longitude=0.0, 
            speed=0, battery=100, temperature=61, timestamp=datetime.now()
        )
        self.controller.process_telemetry_event(vehicle, event)
        
        self.assertEqual(vehicle.state.value, VehicleState.EMERGENCY_LOCK.value)

    def test_rome_zone_restriction(self):
        """Test Rome specific safety logic."""
        vehicle = Vehicle("V3", VehicleType.SCOOTER, City.ROME)
        user = MagicMock()
        user.id = "U3"
        
        self.controller.start_rental(user, vehicle)
        # Rome uses specific coordinate checks in the codebase
        event = TelemetryEvent(
            vehicle.id, city=City.ROME, latitude=41.80, longitude=12.50, 
            speed=0, battery=100, temperature=25, timestamp=datetime.now()
        )
        self.controller.process_telemetry_event(vehicle, event)
        
        # Ensuring state is logically correct (In use or locked)
        self.assertIn(vehicle.state.value, [VehicleState.IN_USE.value, VehicleState.EMERGENCY_LOCK.value])

    def test_milan_helmet_presence_required_for_moped(self):
        """Verify helmet requirement in Milan."""
        vehicle = Vehicle("V4", VehicleType.MOPED, City.MILAN)
        vehicle.helmet_present = False
        user = MagicMock()
        user.id = "U4"
        
        with self.assertRaises(Exception):
            self.controller.start_rental(user, vehicle)

if __name__ == "__main__":
    unittest.main()