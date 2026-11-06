import unittest
from unittest.mock import MagicMock, patch

from smartmove.simulation.simulation_engine import SimulationEngine

class TestSimulationEngine(unittest.TestCase):
    """
    Unit tests for SimulationEngine.
    Mocks out file system operations, factories, and thread startups
    to test the orchestration logic in isolation.
    """

    def setUp(self):
        self.mock_controller = MagicMock()
        self.engine = SimulationEngine(controller=self.mock_controller, telemetry_worker_count=2)
        # Mock the factory so we don't actually create real objects
        self.engine.telemetry_factory = MagicMock()

    @patch("smartmove.simulation.simulation_engine.load_users")
    @patch("smartmove.simulation.simulation_engine.load_vehicles")
    @patch("smartmove.simulation.simulation_engine.users_exist")
    @patch("smartmove.simulation.simulation_engine.vehicles_exist")
    def test_bootstrap_loads_existing_data(self, mock_v_exist, mock_u_exist, mock_load_v, mock_load_u):
        """Test that bootstrap loads from disk if data already exists."""
        mock_v_exist.return_value = True
        mock_u_exist.return_value = True
        
        mock_v = MagicMock()
        mock_load_v.return_value = {"V1": mock_v}
        mock_load_u.return_value = {"U1": MagicMock()}

        self.engine.bootstrap()

        mock_load_v.assert_called_once()
        mock_load_u.assert_called_once()
        self.engine.telemetry_factory.create_initial.assert_called_once_with(mock_v)
        self.mock_controller.bind_runtime_state.assert_called_once()

    @patch("smartmove.simulation.simulation_engine.save_users")
    @patch("smartmove.simulation.simulation_engine.save_vehicles")
    @patch("smartmove.simulation.simulation_engine.UserFactory")
    @patch("smartmove.simulation.simulation_engine.VehicleFactory")
    @patch("smartmove.simulation.simulation_engine.users_exist")
    @patch("smartmove.simulation.simulation_engine.vehicles_exist")
    def test_bootstrap_creates_new_data(self, mock_v_exist, mock_u_exist, mock_v_factory, mock_u_factory, mock_save_v, mock_save_u):
        """Test that bootstrap creates new fleets and users if none exist on disk."""
        mock_v_exist.return_value = False
        mock_u_exist.return_value = False
        
        mock_v = MagicMock()
        mock_v_factory.create_fleet.return_value = {"V1": mock_v}
        mock_u_factory.create_users.return_value = {"U1": MagicMock()}

        self.engine.bootstrap()

        mock_v_factory.create_fleet.assert_called_once()
        mock_u_factory.create_users.assert_called_once()
        mock_save_v.assert_called_once()
        mock_save_u.assert_called_once()
        self.mock_controller.bind_runtime_state.assert_called_once()

    @patch("smartmove.simulation.simulation_engine.TelemetryWorker")
    def test_build_telemetry_workers(self, mock_worker_class):
        """Test that vehicles are correctly chunked into the right number of workers."""
        # Setup 4 dummy vehicles
        self.engine.vehicles = {f"V{i}": MagicMock() for i in range(4)}
        self.engine.telemetry_worker_count = 2  # Should create chunks of 2
        
        workers = self.engine._build_telemetry_workers()
        
        self.assertEqual(len(workers), 2)
        # Check if TelemetryWorker was instantiated twice
        self.assertEqual(mock_worker_class.call_count, 2)

    def test_build_telemetry_workers_empty(self):
        """Test that building workers with no vehicles returns an empty list safely."""
        self.engine.vehicles = {}
        workers = self.engine._build_telemetry_workers()
        self.assertEqual(workers, [])

    @patch("smartmove.simulation.simulation_engine.RentalSimulator")
    @patch("smartmove.simulation.simulation_engine.TelemetrySimulator")
    @patch("smartmove.simulation.simulation_engine.EventProcessor")
    def test_start_simulations(self, mock_processor_class, mock_telemetry_sim, mock_rental_sim):
        """Test that start() initializes and starts all necessary background threads."""
        # Mock the instances returned by the classes
        mock_processor_instance = MagicMock()
        mock_processor_class.return_value = mock_processor_instance
        
        mock_telemetry_instance = MagicMock()
        mock_telemetry_sim.return_value = mock_telemetry_instance
        
        mock_rental_instance = MagicMock()
        mock_rental_sim.return_value = mock_rental_instance
        
        # Override _build_telemetry_workers to avoid testing it here
        self.engine._build_telemetry_workers = MagicMock(return_value=[])

        self.engine.start()

        mock_processor_instance.start.assert_called_once()
        mock_telemetry_instance.start.assert_called_once()
        mock_rental_instance.start.assert_called_once()

    def test_stop_simulations(self):
        """Test that stop() safely attempts to stop and join all running threads."""
        self.engine.rental_simulator = MagicMock()
        self.engine.telemetry_simulator = MagicMock()
        self.engine.event_processor = MagicMock()

        self.engine.stop()

        self.engine.rental_simulator.stop.assert_called_once()
        self.engine.rental_simulator.join.assert_called_once()
        
        self.engine.telemetry_simulator.stop.assert_called_once()
        # Note: telemetry_simulator does not have join() called in the original code
        
        self.engine.event_processor.stop.assert_called_once()
        self.engine.event_processor.join.assert_called_once()

    def test_stop_with_none(self):
        """Test that stop() handles None values without raising exceptions."""
        self.engine.rental_simulator = None
        self.engine.telemetry_simulator = None
        self.engine.event_processor = None
        
        # Should not raise any attribute errors
        self.engine.stop()

if __name__ == "__main__":
    unittest.main()