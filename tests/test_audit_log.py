import unittest
import os
import json
from smartmove.persistence.audit_log import AuditLog
from core.exceptions import IntegrityCheckError

class TestAuditLog(unittest.TestCase):

    def setUp(self):
        # FIX: Ensure the directory exists
        self.test_dir = "data"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
            
        self.test_log_path = os.path.join(self.test_dir, "test_audit.log")

        if os.path.exists(self.test_log_path):
            os.remove(self.test_log_path)

        # FIX: Use 'filepath' instead of 'path' to match the class signature
        self.audit = AuditLog(filepath=self.test_log_path)

    def tearDown(self):
        if os.path.exists(self.test_log_path):
            os.remove(self.test_log_path)

    def test_audit_log_file_created(self):
        self.audit.record("V1", "AVAILABLE -> IN_USE", "Rental started")
        self.assertTrue(os.path.exists(self.test_log_path))

    def test_checksum_chain_is_linked(self):
        self.audit.record("V1", "AVAILABLE -> IN_USE", "Rental started")
        self.audit.record("V1", "IN_USE -> AVAILABLE", "Rental ended")

        with open(self.test_log_path, "r") as f:
            lines = f.readlines()

        first_entry = json.loads(lines[0])
        second_entry = json.loads(lines[1])

        # FIX: Matches 'previous_checksum' as defined in the AuditLog class
        self.assertEqual(second_entry["previous_checksum"], first_entry["checksum"])

    def test_audit_entries_contain_expected_fields(self):
        self.audit.record("V1", "AVAILABLE -> IN_USE", "Rental started")

        with open(self.test_log_path, "r") as f:
            entry = json.loads(f.readline())

        self.assertIn("entity_id", entry)
        self.assertIn("action", entry)
        self.assertIn("reason", entry)
        self.assertIn("previous_checksum", entry) # Fixed
        self.assertIn("checksum", entry)

    # --- NEW TESTS TO INCREASE COVERAGE ---

    def test_integrity_verification_success(self):
        """verify_integrity should return True if the log file is intact and compliant."""
        self.audit.record("V1", "ACTION1", "Reason 1")
        self.audit.record("V2", "ACTION2", "Reason 2")
        self.assertTrue(self.audit.verify_integrity())

    def test_integrity_fails_when_file_tampered(self):
        """Verification should raise an error if the log file is tampered with."""
        self.audit.record("V1", "ACTION1", "Reason 1")
        
        # Open the file and corrupt its content (simulating manual tampering)
        with open(self.test_log_path, "a") as f:
            f.write(json.dumps({"id": 99, "action": "HACKED"}) + "\n")
            
        with self.assertRaises(IntegrityCheckError):
            self.audit.verify_integrity()

    def test_empty_log_integrity(self):
        """An empty log file is technically consistent."""
        self.assertTrue(self.audit.verify_integrity())