# tests/test_permutation_importance.py

"""
Unit tests for the `PermutationImportanceExplainer` class in the model_explain package.

These tests use pytest and unittest.mock to validate:
- Initialization of the explainer
- Calculation of permutation importance
- Plotting of feature importance

Run with:
    pytest test_permutation_importance.py

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-23
"""

import pytest
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import make_classification
from model_explain.explainers.permutation_importance import (
    PermutationImportanceExplainer,
)
from unittest.mock import patch


@pytest.fixture
def mock_data():
    """
    Generate a mock dataset for testing.

    :return: Features, target, and trained model.
    :rtype: tuple (pd.DataFrame, pd.Series, LogisticRegression)
    """
    X, y = make_classification(n_samples=100, n_features=5, random_state=42)
    X = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(1, 6)])
    y = pd.Series(y)
    model = LogisticRegression()
    model.fit(X, y)
    return X, y, model


def test_initialization(mock_data):
    """
    Test the initialization of the PermutationImportanceExplainer.

    :param mock_data: Fixture providing mock dataset and model.
    :type mock_data: tuple
    """
    X, y, model = mock_data
    explainer = PermutationImportanceExplainer(model, X, y)
    assert explainer.model == model
    assert explainer.X_train.equals(X)
    assert explainer.y_train.equals(y)


def test_calculate_importance(mock_data):
    """
    Test the calculate_importance method of PermutationImportanceExplainer.

    :param mock_data: Fixture providing mock dataset and model.
    :type mock_data: tuple
    """
    X, y, model = mock_data
    explainer = PermutationImportanceExplainer(model, X, y)
    with patch(
        "model_explain.explainers.permutation_importance.permutation_importance"
    ) as mock_perm_importance:
        mock_perm_importance.return_value.importances_mean = np.array(
            [0.2, 0.5, 0.1, 0.05, 0.15]
        )
        mock_perm_importance.return_value.importances_std = np.array(
            [0.05, 0.03, 0.02, 0.01, 0.04]
        )
        mean_importance, std_importance = explainer.calculate_importance()
        assert mean_importance.equals(
            pd.Series([0.2, 0.5, 0.1, 0.05, 0.15], index=X.columns)
        )
        assert std_importance.equals(
            pd.Series([0.05, 0.03, 0.02, 0.01, 0.04], index=X.columns)
        )


def test_calculate_importance_with_scoring(mock_data):
    """
    Test calculate_importance with a different scoring metric.

    :param mock_data: Fixture providing mock dataset and model.
    :type mock_data: tuple
    """
    X, y, model = mock_data
    explainer = PermutationImportanceExplainer(model, X, y)
    with patch(
        "model_explain.explainers.permutation_importance.permutation_importance"
    ) as mock_perm_importance:
        mock_perm_importance.return_value.importances_mean = np.array(
            [0.1, 0.2, 0.3, 0.4, 0.5]
        )
        mock_perm_importance.return_value.importances_std = np.array(
            [0.01, 0.02, 0.03, 0.04, 0.05]
        )
        mean_importance, std_importance = explainer.calculate_importance(scoring="f1")
        assert mean_importance.equals(
            pd.Series([0.1, 0.2, 0.3, 0.4, 0.5], index=X.columns)
        )
        assert std_importance.equals(
            pd.Series([0.01, 0.02, 0.03, 0.04, 0.05], index=X.columns)
        )


def test_plot_importance(mock_data):
    """
    Test the plot_importance method of PermutationImportanceExplainer.

    :param mock_data: Fixture providing mock dataset and model.
    :type mock_data: tuple
    """
    X, y, model = mock_data
    explainer = PermutationImportanceExplainer(model, X, y)
    with patch("matplotlib.pyplot.show") as mock_show:
        with patch(
            "model_explain.explainers.permutation_importance.PermutationImportanceExplainer.calculate_importance"
        ) as mock_calc:
            mock_calc.return_value = (
                pd.Series([0.2, 0.5, 0.1, 0.05, 0.15], index=X.columns),
                pd.Series([0.05, 0.03, 0.02, 0.01, 0.04], index=X.columns),
            )
            explainer.plot_importance()
            mock_show.assert_called_once()


def test_default_scoring(mock_data):
    """
    Test that the default scoring metric is 'accuracy'.

    :param mock_data: Fixture providing mock dataset and model.
    :type mock_data: tuple
    """
    X, y, model = mock_data
    explainer = PermutationImportanceExplainer(model, X, y)
    with patch(
        "model_explain.explainers.permutation_importance.permutation_importance"
    ) as mock_perm_importance:
        mock_perm_importance.return_value.importances_mean = np.zeros(5)
        mock_perm_importance.return_value.importances_std = np.zeros(5)
        explainer.calculate_importance()
        mock_perm_importance.assert_called_with(
            model, X, y, scoring="accuracy", n_repeats=10, random_state=42
        )


def main():
    pytest.main([__file__])
    print("Testing Permutation Importance Explainer")


if __name__ == "__main__":
    main()
