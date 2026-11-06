from domain.enums import VehicleState
from core.exceptions import InvalidTransitionError


VALID_TRANSITIONS = {
    VehicleState.AVAILABLE: {
        VehicleState.RESERVED,
        VehicleState.IN_USE,
        VehicleState.MAINTENANCE,
        VehicleState.EMERGENCY_LOCK
    },
    VehicleState.RESERVED: {
        VehicleState.IN_USE,
        VehicleState.AVAILABLE
    },
    VehicleState.IN_USE: {
        VehicleState.AVAILABLE,
        VehicleState.MAINTENANCE,
        VehicleState.EMERGENCY_LOCK
    },
    VehicleState.MAINTENANCE: {
        VehicleState.AVAILABLE
    },
    VehicleState.EMERGENCY_LOCK: {
        VehicleState.MAINTENANCE
    },
    VehicleState.RELOCATING: {
        VehicleState.AVAILABLE
    }
}


class StateMachine:
    @staticmethod
    def validate(current, target):
        return target in VALID_TRANSITIONS.get(current, set())

    @staticmethod
    def transition(vehicle, target_state):
        current_state = vehicle.state

        if not StateMachine.validate(current_state, target_state):
            raise InvalidTransitionError(
                f"Invalid transition: {current_state} -> {target_state}"
            )

        vehicle.state = target_state
        return current_state, target_state