from src.utilities.database_manager import DatabaseManager
from src.ml.linear_regression import LinearRegressionHandler

with DatabaseManager() as database_manager:
    measurements = database_manager.read()

linear_regression_handler = LinearRegressionHandler()
data = linear_regression_handler.load(measurements)
X = data[0]
y = data[1]
print(X, y, X.shape, y.shape, sep="\n")