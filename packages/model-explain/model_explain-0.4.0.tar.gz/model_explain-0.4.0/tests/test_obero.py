# tests/test_obero.py

"""
Unit tests for the `OberoExplainer` class in the model_explain package.

Tests:
- Initialization
- Attention weights extraction for classification
- Plotting of attention weights

Run with:
    pytest test_obero.py

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-23
"""

import pytest
from unittest.mock import MagicMock, patch
import torch
from model_explain.explainers.obero import OberoExplainer


@pytest.fixture
def mock_model_and_tokenizer():
    """
    Provides a mock transformer classification model and tokenizer.

    :return: Mock model and tokenizer.
    :rtype: tuple (MagicMock, MagicMock)
    """
    tokenizer = MagicMock()
    tokenizer.encode.return_value = torch.tensor([[101, 2003, 2023, 102]])
    tokenizer.convert_ids_to_tokens.return_value = ["[CLS]", "is", "this", "[SEP]"]

    model = MagicMock()
    # Simulate 12 layers, 12 heads, 4 tokens
    fake_attention = [torch.rand(1, 12, 4, 4) for _ in range(12)]
    outputs = MagicMock()
    outputs.attentions = fake_attention
    model.return_value = outputs

    return model, tokenizer


def test_initialization(mock_model_and_tokenizer):
    """
    Test initialization of OberoExplainer.

    :param mock_model_and_tokenizer: Fixture providing mock model and tokenizer.
    :type mock_model_and_tokenizer: tuple
    """
    model, tokenizer = mock_model_and_tokenizer
    explainer = OberoExplainer(model, tokenizer, "is this")
    assert explainer.model is model
    assert explainer.tokenizer is tokenizer
    assert explainer.input_text == "is this"
    assert explainer.input_ids.shape == (1, 4)
    assert explainer.tokens == ["[CLS]", "is", "this", "[SEP]"]


def test_get_attention_weights(mock_model_and_tokenizer):
    """
    Test extraction of attention weights for classification.

    :param mock_model_and_tokenizer: Fixture providing mock model and tokenizer.
    :type mock_model_and_tokenizer: tuple
    """
    model, tokenizer = mock_model_and_tokenizer
    explainer = OberoExplainer(model, tokenizer, "is this")
    attn = explainer.get_attention_weights()
    assert isinstance(attn, list)
    assert len(attn) == 12
    assert attn[0].shape == (1, 12, 4, 4)


def test_plot_attention_weights(mock_model_and_tokenizer):
    """
    Test plotting of attention weights for classification.

    :param mock_model_and_tokenizer: Fixture providing mock model and tokenizer.
    :type mock_model_and_tokenizer: tuple
    """
    model, tokenizer = mock_model_and_tokenizer
    explainer = OberoExplainer(model, tokenizer, "is this")
    with patch("matplotlib.pyplot.show") as mock_show:
        explainer.plot_attention_weights(layer=0, head=0)
        mock_show.assert_called_once()


def main():
    pytest.main([__file__])


if __name__ == "__main__":
    main()
