import hashlib
import json
import os
import threading
from datetime import datetime

from core.exceptions import AuditWriteError, IntegrityCheckError


class AuditLog:
    """
    Thread-safe append-only audit log with sequential IDs and checksum chaining.
    Improves reliability and integrity.
    """

    def __init__(self, filepath="data/audit.log"):
        self.filepath = filepath
        print("AUDIT ABS PATH:", os.path.abspath(self.filepath))
        self.filepath = filepath
        self._lock = threading.Lock()

        directory = os.path.dirname(self.filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)

        if not os.path.exists(self.filepath):
            open(self.filepath, "a", encoding="utf-8").close()

    def _read_entries(self):
        entries = []
        if not os.path.exists(self.filepath):
            return entries

        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entries.append(json.loads(line))
        return entries

    def _hash_payload(self, payload: str) -> str:
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def record(self, entity_id, action, reason):
        print("WRITING TO:", os.path.abspath(self.filepath))
        print("AUDIT RECORD CALLED:", entity_id, action, reason)
        with self._lock:
            try:
                entries = self._read_entries()

                previous_id = entries[-1]["id"] if entries else 0
                previous_checksum = entries[-1]["checksum"] if entries else "GENESIS"

                entry = {
                    "id": previous_id + 1,
                    "timestamp": datetime.now().isoformat(),
                    "entity_id": entity_id,
                    "action": action,
                    "reason": reason,
                    "previous_checksum": previous_checksum,
                }

                checksum_basis = json.dumps(entry, sort_keys=True)
                entry["checksum"] = self._hash_payload(checksum_basis)

                with open(self.filepath, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")

            except Exception as exc:
                raise AuditWriteError(f"Failed to write audit log: {exc}") from exc

    def verify_integrity(self):
        with self._lock:
            entries = self._read_entries()
            expected_previous = "GENESIS"
            expected_id = 1

            for entry in entries:
                if entry["id"] != expected_id:
                    raise IntegrityCheckError(
                        f"Audit log ID sequence broken at entry {entry}"
                    )

                if entry["previous_checksum"] != expected_previous:
                    raise IntegrityCheckError(
                        f"Audit checksum chain broken at entry {entry['id']}"
                    )

                checksum = entry["checksum"]
                entry_without_checksum = dict(entry)
                del entry_without_checksum["checksum"]

                checksum_basis = json.dumps(entry_without_checksum, sort_keys=True)
                recomputed = self._hash_payload(checksum_basis)

                if checksum != recomputed:
                    raise IntegrityCheckError(
                        f"Audit checksum mismatch at entry {entry['id']}"
                    )

                expected_previous = checksum
                expected_id += 1
            return True