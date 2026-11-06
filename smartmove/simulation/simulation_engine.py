from .factories.vehicle_factory import VehicleFactory
from .factories.user_factory import UserFactory
from .factories.telemetry_factory import TelemetryFactory
from .telemetry_worker import TelemetryWorker
from .telemetry_simulator import TelemetrySimulator
from .rental_simulator import RentalSimulator

from domain.enums import City
from persistence.storage import (
    vehicles_exist,
    users_exist,
    load_vehicles,
    load_users,
    save_vehicles,
    save_users
)

from core.event_bus import EventBus
from core.event_processor import EventProcessor


class SimulationEngine:
    """
    Owns simulation lifecycle and wires producers to the event-driven core.
    """

    def __init__(self, controller, telemetry_worker_count=4):
        self.controller = controller
        self.vehicles = {}
        self.users = {}

        self.telemetry_factory = TelemetryFactory()
        self.telemetry_worker_count = telemetry_worker_count

        self.event_bus = EventBus()
        self.event_processor = None
        self.telemetry_simulator = None
        self.rental_simulator = None

    def bootstrap(self):
        if vehicles_exist():
            print("Loading vehicles from disk")
            self.vehicles = load_vehicles()
        else:
            print("Creating vehicle fleet")
            self.vehicles = VehicleFactory.create_fleet(
                size=10_000,
                city_distribution={
                    City.LONDON: 0.4,
                    City.MILAN: 0.3,
                    City.ROME: 0.3
                }
            )
            save_vehicles(self.vehicles)

        if users_exist():
            print("Loading users from disk")
            self.users = load_users()
        else:
            print("Creating users")
            self.users = UserFactory.create_users(2_000)
            save_users(self.users)

        print("Initializing telemetry for all vehicles")
        for vehicle in self.vehicles.values():
            vehicle.telemetry = self.telemetry_factory.create_initial(vehicle)
        print("Telemetry initialized")

        self.controller.bind_runtime_state(self.vehicles, self.users)

    def _build_telemetry_workers(self):
        vehicles_list = list(self.vehicles.values())
        if not vehicles_list:
            return []

        chunk_size = max(1, len(vehicles_list) // self.telemetry_worker_count)
        chunks = [
            vehicles_list[i:i + chunk_size]
            for i in range(0, len(vehicles_list), chunk_size)
        ]

        workers = []
        for chunk in chunks:
            workers.append(
                TelemetryWorker(
                    vehicles=chunk,
                    telemetry_factory=self.telemetry_factory,
                    event_bus=self.event_bus,
                    interval=1.0
                )
            )
        return workers

    def start(self):
        self.event_processor = EventProcessor(
            event_bus=self.event_bus,
            rental_service=self.controller.rental_service,
            telemetry_service=self.controller.telemetry_service
        )
        self.event_processor.start()

        telemetry_workers = self._build_telemetry_workers()
        self.telemetry_simulator = TelemetrySimulator(telemetry_workers)
        self.telemetry_simulator.start()

        self.rental_simulator = RentalSimulator(
            vehicles=self.vehicles,
            users=self.users,
            event_bus=self.event_bus,
            active_rentals=self.controller.active_rentals,
            interval=2.0
        )
        self.rental_simulator.start()

        print("Telemetry and rental simulation running...")

    def stop(self):
        if self.rental_simulator:
            self.rental_simulator.stop()
            self.rental_simulator.join()

        if self.telemetry_simulator:
            self.telemetry_simulator.stop()

        if self.event_processor:
            self.event_processor.stop()
            self.event_processor.join()