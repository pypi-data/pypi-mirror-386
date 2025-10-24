# model_explain/explainers/saliency_maps.py

"""
This module provides an explainer for generating and visualizing saliency maps for image classification models.

It uses gradient-based methods to compute the importance of each pixel in the input image with respect to the model's
classification prediction.

Features:
- Generate saliency maps for input images in classification tasks.
- Visualize saliency maps using heatmaps.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-23
"""

import matplotlib.pyplot as plt
import torch
from torch import nn


class SaliencyMapsExplainer:
    """
    Explainer for generating and visualizing saliency maps for image classification models.
    Uses gradient-based methods to compute the importance of each pixel in the input image with respect to the model's
    classification prediction.

    Attributes:
        model (nn.Module): Trained PyTorch classification model.
        input_tensor (torch.Tensor): Input tensor (e.g., image) for which to compute saliency map.
        target_class (int): Target class index for which saliency map is computed.
    """

    def __init__(self, model, input_tensor, target_class=None):
        """
        Initialize the SaliencyMapsExplainer for classification.

        :param model: Trained PyTorch classification model (e.g., CNN)
        :type model: nn.Module
        :param input_tensor: Input tensor (e.g., image) of shape (1, C, H, W)
        :type input_tensor: torch.Tensor
        :param target_class: Target class index for which saliency map is computed
        :type target_class: int
        """
        self.model = model
        self.input_tensor = input_tensor
        self.target_class = target_class

    def generate_saliency_map(self):
        """
        Generate and compute saliency map for the input tensor for classification.

        :return: Saliency map showing feature importance for each pixel
        """
        self.model.eval()
        self.input_tensor.requires_grad = True
        output = self.model(self.input_tensor)

        if self.target_class is None:
            # Use the class with the highest score
            target_class = output.argmax(dim=1).item()
        else:
            target_class = self.target_class

        # Backpropagate to compute gradients for the target class
        self.model.zero_grad()
        output[0, target_class].backward()

        # Get the absolute value of gradients (max over channels)
        saliency, _ = torch.max(self.input_tensor.grad.data.abs(), dim=1)
        return saliency

    def plot_saliency_map(self):
        """
        Plot the saliency map for classification.
        """
        saliency = self.generate_saliency_map().cpu().numpy()[0]
        plt.imshow(saliency, cmap="hot")
        plt.axis("off")
        plt.title("Saliency Map (Classification)")
        plt.colorbar()
        plt.show()
