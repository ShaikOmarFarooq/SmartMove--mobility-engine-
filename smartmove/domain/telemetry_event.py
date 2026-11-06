from dataclasses import dataclass
from datetime import datetime


@dataclass
class TelemetryEvent:
    vehicle_id: str
    city: object
    latitude: float
    longitude: float
    speed: float
    battery: float
    temperature: float
    timestamp: datetime