# model_explain/explainers/integrated_gradients.py

"""
This module provides an explainer for generating and visualizing Integrated Gradients for classification models.

It uses the Integrated Gradients method to compute feature attributions for a target class by integrating gradients
along the path from a baseline input to the actual input.

Features:
- Compute Integrated Gradients for input features and target class.
- Visualize Integrated Gradients using heatmaps.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-23
"""

import matplotlib.pyplot as plt
import numpy as np
import torch
from torch import nn


class IntegratedGradientsExplainer:
    """
    Explainer for generating and visualizing Integrated Gradients for classification models.
    Uses the Integrated Gradients method to compute feature attributions for a target class by integrating gradients
    along the path from a baseline input to the actual input.

    Attributes:
        model (nn.Module): Trained classification model.
        baseline (torch.Tensor): Baseline input (e.g., zero image).
        input_tensor (torch.Tensor): Input tensor for which to compute attributions.
        target_class (int): Target class index for attribution.
    """

    def __init__(self, model, baseline, input_tensor, target_class=None):
        """
        Initialize the IntegratedGradientsExplainer for classification.

        :param model: Trained classification model (e.g., CNN, transformer)
        :type model: nn.Module
        :param baseline: Baseline input (e.g., zero image, black image)
        :type baseline: torch.Tensor
        :param input_tensor: Input tensor for which to compute attributions
        :type input_tensor: torch.Tensor
        :param target_class: Target class index for attribution (default: highest scoring class)
        :type target_class: int
        """
        self.model = model
        self.baseline = baseline
        self.input_tensor = input_tensor
        self.target_class = target_class

    def compute_integrated_gradients(self, steps=50):
        """
        Compute Integrated Gradients for the input tensor and target class.

        :param steps: Number of steps for interpolation between baseline and input tensor.
        :type steps: int
        :return: Integrated gradients for each feature.
        :rtype: torch.Tensor
        """
        delta = self.input_tensor - self.baseline
        attributions = torch.zeros_like(self.input_tensor)

        for alpha in np.linspace(0, 1, steps):
            interpolated_input = self.baseline + alpha * delta
            interpolated_input.requires_grad = True
            output = self.model(interpolated_input)
            if self.target_class is None:
                target = output.argmax(dim=1).item()
            else:
                target = self.target_class
            output_to_explain = (
                output[0, target] if output.ndim == 2 else output.squeeze()
            )
            self.model.zero_grad()
            output_to_explain.backward(retain_graph=True)
            attributions += interpolated_input.grad.data
        attributions /= steps
        return attributions

    def plot_attributions(self):
        """
        Plot the Integrated Gradients attributions for the target class.
        """
        attributions = self.compute_integrated_gradients()
        attributions = attributions.squeeze().detach().numpy()
        plt.imshow(attributions, cmap="jet")
        plt.axis("off")
        plt.title("Integrated Gradients Attribution")
        plt.colorbar()
        plt.show()
