from enum import Enum

class VehicleState(Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    EMERGENCY_LOCK = "emergency_lock"
    RELOCATING = "relocating"

class VehicleType(Enum):
    BIKE = "bike"
    SCOOTER = "scooter"
    MOPED = "moped"

class City(Enum):
    LONDON = "london"
    MILAN = "milan"
    ROME = "rome"
