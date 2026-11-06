from domain.enums import VehicleState

class TelemetryProcessor:
    def __init__(self, controller):
        self.controller = controller

    def process(self, vehicle, data):
        with vehicle.lock:
            vehicle.gps = data["gps"]
            vehicle.battery = data["battery"]
            vehicle.temperature = data["temperature"]

            if vehicle.temperature > 60:
                self.controller.transition_vehicle(
                    vehicle,
                    VehicleState.EMERGENCY_LOCK,
                    "Overheating"
                )

            if vehicle.battery < 5:
                self.controller.transition_vehicle(
                    vehicle,
                    VehicleState.MAINTENANCE,
                    "Battery critical"
                )
