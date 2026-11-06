import unittest
from unittest.mock import MagicMock

from core.event_processor import EventProcessor
from core.events import StartRentalEvent, EndRentalEvent, TelemetryReceivedEvent


class TestEventProcessor(unittest.TestCase):
    """
    Unit tests for EventProcessor to ensure correct event dispatching
    and thread-safe polling logic without getting stuck in infinite loops.
    """

    def setUp(self):
        self.event_bus = MagicMock()
        self.rental_service = MagicMock()
        self.telemetry_service = MagicMock()
        self.logger = MagicMock()

        self.processor = EventProcessor(
            event_bus=self.event_bus,
            rental_service=self.rental_service,
            telemetry_service=self.telemetry_service,
            logger=self.logger
        )

    def test_dispatch_start_rental(self):
        """Test that StartRentalEvent correctly calls start_rental_by_id."""
        event = MagicMock(spec=StartRentalEvent)
        event.user_id = "U1"
        event.vehicle_id = "V1"

        self.processor._dispatch(event)

        self.rental_service.start_rental_by_id.assert_called_once_with(
            user_id="U1", vehicle_id="V1"
        )

    def test_dispatch_end_rental(self):
        """Test that EndRentalEvent correctly calls end_rental_by_vehicle_id."""
        event = MagicMock(spec=EndRentalEvent)
        event.vehicle_id = "V1"

        self.processor._dispatch(event)

        self.rental_service.end_rental_by_vehicle_id.assert_called_once_with(
            vehicle_id="V1"
        )

    def test_dispatch_telemetry_received(self):
        """Test that TelemetryReceivedEvent correctly calls process_telemetry_by_id."""
        event = MagicMock(spec=TelemetryReceivedEvent)
        event.vehicle_id = "V1"

        self.processor._dispatch(event)

        self.telemetry_service.process_telemetry_by_id.assert_called_once_with(
            vehicle_id="V1", event=event
        )

    def test_dispatch_unknown_event(self):
        """Test that unknown events are caught and logged as warnings."""
        class UnknownEvent:
            pass

        event = UnknownEvent()
        self.processor._dispatch(event)

        self.logger.warning.assert_called_once()
        # FIX: SonarQube tavsiyesi uzerine assertIn kullanildi
        self.assertIn("Unknown event received", self.logger.warning.call_args[0][0])

    def test_run_loop_processes_event_and_stops(self):
        """Test the main run loop safely processes an event and calls task_done."""
        event = MagicMock(spec=StartRentalEvent)
        
        # FIX: Added required attributes to the mock event to prevent AttributeError
        event.user_id = "U1"
        event.vehicle_id = "V1"
        
        # We mock poll to return an event, and then IMMEDIATELY stop the processor 
        # so the while loop breaks and the test finishes.
        def mock_poll(timeout):
            self.processor.stop()
            return event
            
        self.event_bus.poll.side_effect = mock_poll
        
        self.processor.run()
        
        self.event_bus.task_done.assert_called_once()
        self.rental_service.start_rental_by_id.assert_called_once()

    def test_run_loop_handles_exception(self):
        """Test that exceptions during dispatch are logged and task_done is still called."""
        event = MagicMock(spec=StartRentalEvent)
        
        # FIX: Added required attributes to the mock event here as well
        event.user_id = "U1"
        event.vehicle_id = "V1"
        
        def mock_poll(timeout):
            self.processor.stop()
            return event
            
        self.event_bus.poll.side_effect = mock_poll
        
        # Force the service to throw an exception to test the try/except block
        self.rental_service.start_rental_by_id.side_effect = Exception("Service Down")
        
        self.processor.run()
        
        self.logger.exception.assert_called_once()
        self.event_bus.task_done.assert_called_once()
        
    def test_run_loop_skips_none(self):
        """Test that polling timeout (returning None) skips execution and loops back."""
        def mock_poll(timeout):
            self.processor.stop()
            return None
            
        self.event_bus.poll.side_effect = mock_poll
        self.processor.run()
        
        # If event is None, it should 'continue' and NOT call task_done
        self.event_bus.task_done.assert_not_called()

if __name__ == "__main__":
    unittest.main()