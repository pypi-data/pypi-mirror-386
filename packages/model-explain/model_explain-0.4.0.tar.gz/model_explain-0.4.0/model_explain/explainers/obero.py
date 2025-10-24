# model_explain/explainers/obero.py

"""
This module provides an explainer for transformer models using attention weights.

It extracts and visualizes attention weights from transformer models like BERT to explain classification predictions.

Features:
- Extract attention weights from transformer models.
- Visualize attention weights using heatmaps.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-23
"""

import matplotlib.pyplot as plt
import numpy as np
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from typing import List


class OberoExplainer:
    """
    Explainer for transformer models using attention weights.
    Extracts and visualizes attention weights from transformer models like BERT to explain classification predictions.

    Attributes:
        model (BertForSequenceClassification): Pre-trained transformer classification model.
        tokenizer (BertTokenizer): Tokenizer corresponding to the model.
        input_text (str): Text input to explain.
        input_ids (torch.Tensor): Token IDs for the input text.
        tokens (List[str]): List of tokens corresponding to the input IDs.
    """

    def __init__(
        self,
        model,
        tokenizer,
        input_text,
    ):
        """
        Initialize the OberoExplainer for transformer classification models.

        :param model: Pre-trained transformer classification model (e.g., BERT)
        :type model: BertForSequenceClassification
        :param tokenizer: Tokenizer corresponding to the model
        :type tokenizer: BertTokenizer
        :param input_text: Text input to explain
        :type input_text: str
        """
        self.model = model
        self.tokenizer = tokenizer
        self.input_text = input_text
        self.input_ids = self.tokenizer.encode(input_text, return_tensors="pt")
        self.tokens = self.tokenizer.convert_ids_to_tokens(self.input_ids[0])

    def get_attention_weights(self):
        """
        Extract attention weights from the model's attention layers.

        :return: List of attention weights for each layer.
        """
        outputs = self.model(self.input_ids, output_attentions=True)
        attention_weights = outputs.attentions
        return attention_weights

    def plot_attention_weights(self, layer=0, head=0):
        """
        Visualize the attention weights for a specific layer and head.

        :param layer: Layer index to visualize (default: 0)
        :type layer: int
        :param head: Head index to visualize (default: 0)
        :type head: int
        """
        attention_weights = (
            self.get_attention_weights()[layer][0, head].detach().cpu().numpy()
        )
        num_tokens = len(self.tokens)

        fig, ax = plt.subplots(
            figsize=(max(8, num_tokens // 2), max(8, num_tokens // 2))
        )
        cax = ax.matshow(attention_weights, cmap="viridis", aspect="auto")
        ax.set_xticks(np.arange(num_tokens))
        ax.set_yticks(np.arange(num_tokens))
        ax.set_xticklabels(self.tokens, rotation=90, fontsize=8)
        ax.set_yticklabels(self.tokens, fontsize=8)
        plt.title(f"Attention Heatmap (Layer {layer}, Head {head})")
        plt.colorbar(cax)
        plt.tight_layout()
        plt.show()
