from enum import Enum
from typing import Optional, Union, Tuple
import warnings
from abc import ABCMeta
import pandas as pd
import numpy as np
from .graph import PerturbationDirection


class PerturbationType(Enum):
    """Enum-like class for perturbation functions."""
    ADDITIVE = "additive"
    MULTIPLICATIVE = "multiplicative"
    BINARY = "binary"
    SAMPLE = "sample"


class PerturbationDataset():

    def __init__(self,
                 original_dataset: pd.DataFrame,
                 covariates: list[str],
                 perturbation_direction: PerturbationDirection):
        self._perturbation_dataset = original_dataset.copy()
        self._covariates = covariates
        self._direction = perturbation_direction.value

    def additive_perturb(self, const: float,
                         bound: Optional[Tuple[float, float]] = None
                         ):

        for covar in self._covariates:
            self._perturbation_dataset[covar] = self._perturbation_dataset[covar] + \
                const * self._direction
        if bound is not None:
            min_value = bound[0]
            max_value = bound[1]
            if min_value >= max_value:
                raise ValueError(
                    "Not valid bound, min value has to be smaller than max value")

            # add const within bound, else get closet value of min or max
            for covar in self._covariates:
                self._perturbation_dataset[covar] = self._perturbation_dataset[covar].clip(
                    lower=min_value, upper=max_value)

        return self._perturbation_dataset

    def multipicative_perturb(self, const: float,
                              bound: Optional[Tuple[float, float]] = None):

        for covar in self._covariates:
            self._perturbation_dataset[covar] = self._perturbation_dataset[covar] * \
                (1 + const * self._direction)

        if bound is not None:
            min_value = bound[0]
            max_value = bound[1]
            if min_value >= max_value:
                raise ValueError(
                    "Not valid bound, min value has to be smaller than max value")

            # add const within bound, else get closet value of min or max
            for covar in self._covariates:
                self._perturbation_dataset[covar] = self._perturbation_dataset[covar].clip(
                    lower=min_value, upper=max_value)

        return self._perturbation_dataset

    def binary_perturb(self):
        self._perturbation_dataset_binary_list = []
        if not self._direction == 0:
            raise ValueError(
                'User has to specified Perubation Direction to be binary')
        for covar in self._covariates:
            unique_values = self._perturbation_dataset[covar].unique().tolist()
            if len(unique_values) > 2:
                warnings.warn(
                    f"Categorical covariates provided, number of unique values: {len(unique_values)}")
            for value in unique_values:
                self._perturbation_dataset_binary = self._perturbation_dataset.copy()
                self._perturbation_dataset_binary[covar] = value
                self._perturbation_dataset_binary_list.append(
                    self._perturbation_dataset_binary)
        return self._perturbation_dataset_binary_list

    def add_gaussian_noise(self, mu: float, sigma: float, bound: Tuple[float, float] = None):
        for covar in self._covariates:
            self._perturbation_dataset[covar] = self._perturbation_dataset[covar].apply(
                lambda x: x + abs(np.random.normal(mu, sigma)) * self._direction)
        if bound is not None:
            min_value = bound[0]
            max_value = bound[1]
            if min_value >= max_value:
                raise ValueError(
                    "Not valid bound, min value has to be smaller than max value")
            for covar in self._covariates:
                self._perturbation_dataset[covar] = self._perturbation_dataset[covar].clip(
                    lower=min_value, upper=max_value)
        return self._perturbation_dataset
