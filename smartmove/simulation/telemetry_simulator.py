class TelemetrySimulator:
    """
    Coordinates multiple telemetry workers instead of one single
    sequential telemetry producer.
    """

    def __init__(self, workers):
        self.workers = workers

    def start(self):
        for worker in self.workers:
            worker.start()

    def stop(self):
        for worker in self.workers:
            worker.stop()

        for worker in self.workers:
            worker.join()