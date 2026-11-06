from persistence.audit_log import AuditLog
from core.services.rental_service import RentalService
from core.services.telemetry_service import TelemetryService


class SmartMoveCentralController:
   

    def __init__(self, vehicles=None, users=None, audit_log=None):
        self.vehicles = vehicles or {}
        self.users = users or {}
        self.audit = audit_log or AuditLog()
        self.active_rentals = {}

        self.rental_service = RentalService(
            vehicles=self.vehicles,
            users=self.users,
            audit_log=self.audit,
            active_rentals=self.active_rentals
        )

        self.telemetry_service = TelemetryService(
            vehicles=self.vehicles,
            audit_log=self.audit,
            active_rentals=self.active_rentals,
            rental_service=self.rental_service
        )

    def bind_runtime_state(self, vehicles, users):
        """
        Allows simulation/bootstrap to inject loaded state after construction.
        Keeps dependencies explicit and improves testability.
        """
        self.vehicles = vehicles
        self.users = users

        self.rental_service.vehicles = vehicles
        self.rental_service.users = users

        self.telemetry_service.vehicles = vehicles

    def start_rental(self, user, vehicle):
        return self.rental_service.start_rental(user, vehicle)

    def end_rental(self, vehicle):
        return self.rental_service.end_rental(vehicle)

    def process_telemetry_event(self, vehicle, event):
        return self.telemetry_service.process_telemetry_event(vehicle, event)