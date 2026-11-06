import threading

from core.events import (
    StartRentalEvent,
    EndRentalEvent,
    TelemetryReceivedEvent,
)


class EventProcessor(threading.Thread):
    """
    Consumes events from the EventBus and dispatches them
    to the appropriate service.
    """

    def __init__(self, event_bus, rental_service, telemetry_service, logger=None):
        super().__init__()
        self.event_bus = event_bus
        self.rental_service = rental_service
        self.telemetry_service = telemetry_service
        self.logger = logger
        self._running = True

    def run(self):
        while self._running:
            event = self.event_bus.poll(timeout=0.5)
            if event is None:
                continue

            try:
                self._dispatch(event)
            except Exception as exc:
                if self.logger:
                    self.logger.exception("Event processing failed: %s", exc)
            finally:
                self.event_bus.task_done()

    def _dispatch(self, event):
        if isinstance(event, StartRentalEvent):
            self.rental_service.start_rental_by_id(
                user_id=event.user_id,
                vehicle_id=event.vehicle_id
            )
            return

        if isinstance(event, EndRentalEvent):
            self.rental_service.end_rental_by_vehicle_id(
                vehicle_id=event.vehicle_id
            )
            return

        if isinstance(event, TelemetryReceivedEvent):
            self.telemetry_service.process_telemetry_by_id(
                vehicle_id=event.vehicle_id,
                event=event
            )
            return

        if self.logger:
            self.logger.warning("Unknown event received: %s", type(event).__name__)

    def stop(self):
        self._running = False