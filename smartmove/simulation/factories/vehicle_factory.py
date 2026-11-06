import uuid
import random
from domain.vehicle import Vehicle
from domain.enums import VehicleType, City, VehicleState


class VehicleFactory:
    @staticmethod
    def create_vehicle(
        vehicle_type: VehicleType,
        city: City
    ) -> Vehicle:
        vehicle_id = f"V-{uuid.uuid4()}"

        vehicle = Vehicle(
            vehicle_id=vehicle_id,
            vtype=vehicle_type,
            city=city
        )

        # Initial conditions (realistic defaults)
        vehicle.state = VehicleState.AVAILABLE
        vehicle.battery = random.randint(50, 100)
        vehicle.temperature = random.randint(20, 35)
        vehicle.gps = (0.0, 0.0)

        # City / type specific hardware flags
        if vehicle.type == VehicleType.MOPED:
            vehicle.helmet_present = True

        return vehicle

    @staticmethod
    def create_fleet(
        size: int,
        city_distribution: dict
    ) -> dict:
        """
        city_distribution example:
        {
            City.LONDON: 0.4,
            City.MILAN: 0.3,
            City.ROME: 0.3
        }
        """

        vehicles = {}

        cities = list(city_distribution.keys())
        weights = list(city_distribution.values())

        for _ in range(size):
            city = random.choices(cities, weights=weights, k=1)[0]
            vehicle_type = random.choice(list(VehicleType))

            vehicle = VehicleFactory.create_vehicle(vehicle_type, city)
            vehicles[vehicle.id] = vehicle

        return vehicles
