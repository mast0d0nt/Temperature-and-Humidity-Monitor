from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import numpy as np


class LinearRegressionHandler:
    def __init__(self):
        self._is_loaded = False
        self._min_samples = 50

    def load(self, measurements: list[dict]):
        X, y = [], []
        for measurement in measurements:
            measurement_temperature = measurement.get("temperature")
            measurement_humidity = measurement.get("humidity")
            
            if measurement_temperature is None or measurement_humidity is None:
                continue

            X.append([measurement_temperature])
            y.append(measurement_humidity)

        if len(X) < self._min_samples:
            raise ValueError(f"Amount of {self._min_samples} samples (minimal) is required (computed: {len(X)}, needed {self._min_samples - len(X)} more)! Try again with more data.")

        self._X = np.array(X)
        self._y = np.array(y)
        self._is_loaded = True

        return (self._X, self._y)