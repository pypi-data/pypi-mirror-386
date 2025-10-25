from dataclasses import dataclass, field
from typing import Literal, Optional, Any, Protocol, Union, runtime_checkable
from enum import Enum
import pandas as pd
import numpy as np


class ForecasterType(str, Enum):
    point = "point"
    quantile = "quantile"
    density = "density"
    ensemble = "ensemble"


@dataclass
class AuthorInfo:
    """Author information.

    Attributes:
        name: Name of the author.
        email: Email of the author.
    """

    name: str
    email: Optional[str] = None


@dataclass
class ModelInfo:
    """Model information.

    Attributes:
        name: Name of the model.
        authors: List of authors.
        type: Type of the model.
        params: Parameters of the model.
    """

    name: str
    authors: list[AuthorInfo]
    # type: ForecasterType
    # sk_forecaster_type: Optional[SKForecastType] = None
    params: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Regressor(Protocol):
    def info(self) -> ModelInfo: ...

    def predict(self, dataset: pd.DataFrame) -> pd.Series:
        """
        Predict function.
        Parameters
        ----------
        dataset : pandas dataframe
            test/evaluation dataset for model to make predictions.

        Returns
        -------
        predictions : pandas Series
            Predicted values.

        """
        pass


@runtime_checkable
class Forecaster(Protocol):
    def info(self) -> ModelInfo: ...

    def forecast(self,
                 steps: int,
                 last_window: Union[pd.Series, pd.DataFrame] = None,
                 exog: Union[pd.Series, pd.DataFrame] = None) -> Union[pd.Series, np.ndarray]:
        """
        Predict n steps ahead.
        Rererences: skforecast.base._forecaster_base.py
        Parameters
        ----------
        steps : int
            Number of steps to predict. 
        last_window : pandas Series, pandas DataFrame, default None
            Series values used to create the predictors (lags) needed in the 
            first iteration of the prediction (t + 1).
            If `last_window = None`, the values stored in `self.last_window` are
            used to calculate the initial predictors, and the predictions start
            right after training data.
        exog : pandas Series, pandas DataFrame, default None
            Exogenous variable/s included as predictor/s.

        Returns
        -------
        predictions : pandas Series
            Predicted values.

        """
        pass
