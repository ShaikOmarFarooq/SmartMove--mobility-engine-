from core.controller import SmartMoveCentralController
from simulation.simulation_engine import SimulationEngine
import time


def main():
    controller = SmartMoveCentralController()

    simulation = SimulationEngine(controller, telemetry_worker_count=4)

    simulation.bootstrap()
    simulation.start()

    # Keep the main thread alive while background simulation threads run.
    # If the main thread exits, the whole program terminates and all
    # background simulation activity stops.
    # Ctrl+C triggers graceful shutdown through KeyboardInterrupt.
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        simulation.stop()


if __name__ == "__main__":
    main()