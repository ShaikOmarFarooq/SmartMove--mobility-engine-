import threading
import time

from core.events import TelemetryReceivedEvent


class TelemetryWorker(threading.Thread):
    """
    Produces telemetry for a subset of vehicles.
    Multiple workers improve realism and concurrency.
    """

    def __init__(self, vehicles, telemetry_factory, event_bus, interval=1.0):
        super().__init__()
        self.vehicles = vehicles
        self.telemetry_factory = telemetry_factory
        self.event_bus = event_bus
        self.interval = interval
        self._running = True

    def run(self):
        while self._running:
            for vehicle in self.vehicles:
                previous_snapshot = getattr(vehicle, "telemetry", None)
                if previous_snapshot is None:
                    previous_snapshot = self.telemetry_factory.create_initial(vehicle)
                    vehicle.telemetry = previous_snapshot

                new_snapshot = self.telemetry_factory.next_snapshot(
                    vehicle,
                    previous_snapshot
                )

                with vehicle.lock:
                    vehicle.telemetry = new_snapshot

                event = self.telemetry_factory.to_event(vehicle, new_snapshot)

                self.event_bus.publish(
                    TelemetryReceivedEvent(
                        vehicle_id=event.vehicle_id,
                        latitude=event.latitude,
                        longitude=event.longitude,
                        speed=event.speed,
                        battery=event.battery,
                        temperature=event.temperature,
                        city=event.city,
                        timestamp=event.timestamp
                    )
                )

            time.sleep(self.interval)

    def stop(self):
        self._running = False