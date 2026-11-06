import unittest
from unittest.mock import patch, MagicMock
from smartmove import main

class TestMain(unittest.TestCase):
    """
    Tests for the application entry point in main.py.
    Mocks the infinite loop to test startup and graceful shutdown.
    """

    @patch("smartmove.main.SmartMoveCentralController")
    @patch("smartmove.main.SimulationEngine")
    @patch("smartmove.main.time.sleep")
    def test_main_execution_flow(self, mock_sleep, mock_engine_class, mock_controller_class):
        # Setup the engine mock instance
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        
        # Simulate user pressing Ctrl+C (KeyboardInterrupt) to exit the while True loop
        mock_sleep.side_effect = KeyboardInterrupt()

        # Execute main()
        main.main()

        # Verify the sequence of calls
        mock_engine.bootstrap.assert_called_once()
        mock_engine.start.assert_called_once()
        
        # Verify that stop() was called during the 'except KeyboardInterrupt' block
        mock_engine.stop.assert_called_once()

if __name__ == "__main__":
    unittest.main()