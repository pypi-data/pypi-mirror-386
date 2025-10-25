import pandas as pd
import numpy as np
from spicy import stats
from typing import Dict, Union
from .graph import EffectDirection, PerturbationDirection


class MetricsCalculator:
    """Class to calculate various metrics for forecast verification."""

    @staticmethod
    def calculate_mae(actual: pd.Series, forecast: pd.Series) -> float:
        """Calculates Mean Absolute Error (MAE)."""
        return np.mean(np.abs(actual - forecast))

    @staticmethod
    def calculate_rmse(actual: pd.Series, forecast: pd.Series) -> float:
        """Calculates Root Mean Squared Error (RMSE)."""
        return np.sqrt(np.mean((actual - forecast) ** 2))

    @staticmethod
    def calculate_mape(actual: pd.Series, forecast: pd.Series) -> float:
        """Calculates Mean Absolute Percentage Error (MAPE)."""
        return np.mean(np.abs((actual - forecast) / actual)) * 100

    @staticmethod
    def t_statistics(series_old: pd.Series, series_new: pd.Series) -> Dict[str, float]:
        """Calculates t-statistics for two series."""
        if len(series_old) != len(series_new):
            raise ValueError(
                "Both series must have the same length for t-statistics calculation.")
        if series_old.empty or series_new.empty:
            raise ValueError(
                "Both series must not be empty for t-statistics calculation.")
        if not isinstance(series_old, pd.Series) or not isinstance(series_new, pd.Series):
            raise TypeError(
                "Both inputs must be pandas Series for t-statistics calculation.")
        if series_old.isnull().any() or series_new.isnull().any():
            raise ValueError(
                "Both series must not contain NaN values for t-statistics calculation.")
        tstats = stats.ttest_ind(series_old, series_new)
        """Returns a t statistics with 2 series"""
        return {
            "t_statistic": tstats.statistic,
            "p_value": tstats.pvalue
        }

    @staticmethod
    def alignment_score(pred_original: Union[np.ndarray, pd.Series],
                        pred_perturbed: Union[np.ndarray, pd.Series],
                        effect_direction: EffectDirection,
                        perturbation_direction: PerturbationDirection) -> float:

        assert pred_original.shape == pred_perturbed.shape, "Both series have to be the same length"
        expected = perturbation_direction.value * effect_direction.value
        alignment = (expected) * pred_perturbed >= (expected) * pred_original
        alignment_score = alignment.ravel().sum() / pred_original.shape[-1]

        return alignment_score
