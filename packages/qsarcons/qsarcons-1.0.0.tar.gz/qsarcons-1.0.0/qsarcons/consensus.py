import random
from typing import List, Union, Optional

import numpy as np
import pandas as pd
from pandas import DataFrame, Series, Index

from sklearn.metrics import (
    mean_absolute_error, r2_score, root_mean_squared_error,
    accuracy_score, f1_score, precision_score, recall_score, balanced_accuracy_score, roc_auc_score,
)

from scipy.stats import spearmanr

from .genopt import Individual, GeneticAlgorithm


METRIC_MODES = {
    "mae": "minimize",
    "rmse": "minimize",
    "r2": "maximize",
    "rank": "maximize",
    "top": "maximize",
    "acc": "maximize",
    "f1": "maximize",
    "auto": "maximize",
}

def top_x_overlap_rate(y_true, y_pred, top_percent=0.1):
    """Calculate the overlap rate between top-ranked true and predicted values.

    Args:
        y_true (array-like): Ground truth target values.
        y_pred (array-like): Predicted target values.
        top_percent (float, optional): Fraction of top elements to consider for overlap. Defaults to 0.1.

    Returns:
        float: Fraction of overlapping indices between top-ranked true and predicted values.

    Raises:
        ValueError: If `top_percent` is too small for the dataset size.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    n_top = int(len(y_true) * top_percent)
    if n_top < 1:
        raise ValueError("Top percent too small for dataset size.")
    top_true_idx = set(np.argsort(y_true)[-n_top:])
    top_pred_idx = set(np.argsort(y_pred)[-n_top:])
    return len(top_true_idx & top_pred_idx) / n_top

def calc_accuracy(y_true, y_pred, metric='mae'):
    """Compute performance metrics for regression or classification tasks.

    Args:
        y_true (array-like): Ground truth target values.
        y_pred (array-like): Predicted target values.
        metric (str, optional): Metric name ('mae', 'r2', 'rmse', 'rank', 'top', 'acc', 'f1', or 'auto').

    Returns:
        float: Computed metric score.
    """
    y_true, y_pred = list(y_true), list(y_pred)

    if metric == 'mae':
        return mean_absolute_error(y_true, y_pred)
    elif metric == 'r2':
        return r2_score(y_true, y_pred)
    elif metric == 'rmse':
        return root_mean_squared_error(y_true, y_pred)
    elif metric == 'rank':
        acc, _ = spearmanr(y_true, y_pred)
        return acc.item() if hasattr(acc, 'item') else acc
    elif metric == 'top':
        return top_x_overlap_rate(y_true, y_pred)
    elif metric == 'acc':
        return accuracy_score(y_true, y_pred)
    elif metric == 'f1':
        return f1_score(y_true, y_pred, average='weighted')
    elif metric == 'auto':
        if all(isinstance(v, (int, float)) for v in y_true):
            mae = mean_absolute_error(y_true, y_pred)
            rmse = root_mean_squared_error(y_true, y_pred)
            r2_val = r2_score(y_true, y_pred)
            mae_score = 1 / (1 + mae)
            rmse_score = 1 / (1 + rmse)
            r2_score_norm = max(0.0, r2_val)
            return np.mean([mae_score, rmse_score, r2_score_norm])
        else:
            acc = accuracy_score(y_true, y_pred)
            bal_acc = balanced_accuracy_score(y_true, y_pred)
            f1 = f1_score(y_true, y_pred, average='weighted')
            precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_true, y_pred, average='weighted', zero_division=0)
            roc_auc = roc_auc_score(y_true, y_pred)
            return np.mean([acc, bal_acc, f1, precision, recall, roc_auc])

class ConsensusSearch:
    """Base class for consensus model selection.

    Handles model filtering, consensus formation, and metric optimization across regression and classification tasks.

    Args:
        cons_size (Union[int, str], optional): Number of models to include in consensus or 'auto' for automatic selection.
        cons_size_candidates (List[int], optional): List of candidate consensus sizes for auto mode.
        metric (str, optional): Evaluation metric to optimize.
    """
    def __init__(self, cons_size: Union[int, str] = 9, cons_size_candidates: Optional[List[int]] = None, metric: str = "mae"):
        self.cons_size = cons_size
        self.metric = metric
        self.cons_size_candidates = cons_size_candidates or [3, 5, 7, 9, 11, 13, 15, 17, 20, 25]
        self.n_filtered_models = None

    def _default_metric(self) -> str:
        """Return the default metric used for consensus evaluation."""
        return self.metric

    def _get_baseline_prediction(self, y: Series) -> Series:
        """Generate baseline predictions for the given target values."""
        raise NotImplementedError

    def _consensus_predict(self, x_subset: DataFrame) -> Series:
        """Generate consensus predictions for the provided subset of models."""
        raise NotImplementedError

    def _filter_models(self, x: DataFrame, y: Series) -> DataFrame:
        """Filter out underperforming models based on baseline metric performance.

        Args:
            x (pd.DataFrame): Model prediction matrix (columns = models, rows = samples).
            y (pd.Series): True target values.

        Returns:
            pd.DataFrame: Filtered subset of models with better-than-baseline performance.
        """
        metric = "r2" if isinstance(self, ConsensusSearchRegressor) else "acc"

        mode = METRIC_MODES[metric]
        baseline_pred = self._get_baseline_prediction(y)
        baseline_score = calc_accuracy(y, baseline_pred, metric=metric)

        filtered_cols = [col for col in x.columns if
                         (mode == 'maximize' and calc_accuracy(y, x[col], metric=metric) > baseline_score) or
                         (mode == 'minimize' and calc_accuracy(y, x[col], metric=metric) < baseline_score)]

        filtered = x[filtered_cols]
        self.n_filtered_models = filtered.shape[1]
        if self.n_filtered_models == 0:
            print("No models left after filtering. All models selected.")
            return x
        return filtered

    def run(self, x: DataFrame, y: Series) -> Index:
        """Execute consensus model search.

        Args:
            x (pd.DataFrame): DataFrame of model predictions.
            y (pd.Series): True target values.

        Returns:
            pd.Index: Selected model indices for consensus.
        """
        x_filtered = self._filter_models(x, y)
        if len(x_filtered.columns) < max(self.cons_size_candidates):
            print("WARNING: The number of filtered models is lower than the consensus size candidates. All models are used for consensus search.")
            x_filtered = x

        if isinstance(self.cons_size, int):
            return self._run_with_cons_size(x_filtered, y, self.cons_size)

        elif self.cons_size == 'auto':
            best_cons = None
            best_score = None
            mode = METRIC_MODES[self.metric]
            for size in self.cons_size_candidates:
                candidate = self._run_with_cons_size(x_filtered, y, size)
                y_pred = self._consensus_predict(x_filtered[candidate])
                score = calc_accuracy(y, y_pred, self.metric)
                if best_score is None or \
                   (mode == 'maximize' and score > best_score) or \
                   (mode == 'minimize' and score < best_score):
                    best_score = score
                    best_cons = candidate
            return best_cons
        else:
            raise ValueError(f"Unsupported cons_size value: {self.cons_size}")

class ConsensusSearchRegressor(ConsensusSearch):
    """Consensus search strategy for regression models.

    Uses mean predictions across selected models for consensus evaluation.
    """
    def _get_baseline_prediction(self, y: Series) -> Series:
        return pd.Series(np.full_like(y, fill_value=y.mean(), dtype=np.float64), index=y.index)

    def _consensus_predict(self, x_subset: DataFrame) -> Series:
        return x_subset.mean(axis=1)

class ConsensusSearchClassifier(ConsensusSearch):
    """Consensus search strategy for classification models.

    Uses majority voting across model predictions to determine final class labels.
    """
    def _get_baseline_prediction(self, y: Series) -> Series:
        return pd.Series([y.mode()[0]] * len(y), index=y.index)

    def _majority_vote(self, preds: pd.DataFrame) -> pd.Series:
        """Perform majority voting across model predictions.

        Args:
            preds (pd.DataFrame): Predictions from multiple models.

        Returns:
            pd.Series: Final class predictions after voting.
        """
        arr = preds.to_numpy()
        classes = np.unique(arr)
        counts = (arr[:, :, None] == classes).sum(axis=1)
        max_counts = counts.max(axis=1, keepdims=True)
        mask = counts == max_counts
        indices = np.argmax(mask, axis=1)
        modes = classes[indices]
        return pd.Series(modes, index=preds.index)

    def _consensus_predict(self, x_subset: DataFrame) -> Series:
        return self._majority_vote(x_subset)

class DefaultConsensusRegressor(ConsensusSearchRegressor):
    """Default regressor consensus using predefined model names.

    Args:
        model_names (List[str]): List of model names included in the consensus.
    """
    def __init__(self, model_names: List[str]):
        super().__init__(cons_size=len(model_names))
        self.model_names = model_names

    def run(self, x: DataFrame, y: Series) -> Index:
        """Select predefined models as the consensus set."""
        selected = self.model_names
        return pd.Index(selected)

class RandomSearchRegressor(ConsensusSearchRegressor):
    """Randomized search for optimal regression consensus.

    Args:
        cons_size (int, optional): Number of models in consensus.
        n_iter (int, optional): Number of random combinations to evaluate.
        metric (str, optional): Evaluation metric.
        cons_size_candidates (List[int], optional): Consensus size options for auto mode.
    """
    def __init__(self, cons_size=10, n_iter=5000, metric="mae", cons_size_candidates=None):
        super().__init__(cons_size, cons_size_candidates, metric)
        self.n_iter = n_iter

    def _run_with_cons_size(self, x: DataFrame, y: Series, cons_size: int) -> Index:
        """Run random search for a fixed consensus size."""
        results = []
        for _ in range(self.n_iter):
            cols = random.sample(list(x.columns), cons_size)
            y_pred = self._consensus_predict(x[cols])
            score = calc_accuracy(y, y_pred, self.metric)
            results.append((cols, score))
        results.sort(key=lambda tup: tup[1], reverse=METRIC_MODES[self.metric] == 'maximize')
        return pd.Index(results[0][0])

class DefaultConsensusClassifier(ConsensusSearchClassifier):
    """Default classifier consensus using predefined model names.

    Args:
        model_names (List[str]): List of model names included in the consensus.
    """
    def __init__(self, model_names: List[str]):
        super().__init__(cons_size=len(model_names))
        self.model_names = model_names

    def run(self, x: DataFrame, y: Series) -> Index:
        """Select predefined models as the consensus set."""
        selected = self.model_names
        return pd.Index(selected)

class RandomSearchClassifier(ConsensusSearchClassifier):
    """Randomized search for optimal classification consensus.

    Args:
        cons_size (int, optional): Number of models in consensus.
        n_iter (int, optional): Number of random combinations to evaluate.
        metric (str, optional): Evaluation metric.
        cons_size_candidates (List[int], optional): Consensus size options for auto mode.
    """
    def __init__(self, cons_size=10, n_iter=1000, metric="acc", cons_size_candidates=None):
        super().__init__(cons_size, cons_size_candidates, metric)
        self.n_iter = n_iter

    def _run_with_cons_size(self, x: DataFrame, y: Series, cons_size: int) -> Index:
        """Run random search for a fixed consensus size."""
        results = []
        for _ in range(self.n_iter):
            cols = random.sample(list(x.columns), cons_size)
            y_pred = self._consensus_predict(x[cols])
            score = calc_accuracy(y, y_pred, self.metric)
            results.append((cols, score))
        results.sort(key=lambda tup: tup[1], reverse=METRIC_MODES[self.metric] == 'maximize')
        return pd.Index(results[0][0])

class SystematicSearchRegressor(ConsensusSearchRegressor):
    """Systematic selection of top-performing regression models.

    Selects models with the best individual metric scores for consensus formation.
    """
    def _run_with_cons_size(self, x: DataFrame, y: Series, cons_size: int) -> Index:
        """Run systematic search for regression models."""
        scores = [(col, calc_accuracy(y, x[col], self.metric)) for col in x.columns]
        scores.sort(key=lambda tup: tup[1], reverse=METRIC_MODES[self.metric] == 'maximize')
        top_cols = [col for col, _ in scores[:cons_size]]
        return pd.Index(top_cols)

class SystematicSearchClassifier(ConsensusSearchClassifier):
    """Systematic selection of top-performing classification models.

    Selects models with the best accuracy or F1 score for consensus formation.
    """
    def _run_with_cons_size(self, x: DataFrame, y: Series, cons_size: int) -> Index:
        """Run systematic search for classification models."""
        scores = [(col, calc_accuracy(y, x[col], self.metric)) for col in x.columns]
        scores.sort(key=lambda tup: tup[1], reverse=METRIC_MODES[self.metric] == 'maximize')
        top_cols = [col for col, _ in scores[:cons_size]]
        return pd.Index(top_cols)

class GeneticSearchRegressor(ConsensusSearchRegressor):
    """Genetic algorithm-based search for optimal regression consensus.

    Args:
        cons_size (int, optional): Number of models in consensus.
        n_iter (int, optional): Number of genetic algorithm iterations.
        pop_size (int, optional): Population size.
        mut_prob (float, optional): Mutation probability.
        metric (str, optional): Evaluation metric.
        cons_size_candidates (List[int], optional): Consensus size options for auto mode.
    """
    def __init__(self, cons_size=10, n_iter=200, pop_size=50, mut_prob=0.2, metric="mae", cons_size_candidates=None):
        super().__init__(cons_size, cons_size_candidates, metric)
        self.pop_size = pop_size
        self.n_iter = n_iter
        self.mut_prob = mut_prob

    def _run_with_cons_size(self, x: DataFrame, y: Series, cons_size: int) -> Index:
        """Run genetic algorithm search for a fixed consensus size."""
        def objective(ind: Individual) -> float:
            y_pred = self._consensus_predict(x.iloc[:, list(ind)])
            return calc_accuracy(y, y_pred, self.metric)

        space = range(len(x.columns))
        task = METRIC_MODES[self.metric]

        ga = GeneticAlgorithm(task=task, pop_size=self.pop_size, crossover_prob=0.95,
                              mutation_prob=self.mut_prob, elitism=True, random_seed=11)
        ga.set_fitness(objective)
        ga.initialize(space, ind_size=cons_size)
        ga.run(n_iter=self.n_iter, verbose=False)
        return x.columns[list(ga.get_global_best())]

class GeneticSearchClassifier(ConsensusSearchClassifier):
    """Genetic algorithm-based search for optimal classification consensus.

    Args:
        cons_size (int, optional): Number of models in consensus.
        n_iter (int, optional): Number of genetic algorithm iterations.
        pop_size (int, optional): Population size.
        mut_prob (float, optional): Mutation probability.
        metric (str, optional): Evaluation metric.
        cons_size_candidates (List[int], optional): Consensus size options for auto mode.
    """
    def __init__(self, cons_size=10, n_iter=200, pop_size=50, mut_prob=0.2, metric="acc", cons_size_candidates=None):
        super().__init__(cons_size, cons_size_candidates, metric)
        self.pop_size = pop_size
        self.n_iter = n_iter
        self.mut_prob = mut_prob

    def _run_with_cons_size(self, x: DataFrame, y: Series, cons_size: int) -> Index:
        """Run genetic algorithm search for a fixed consensus size."""
        def objective(ind: Individual) -> float:
            y_pred = self._consensus_predict(x.iloc[:, list(ind)])
            return calc_accuracy(y, y_pred, self.metric)

        space = range(len(x.columns))
        task = METRIC_MODES[self.metric]

        ga = GeneticAlgorithm(task=task, pop_size=self.pop_size, crossover_prob=0.95,
                              mutation_prob=self.mut_prob, elitism=True, random_seed=11)
        ga.set_fitness(objective)
        ga.initialize(space, ind_size=cons_size)
        ga.run(n_iter=self.n_iter, verbose=False)
        return x.columns[list(ga.get_global_best())]
