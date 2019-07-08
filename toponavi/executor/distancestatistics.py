import numpy as np

from .controller import MedianFilter

class DistanceStatisics:
    def __init__(self, config, control_interval):
        self.control_interval = control_interval
        self._filter = MedianFilter(config['median_filter'])
        self.window_size = config['window_size']
        self.window = []
        self.latest_raw = None
        self.latest_filtered = None
        self.latest = None
        self.approaching_rate = None
        self.squared_error = None
    def clear_window(self):
        self.window = []
    def data(self, raw_data):
        self.latest_raw = raw_data
        self.latest_filtered = self._filter.next(raw_data)

        self.window.append(self.latest_filtered)
        if len(self.window) > self.window_size:
            self.window.pop(0)
        if len(self.window) < 2:
            self.latest = self.latest_filtered
            self.squared_error = 0
            self.approaching_rate = 0
        else:
            x = range(-len(self.window)+1, 1)
            A = np.vstack([x, np.ones(len(x))]).T
            result = np.linalg.lstsq(A, self.window, rcond=None)
            k, self.latest = result[0]
            self.squared_error = result[1][0] if result[1] else 0
            self.approaching_rate = k / self.control_interval
