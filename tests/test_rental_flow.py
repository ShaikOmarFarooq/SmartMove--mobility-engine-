import unittest
from smartmove.domain.vehicle import Vehicle
from smartmove.domain.enums import VehicleType, City, VehicleState
from smartmove.core.controller import SmartMoveCentralController


class TestRentalFlow(unittest.TestCase):

    def test_vehicle_not_available(self):
        controller = SmartMoveCentralController()
        vehicle = Vehicle("V1", VehicleType.SCOOTER, City.LONDON)
        vehicle.state = VehicleState.MAINTENANCE
        user = type("User", (), {"id": "U1"})()

        with self.assertRaises(Exception):
            controller.start_rental(user, vehicle)

    def test_end_rental_without_active_rental(self):
        controller = SmartMoveCentralController()
        vehicle = Vehicle("V2", VehicleType.SCOOTER, City.LONDON)

        with self.assertRaises(Exception):
            controller.end_rental(vehicle)

    def test_invalid_user_cannot_start_rental(self):
        controller = SmartMoveCentralController()
        vehicle = Vehicle("V3", VehicleType.SCOOTER, City.LONDON)

        with self.assertRaises(Exception):
            controller.start_rental(None, vehicle)

    def test_successful_rental_changes_state(self):
        controller = SmartMoveCentralController()
        vehicle = Vehicle("V6", VehicleType.SCOOTER, City.LONDON)
        user = type("User", (), {"id": "U3"})()

        controller.start_rental(user, vehicle)
        self.assertEqual(vehicle.state.value, VehicleState.IN_USE.value)

    def test_end_rental_returns_vehicle_to_available(self):
        controller = SmartMoveCentralController()
        vehicle = Vehicle("V7", VehicleType.SCOOTER, City.LONDON)
        user = type("User", (), {"id": "U4"})()

        controller.start_rental(user, vehicle)
        controller.end_rental(vehicle)

        self.assertEqual(vehicle.state.value, VehicleState.AVAILABLE.value)


if __name__ == "__main__":
    unittest.main()