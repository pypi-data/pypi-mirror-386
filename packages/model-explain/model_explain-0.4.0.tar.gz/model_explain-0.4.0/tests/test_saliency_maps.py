# tests/test_saliency_maps.py

"""
Unit tests for the `SaliencyMapsExplainer` class in the model_explain package.

Tests:
- Initialization
- Saliency map generation for classification
- Plotting of saliency map

Run with:
    pytest test_saliency_maps.py

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-23
"""

import pytest
import torch
from torch import nn
from unittest.mock import patch, MagicMock
from model_explain.explainers.saliency_maps import SaliencyMapsExplainer


@pytest.fixture
def mock_model_and_input():
    """
    Provides a mock classification model and input tensor.

    :return: Mock model and input tensor.
    :rtype: tuple (nn.Module, torch.Tensor)
    """

    class DummyModel(nn.Module):
        def forward(self, x):
            # Simulate batch size 1, 3 classes
            return torch.tensor([[0.1, 0.5, 0.4]], requires_grad=True)

    model = DummyModel()
    # Shape: (1, 3, 8, 8) for batch, channels, height, width
    input_tensor = torch.randn(1, 3, 8, 8, requires_grad=True)
    return model, input_tensor


def test_initialization(mock_model_and_input):
    """
    Test initialization of SaliencyMapsExplainer.

    :param mock_model_and_input: Fixture providing mock model and input tensor.
    :type mock_model_and_input: tuple
    """
    model, input_tensor = mock_model_and_input
    explainer = SaliencyMapsExplainer(model, input_tensor, target_class=1)
    assert explainer.model is model
    assert torch.equal(explainer.input_tensor, input_tensor)
    assert explainer.target_class == 1


def test_generate_saliency_map(mock_model_and_input):
    """
    Test saliency map generation for classification.

    :param mock_model_and_input: Fixture providing mock model and input tensor.
    :type mock_model_and_input: tuple
    """
    model, input_tensor = mock_model_and_input
    explainer = SaliencyMapsExplainer(model, input_tensor)
    # Patch backward and set a fake grad tensor
    with patch.object(torch.Tensor, "backward", return_value=None):
        # Manually set grad to a tensor of the correct shape
        fake_grad = torch.ones_like(input_tensor)
        input_tensor.grad = fake_grad
        saliency = explainer.generate_saliency_map()
        assert isinstance(saliency, torch.Tensor)
        assert saliency.shape == (1, 8, 8)


def test_generate_saliency_map_with_target_class(mock_model_and_input):
    """
    Test saliency map generation for a specific target class.

    :param mock_model_and_input: Fixture providing mock model and input tensor.
    :type mock_model_and_input: tuple
    """
    model, input_tensor = mock_model_and_input
    explainer = SaliencyMapsExplainer(model, input_tensor, target_class=2)
    with patch.object(torch.Tensor, "backward", return_value=None):
        fake_grad = torch.ones_like(input_tensor)
        input_tensor.grad = fake_grad
        saliency = explainer.generate_saliency_map()
        assert isinstance(saliency, torch.Tensor)
        assert saliency.shape == (1, 8, 8)


def test_plot_saliency_map(mock_model_and_input):
    """
    Test plotting of the saliency map.

    :param mock_model_and_input: Fixture providing mock model and input tensor.
    :type mock_model_and_input: tuple
    """
    model, input_tensor = mock_model_and_input
    explainer = SaliencyMapsExplainer(model, input_tensor)
    with patch.object(
        SaliencyMapsExplainer, "generate_saliency_map", return_value=torch.ones(1, 8, 8)
    ):
        with patch("matplotlib.pyplot.show") as mock_show:
            explainer.plot_saliency_map()
            mock_show.assert_called_once()


def main():
    pytest.main([__file__])


if __name__ == "__main__":
    main()
