import numpy as np

class DistanceStatisics:
    def __init__(self, config, control_interval):
        self.control_interval = control_interval
        self.window_size = config['window_size']
        self.window = []
        self.latest = None
        self.aproching_rate = None
        self.squared_error = None
    def data(self, data):
        self.window.append(data)
        if len(self.window) > self.window_size:
            self.window.pop(0)
        if len(self.window) < 2:
            self.latest = data
            self.squared_error = 0
            self.aproching_rate = 0
        else:
            x = range(-len(self.window)+1, 1)
            A = np.vstack([x, np.ones(len(x))]).T
            result = np.linalg.lstsq(A, self.window, rcond=None)
            k, self.latest = result[0]
            self.squared_error = result[1][0] if result[1] else 0
            self.aproching_rate = k / self.control_interval
