from queue import Queue, Empty


class EventBus:
    """
    Thread-safe event queue used by producers (simulators)
    and consumed by the event processor.
    """

    def __init__(self):
        self._queue = Queue()

    def publish(self, event):
        self._queue.put(event)

    def poll(self, timeout=0.5):
        try:
            return self._queue.get(timeout=timeout)
        except Empty:
            return None

    def task_done(self):
        self._queue.task_done()