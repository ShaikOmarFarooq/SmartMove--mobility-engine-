import random
import threading
import time

from domain.enums import VehicleState
from core.events import StartRentalEvent, EndRentalEvent


class RentalSimulator(threading.Thread):
    """
    Produces rental-related events instead of directly calling the controller.
    This supports the producer-consumer pattern.
    """

    def __init__(self, vehicles, users, event_bus, active_rentals, interval=2.0):
        super().__init__()
        self.vehicles = vehicles
        self.users = users
        self.event_bus = event_bus
        self.active_rentals = active_rentals
        self.interval = interval
        self._running = True

    def run(self):
        user_ids = list(self.users.keys())

        while self._running:
            available = [
                v for v in self.vehicles.values()
                if v.state == VehicleState.AVAILABLE
            ]

            if available and random.random() < 0.30:
                vehicle = random.choice(available)
                user_id = random.choice(user_ids)

                self.event_bus.publish(
                    StartRentalEvent(
                        user_id=user_id,
                        vehicle_id=vehicle.id
                    )
                )

            active_ids = list(self.active_rentals.keys())

            if active_ids and random.random() < 0.20:
                vehicle_id = random.choice(active_ids)
                self.event_bus.publish(
                    EndRentalEvent(vehicle_id=vehicle_id)
                )

            time.sleep(self.interval)

    def stop(self):
        self._running = False