from dataclasses import dataclass


@dataclass(frozen=True)
class StartRentalEvent:
    user_id: str
    vehicle_id: str


@dataclass(frozen=True)
class EndRentalEvent:
    vehicle_id: str


@dataclass(frozen=True)
class TelemetryReceivedEvent:
    vehicle_id: str
    latitude: float
    longitude: float
    speed: float
    battery: float
    temperature: float
    city: object
    timestamp: object