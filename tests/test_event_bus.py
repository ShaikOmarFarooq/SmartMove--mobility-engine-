import unittest
from smartmove.core.event_bus import EventBus

class TestEventBus(unittest.TestCase):
    """
    Unit tests for the EventBus class to ensure thread-safe 
    event publishing and polling.
    """

    def setUp(self):
        # Create a fresh EventBus instance before each test
        self.event_bus = EventBus()

    def test_publish_and_poll_event(self):
        """Test that an event can be published and successfully polled."""
        mock_event = {"type": "RENTAL_STARTED", "vehicle_id": "V123"}
        
        # Publish the event
        self.event_bus.publish(mock_event)
        
        # Poll the event and verify it matches
        polled_event = self.event_bus.poll()
        self.assertEqual(polled_event, mock_event)

    def test_poll_empty_bus_returns_none(self):
        """Test polling an empty event bus returns None after timeout."""
        # Poll with a very short timeout to keep tests fast
        polled_event = self.event_bus.poll(timeout=0.1)
        
        # Should return None because the queue is empty
        self.assertIsNone(polled_event)

    def test_task_done(self):
        """Test that task_done can be called without errors after polling an event."""
        mock_event = {"type": "TELEMETRY_UPDATE"}
        
        self.event_bus.publish(mock_event)
        self.event_bus.poll()
        
        # Call task_done. If it throws a ValueError, the test will fail automatically.
        try:
            self.event_bus.task_done()
        except ValueError:
            self.fail("task_done() raised ValueError unexpectedly. The queue internal count is wrong.")

if __name__ == "__main__":
    unittest.main()