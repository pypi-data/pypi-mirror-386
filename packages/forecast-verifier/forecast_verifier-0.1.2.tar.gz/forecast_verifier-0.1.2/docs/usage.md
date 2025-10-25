# Quickstart

## Installation
Install the latest forecast-verifier version from PyPi using `pip`:

`pip install forecast-verifier`

Note: Different examples can be found via `notebooks/` folder.

## Regression example
```python
import pandas as pd
from forecast_verifier.verifier import Verifier
from forecast_verifier.model import Regressor
from forecast_verifier.dataset import PerturbationDataset
from forecast_verifier.graph import PerturbationDirection, EffectDirection

# Create model class inheriting from Regressor that implements the predict method
class CustomRegressor(Regressor):
    def __init__(self, model):
        self.model = model
    
    def predict(self, dataset):
        """
        Generate predictions using given dataset.

        Args:
            dataset (pd.DataFrame): Input data for prediction.

        Returns:
            np.ndarray: Predicted values.
        """
        return self.model.predict(dataset)

my_model = CustomRegressor(model)  # model is a pre-trained regression model

# Load your dataset
original_data = pd.read_csv('your_dataset.csv')
pertubation_data = pd.read_csv('your_pertubation_dataset.csv')

verifier = Verifier(my_model, 
                    original_dataset, 
                    perturbation_dataset, 
                    ['variable1'], 
                    PerturbationDirection.decreasing, 
                    EffectDirection.positive)
print(verifier())

```

## Forecast example
``` python
import pandas as pd
from forecast_verifier.verifier import Verifier
from forecast_verifier.model import Forecaster
from forecast_verifier.dataset import PerturbationDataset
from forecast_verifier.graph import PerturbationDirection, EffectDirection
from forecast_verifier.utils import load_model

class CustomForecaster(Forecaster):
    
    # exmple of loading a model from path
    def __init__(self, model_path: str):        
        
        self.model = load_model(model_path=model_path)

    def forecast(self, dataset: pd.DataFrame) -> np.ndarray:
        """
        Generate forecasts using given dataset.

        Args:
            dataset (pd.DataFrame): Input data for forecasting.

        Returns:
            np.ndarray: Forecasted values.
        """
        
        # Implement your forecasting logic here
        pass

my_model = CustomForecaster(model_path='path_to_your_model')

# Load your dataset
original_data = pd.read_csv('your_dataset.csv')
pertubation_data = pd.read_csv('your_pertubation_dataset.csv')  

verifier = Verifier(my_model, 
                    original_dataset, 
                    perturbation_dataset, 
                    ['variable1'], 
                    PerturbationDirection.decreasing, 
                    EffectDirection.positive)
print(verifier())
```


