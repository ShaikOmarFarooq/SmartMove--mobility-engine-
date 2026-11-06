import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

from smartmove.persistence import storage

class TestStorage(unittest.TestCase):
    """
    Unit tests for the storage module.
    Uses temporary directories and mocked domain objects
    to prevent modifying real data files during tests.
    """

    def setUp(self):
        # Create a temporary directory for safe testing
        self.test_dir = tempfile.TemporaryDirectory()
        
        # Override file paths to use the temp directory
        self.orig_vehicles_file = storage.VEHICLES_FILE
        self.orig_users_file = storage.USERS_FILE
        
        storage.VEHICLES_FILE = os.path.join(self.test_dir.name, "vehicles.json")
        storage.USERS_FILE = os.path.join(self.test_dir.name, "users.json")

    def tearDown(self):
        # Restore original paths and clean up the temp directory
        storage.VEHICLES_FILE = self.orig_vehicles_file
        storage.USERS_FILE = self.orig_users_file
        self.test_dir.cleanup()

    def test_atomic_write_json(self):
        """Test that atomic write correctly formats and saves JSON data."""
        test_file = os.path.join(self.test_dir.name, "atomic_test.json")
        data = [{"key": "value"}]
        storage._atomic_write_json(test_file, data)
        
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, "r") as f:
            self.assertEqual(json.load(f), data)

    def test_exist_functions(self):
        """Test vehicles_exist and users_exist return correct boolean values."""
        self.assertFalse(storage.vehicles_exist())
        self.assertFalse(storage.users_exist())
        
        # Simulate file creation
        with open(storage.VEHICLES_FILE, "w") as f: f.write("[]")
        with open(storage.USERS_FILE, "w") as f: f.write("[]")
        
        self.assertTrue(storage.vehicles_exist())
        self.assertTrue(storage.users_exist())

    @patch("smartmove.persistence.storage.Vehicle")
    @patch("smartmove.persistence.storage.VehicleType")
    @patch("smartmove.persistence.storage.City")
    @patch("smartmove.persistence.storage.VehicleState")
    def test_save_and_load_vehicles(self, mock_state, mock_city, mock_type, mock_vehicle_class):
        """Test saving a mock vehicle and loading it back."""
        # Setup a dummy vehicle to save
        mock_v = MagicMock()
        mock_v.id = "V1"
        mock_v.type.value = "SCOOTER"
        mock_v.city.value = "ROME"
        mock_v.state.value = "AVAILABLE"
        mock_v.gps = [41.9, 12.4]
        mock_v.battery = 100
        mock_v.temperature = 22
        mock_v.helmet_present = True

        # Perform save operation
        storage.save_vehicles({"V1": mock_v})
        self.assertTrue(os.path.exists(storage.VEHICLES_FILE))

        # Setup mock for the load operation
        mock_loaded_v = MagicMock()
        mock_loaded_v.id = "V1"  # Fixed missing ID
        mock_vehicle_class.return_value = mock_loaded_v

        # Perform load operation
        loaded_vehicles = storage.load_vehicles()
        
        self.assertIn("V1", loaded_vehicles)
        mock_vehicle_class.assert_called_once()

    def test_load_vehicles_invalid_format(self):
        """Test load_vehicles raises ValueError if JSON root is not a list."""
        with open(storage.VEHICLES_FILE, "w") as f:
            json.dump({"not_a_list": True}, f)
            
        with self.assertRaises(ValueError):
            storage.load_vehicles()

    def test_load_vehicles_skips_non_dict(self):
        """Test load_vehicles safely ignores items that are not dictionaries."""
        with open(storage.VEHICLES_FILE, "w") as f:
            json.dump(["string_instead_of_dict"], f)
            
        self.assertEqual(storage.load_vehicles(), {})

    @patch("smartmove.persistence.storage.User")
    def test_save_and_load_users(self, mock_user_class):
        """Test saving a mock user and loading it back."""
        mock_u = MagicMock()
        mock_u.id = "U1"
        mock_u.name = "Test User"
        
        storage.save_users({"U1": mock_u})
        self.assertTrue(os.path.exists(storage.USERS_FILE))
        
        mock_loaded_u = MagicMock()
        mock_loaded_u.id = "U1"  # Fixed missing ID
        mock_user_class.return_value = mock_loaded_u
        
        loaded_users = storage.load_users()
        self.assertIn("U1", loaded_users)
        
    def test_load_users_invalid_format(self):
        """Test load_users raises ValueError if JSON root is not a list."""
        with open(storage.USERS_FILE, "w") as f:
            json.dump({"not_a_list": True}, f)
            
        with self.assertRaises(ValueError):
            storage.load_users()

    def test_load_users_skips_non_dict(self):
        """Test load_users safely ignores items that are not dictionaries."""
        with open(storage.USERS_FILE, "w") as f:
            json.dump(["string_instead_of_dict"], f)
            
        self.assertEqual(storage.load_users(), {})

if __name__ == "__main__":
    unittest.main()