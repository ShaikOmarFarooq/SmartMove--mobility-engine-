import random
from datetime import datetime
from domain.telemetry_snapshot import TelemetrySnapshot
from domain.telemetry_event import TelemetryEvent
from domain.enums import VehicleState


class TelemetryFactory:

    @staticmethod
    def create_initial(vehicle) -> TelemetrySnapshot:
        lat, lon = vehicle.gps

        return TelemetrySnapshot(
            latitude=lat,
            longitude=lon,
            speed=0.0,
            battery=vehicle.battery,
            temperature=vehicle.temperature
        )

    @staticmethod
    def next_snapshot(vehicle, previous: TelemetrySnapshot) -> TelemetrySnapshot:
        # Vehicle in active trip
        if vehicle.state == VehicleState.IN_USE:
            speed = random.uniform(8, 28)
            battery_drain = random.uniform(0.8, 2.5)
            temp_change = random.uniform(0.3, 1.5)

            # occasional overheating spike while in use
            if random.random() < 0.03:
                temp_change += random.uniform(15, 35)

        # Vehicle locked / emergency / maintenance / available
        else:
            speed = 0.0
            battery_drain = random.uniform(0.0, 0.03)
            temp_change = random.uniform(-0.2, 0.2)

        lat_shift = random.uniform(-0.00005, 0.00005) if speed > 0 else 0.0
        lon_shift = random.uniform(-0.00005, 0.00005) if speed > 0 else 0.0

        new_battery = max(previous.battery - battery_drain, 0)
        new_temperature = max(15.0, previous.temperature + temp_change)

        return TelemetrySnapshot(
            latitude=previous.latitude + lat_shift,
            longitude=previous.longitude + lon_shift,
            speed=speed,
            battery=new_battery,
            temperature=new_temperature
        )

    @staticmethod
    def to_event(vehicle, snapshot: TelemetrySnapshot) -> TelemetryEvent:
        return TelemetryEvent(
            vehicle_id=vehicle.id,
            city=vehicle.city,
            latitude=snapshot.latitude,
            longitude=snapshot.longitude,
            speed=snapshot.speed,
            battery=snapshot.battery,
            temperature=snapshot.temperature,
            timestamp=datetime.now()
        )