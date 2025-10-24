# tests/test_integrated_gradients.py

"""
Unit tests for the `IntegratedGradientsExplainer` class in the model_explain package.

Tests:
- Initialization
- Integrated Gradients computation for classification
- Attribution plotting

Run with:
    pytest tests/test_integrated_gradients.py

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-23
"""

import pytest
from unittest.mock import MagicMock, patch
import torch
from model_explain.explainers.integrated_gradients import IntegratedGradientsExplainer


@pytest.fixture
def mock_model_and_inputs():
    """
    Provides a mock classification model, baseline, and input tensor.

    :return: Mock model, baseline tensor, and input tensor.
    :rtype: tuple (torch.nn.Module, torch.Tensor, torch.Tensor)
    """

    # Dummy model: returns logits for 3 classes
    class DummyModel(torch.nn.Module):
        def forward(self, x):
            # x: (batch, channels, height, width)
            batch = x.shape[0]
            return torch.ones(batch, 3)

    model = DummyModel()
    baseline = torch.zeros(1, 1, 8, 8)
    input_tensor = torch.ones(1, 1, 8, 8)
    return model, baseline, input_tensor


def test_initialization(mock_model_and_inputs):
    """
    Test initialization of IntegratedGradientsExplainer.

    :param mock_model_and_inputs: Fixture providing mock model and inputs.
    :type mock_model_and_inputs: tuple
    """
    model, baseline, input_tensor = mock_model_and_inputs
    explainer = IntegratedGradientsExplainer(
        model, baseline, input_tensor, target_class=1
    )
    assert explainer.model is model
    assert torch.equal(explainer.baseline, baseline)
    assert torch.equal(explainer.input_tensor, input_tensor)
    assert explainer.target_class == 1


def test_compute_integrated_gradients(mock_model_and_inputs):
    """
    Test computation of Integrated Gradients for classification.

    :param mock_model_and_inputs: Fixture providing mock model and inputs.
    :type mock_model_and_inputs: tuple
    """
    model, baseline, input_tensor = mock_model_and_inputs
    explainer = IntegratedGradientsExplainer(
        model, baseline, input_tensor, target_class=2
    )
    # Patch backward to avoid actual gradient computation
    with patch.object(torch.Tensor, "backward", return_value=None):
        # Manually set grad to a tensor of ones
        def fake_forward(x):
            x.grad = torch.ones_like(x)
            return torch.ones(x.shape[0], 3)

        explainer.model.forward = fake_forward
        attributions = explainer.compute_integrated_gradients(steps=5)
        assert isinstance(attributions, torch.Tensor)
        assert attributions.shape == input_tensor.shape


def test_plot_attributions(mock_model_and_inputs):
    """
    Test plotting of Integrated Gradients attributions for classification.

    :param mock_model_and_inputs: Fixture providing mock model and inputs.
    :type mock_model_and_inputs: tuple
    """
    model, baseline, input_tensor = mock_model_and_inputs
    explainer = IntegratedGradientsExplainer(
        model, baseline, input_tensor, target_class=0
    )
    with patch("matplotlib.pyplot.show") as mock_show, patch.object(
        IntegratedGradientsExplainer,
        "compute_integrated_gradients",
        return_value=torch.ones(1, 1, 8, 8),
    ):
        explainer.plot_attributions()
        mock_show.assert_called_once()


def main():
    pytest.main([__file__])


if __name__ == "__main__":
    main()
