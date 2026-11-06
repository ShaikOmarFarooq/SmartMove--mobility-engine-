from dataclasses import dataclass

@dataclass
class TelemetrySnapshot:
    latitude: float
    longitude: float
    speed: float
    battery: float
    temperature: float
