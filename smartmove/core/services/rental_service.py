import uuid

from core.state_machine import StateMachine
from core.pricing import PricingEngine
from core.exceptions import (
    VehicleUnavailableError,
    NoActiveRentalError,
)
from domain.enums import VehicleState
from domain.rental import Rental
from rules.london import LondonRules
from rules.milan import MilanRules
from rules.rome import RomeRules


CITY_RULES = {
    "london": LondonRules(),
    "milan": MilanRules(),
    "rome": RomeRules()
}


class RentalService:
    """
    Handles rental lifecycle logic.
    Keeps controller thinner and improves maintainability/testability.
    """

    def __init__(self, vehicles, users, audit_log, active_rentals):
        self.vehicles = vehicles
        self.users = users
        self.audit = audit_log
        self.active_rentals = active_rentals

    def start_rental_by_id(self, user_id, vehicle_id):
        user = self.users[user_id]
        vehicle = self.vehicles[vehicle_id]
        return self.start_rental(user, vehicle)

    def end_rental_by_vehicle_id(self, vehicle_id):
        vehicle = self.vehicles[vehicle_id]
        return self.end_rental(vehicle)

    def start_rental(self, user, vehicle):
        with vehicle.lock:
            if vehicle.state != VehicleState.AVAILABLE:
                raise VehicleUnavailableError("Vehicle not available")

            rules = CITY_RULES[vehicle.city.value]
            rules.on_unlock(vehicle, user)

            rental = Rental(
                rental_id=str(uuid.uuid4()),
                user_id=user.id,
                vehicle_id=vehicle.id
            )

            self.active_rentals[vehicle.id] = rental

            old_state, new_state = StateMachine.transition(
                vehicle,
                VehicleState.IN_USE
            )

            self.audit.record(
                entity_id=vehicle.id,
                action=f"{old_state.name} -> {new_state.name}",
                reason="Rental started"
            )

            return rental

    def end_rental(self, vehicle):
        with vehicle.lock:
            rental = self.active_rentals.get(vehicle.id)
            if not rental:
                raise NoActiveRentalError("No active rental")

            rental.end()
            rental.cost = PricingEngine.calculate(rental)

            rules = CITY_RULES[vehicle.city.value]
            rules.on_end_rental(rental)

            old_state, new_state = StateMachine.transition(
                vehicle,
                VehicleState.AVAILABLE
            )

            del self.active_rentals[vehicle.id]

            self.audit.record(
                entity_id=vehicle.id,
                action=f"{old_state.name} -> {new_state.name}",
                reason=f"Rental ended. Cost: {rental.cost}"
            )

            return rental

    def terminate_active_rental(self, vehicle, reason):
        """
        Shared helper used by telemetry/safety logic so termination code
        is not duplicated in multiple branches.
        """
        rental = self.active_rentals.get(vehicle.id)
        if not rental:
            return None

        rental.end()
        del self.active_rentals[vehicle.id]

        self.audit.record(
            entity_id=vehicle.id,
            action="RENTAL_TERMINATED",
            reason=reason
        )

        return rental