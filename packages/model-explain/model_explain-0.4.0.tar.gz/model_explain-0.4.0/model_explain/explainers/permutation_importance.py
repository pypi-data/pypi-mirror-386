# model_explain/explainers/permutation_importance.py

"""
This module provides an explainer for calculating and visualizing permutation feature importance for classification models.

It uses the permutation importance method to assess the importance of each feature by measuring the increase in the
model's prediction error after permuting the feature's values.

Features:
- Calculate permutation importance for features in classification tasks.
- Visualize feature importance using bar plots.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-23
"""

from typing import Tuple

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.inspection import permutation_importance


class PermutationImportanceExplainer:
    """
    Explainer for calculating and visualizing permutation feature importance for classification models.
    Uses the permutation importance method to assess the importance of each feature by measuring the increase in the
    model's prediction error after permuting the feature's values.

    Attributes:
        model (ClassifierMixin): Trained classification model.
        X_train (pd.DataFrame): Training features.
        y_train (pd.Series): Training target values.
    """

    def __init__(self, model, X_train, y_train):
        """
        Initialize the PermutationImportanceExplainer for classification.

        :param model: Classification model (e.g., sklearn.linear_model.LogisticRegression).
        :type model: ClassifierMixin
        :param X_train: Training features as a pandas DataFrame.
        :type X_train: pd.DataFrame
        :param y_train: Training target values as a pandas Series.
        :type y_train: pd.Series
        """
        self.model = model
        self.X_train = X_train
        self.y_train = y_train

    def calculate_importance(self, scoring="accuracy", n_repeats=10, random_state=42):
        """
        Calculate permutation importance for all features in a classification model.

        :param scoring: Metric used to evaluate model performance ('accuracy', 'f1', 'roc_auc', etc.).
        :type scoring: str
        :param n_repeats: Number of times to permute a feature.
        :type n_repeats: int
        :param random_state: Random seed for reproducibility.
        :type random_state: int
        :return: Mean and standard deviation of permutation importance for each feature.
        :rtype: Tuple[pd.Series, pd.Series]
        """
        result = permutation_importance(
            self.model,
            self.X_train,
            self.y_train,
            scoring=scoring,
            n_repeats=n_repeats,
            random_state=random_state,
        )
        importances_mean = pd.Series(
            result.importances_mean, index=self.X_train.columns
        )
        importances_std = pd.Series(result.importances_std, index=self.X_train.columns)
        return importances_mean, importances_std

    def plot_importance(self, scoring="accuracy", n_repeats=10, random_state=42):
        """
        Plot the feature importance for a classification model.

        :param scoring: Metric used to evaluate model performance ('accuracy', 'f1', 'roc_auc', etc.).
        :type scoring: str
        :param n_repeats: Number of times to permute a feature.
        :type n_repeats: int
        :param random_state: Random seed for reproducibility.
        :type random_state: int
        """
        importances, importances_std = self.calculate_importance(
            scoring=scoring, n_repeats=n_repeats, random_state=random_state
        )

        plt.figure(figsize=(10, 6))
        plt.barh(importances.index, importances.values, xerr=importances_std.values)
        plt.xlabel("Permutation Importance")
        plt.title(f"Feature Importance ({scoring})")
        plt.tight_layout()
        plt.show()
