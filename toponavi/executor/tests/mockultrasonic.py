class MockUltrasonic:
    def __init__(self, reading):
        self._reading = reading

    def measure(self):
        return self._reading
