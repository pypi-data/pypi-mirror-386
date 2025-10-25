from typing import List, Optional, Union
import pandas as pd
from .model import Forecaster, Regressor
from .graph import EffectDirection, PerturbationDirection
from .metrics import MetricsCalculator
import graphviz as gr


class Verifier:
    """Class to verify the causal effect given trained models and datasets."""

    def __init__(self,
                 model: Union[Forecaster, Regressor],
                 original_dataset: pd.DataFrame,
                 perturbed_dataset: pd.DataFrame,
                 covariates: List[str],
                 perturbation_direction: PerturbationDirection,
                 effect_direction: EffectDirection,
                 scaled: bool = True):
        """
        Args:
            model: Model class
            original_dataset (pd.DataFrame): Original dataset
            perturbed_dataset (pd.DataFrame): Dataset having covariate(s) perturbed
            covariates (List[str]): Name(s) of specified covariate(s)
            perturbation_direction (PerturbationDirection): Direction of perturbation process (increasing or decreasing)
            effect_direction (EffectType): Relationship between covariate(s) and target forecast (positive or negative)

        """
        self.model = model
        self.original_dataset = original_dataset
        self.perturbed_dataset = perturbed_dataset
        self.covariates = covariates
        self.perturbation_direction = perturbation_direction
        self.effect_direction = effect_direction
        self.scaled = scaled

        # Check if original and perturbed datasets have the same shape
        assert self.original_dataset.shape == self.perturbed_dataset.shape, "Both datasets should have same shape"

    def assumption_plot(self, render: bool = False):
        # visualize covariate causal graph using pygraphviz
        g = gr.Digraph()
        g.node("Target", shape="box")
        for covar in self.covariates:
            g.node(covar)
            g.edge(covar, "Target", label=self.effect_direction.name)
        if render:
            g.render("covariate_causal_graph", format="png", cleanup=True)
        return g

    def procedure_plot(self, render: bool = False):
        g = gr.Digraph()
        g.node("Original Dataset", shape="box")
        g.node("Perturbed Dataset", shape="box")
        g.node("Model", shape="box")
        g.node("Predictions", shape="box")
        g.node("Predictions Perturbed", shape="box")
        g.node("Violation score", shape="box")
        g.edge("Original Dataset", "Perturbed Dataset",
               label=str(self.perturbation_direction))
        g.edge("Original Dataset", "Model")
        g.edge("Perturbed Dataset", "Model")
        g.edge("Model", "Predictions")
        g.edge("Model", "Predictions Perturbed")
        g.edge("Predictions", "Violation score")
        g.edge("Predictions Perturbed", "Violation score")

        if render:
            g.render("procedure_graph", format="png", cleanup=True)
        return g

    def _check_covariate_direction_violation(self):

        # check original_dataset == perturbed_dataset except for covariate column
        if not self.original_dataset.drop(columns=self.covariates).\
                equals(self.perturbed_dataset.drop(columns=self.covariates)):
            return True
        # and check if covariate is perturbed in the specified direction
        if self.perturbation_direction == PerturbationDirection.increasing:
            return (self.original_dataset[self.covariates] > self.perturbed_dataset[self.covariates]).any().sum()
        elif self.perturbation_direction == PerturbationDirection.decreasing:
            return (self.original_dataset[self.covariates] < self.perturbed_dataset[self.covariates]).any().sum()
        return True

    def __call__(self) -> dict:
        if not self.scaled and self._check_covariate_direction_violation():
            raise ValueError("Covariate direction check failed.")
        predictions = self.model.forecast(self.original_dataset) if isinstance(
            self.model, Forecaster) else self.model.predict(self.original_dataset)
        predictions_perturbed = self.model.forecast(self.perturbed_dataset) if isinstance(
            self.model, Forecaster) else self.model.predict(self.perturbed_dataset)

        alignment_score = MetricsCalculator.alignment_score(predictions,
                                                            predictions_perturbed,
                                                            perturbation_direction=self.perturbation_direction,
                                                            effect_direction=self.effect_direction)

        result = {
            "assumption": f"{self.covariates} → target",
            "relationship": f"{self.effect_direction}",
            "perturbation_direction": self.perturbation_direction,
            "alignment_score": alignment_score,
            "target_length": predictions.shape[-1]
        }
        return result
