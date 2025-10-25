# Forecast Verifier

Forecast verifier is Python package for verifying specified causal relationships between forecasts/predictions and covariates given trained models. The package goes one step beyond simple model explainability tools to extract learnt causal relationships, and verify them against existing domain knowledge.

Documentation can be found at: [Homepage](https://maichi-bui.github.io/forecast-verifier) 

## Installation
Install the forecast_verifier package using `pip` command:

```bash
pip install forecast-verifier
```

## Usage example
```python
import pandas as pd
from forecast_verifier.model import Forecaster, Regressor
from forecast_verifier.dataset import PerturbationDataset
from forecast_verifier.verifier import Verifier
from forecast_verifier.graph import PerturbationDirection, EffectDirection

# Create your model inheriting from Forecaster or Regressor that implements the forecast/predict method
class CustomForecaster(Forecaster):
    def __init__(self):
        super().__init__()
        # Initialize your model here    
    def forecast(self, dataset):
        # Implement your forecasting logic here
        pass

my_model = CustomForecaster()

# Load your dataset
original_data = pd.read_csv('your_dataset.csv')
pertubation_data = pd.read_csv('your_pertubation_dataset.csv')

# if pertubation_data are not available, create a PerturbationDataset based on original_data
perturbation_data = PerturbationDataset(original_dataset=original_data, 
                                        covariates=['covariate1'], 
                                        perturbation_direction=PerturbationDirection.increasing)
# increase covariate1 by 20% with bounds (-10, 40)
perturbation_data = perturbation_data.multipicative_perturb(0.2, bound=(-10, 40))
# increase covariate1 by 10 units with bounds (-10, 40)
perturbation_data = perturbation_data.additive_perturb(10, bound=(-10, 40))

# Define and verify causal relationships
## when covariate1 increases, the forecast should decrease, i.e., negative effect
## perturbation direction is increasing, meaning that we increase covariate1 from original_data to pertubation_data
verifier = Verifier(model=my_model, 
                    original_dataset=original_data, 
                    perturbed_dataset=pertubation_data, 
                    covariates=['covariate1'],                     
                    effect_direction=EffectDirection.negative,
                    perturbation_direction=PerturbationDirection.increasing)

print(verifier())
```
Check out other examples in examples/ folder
