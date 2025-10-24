# model_explain/utils/model_loader.py

"""
Utility function to load a machine learning model from a specified file path.

Features:
- Uses joblib for loading models.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-23
"""

# Import necessary libraries
import os


def load_model(path):
    """
    Load a machine learning model from the specified file path.

    :param path: The file path to the saved model.
    :type path: str
    :return: The loaded model object.
    :rtype: object
    :raises FileNotFoundError: If the specified file does not exist.
    :raises Exception: For any other issues encountered during loading.
    """
    import joblib

    if not isinstance(path, str):
        raise ValueError("The path must be a string.")
    if not path:
        raise ValueError("The path cannot be empty.")
    if not os.path.exists(path):
        raise FileNotFoundError(f"The specified file does not exist: {path}")
    try:
        return joblib.load(path)
    except Exception as e:
        raise Exception(f"An error occurred while loading the model: {e}")


def load_pytorch_model(path):
    """
    Load a PyTorch model from the specified file path.

    :param path: The file path to the saved PyTorch model.
    :type path: str
    :return: The loaded PyTorch model object.
    :rtype: torch.nn.Module
    :raises FileNotFoundError: If the specified file does not exist.
    :raises Exception: For any other issues encountered during loading.
    """
    import torch

    if not isinstance(path, str):
        raise ValueError("The path must be a string.")
    if not path:
        raise ValueError("The path cannot be empty.")
    if not os.path.exists(path):
        raise FileNotFoundError(f"The specified file does not exist: {path}")
    try:
        model = torch.load(path)
        model.eval()  # Set the model to evaluation mode
        return model
    except Exception as e:
        raise Exception(f"An error occurred while loading the PyTorch model: {e}")


def load_sklearn_classifier(path):
    """
    Load a scikit-learn classifier model from the specified file path.

    :param path: The file path to the saved classifier model.
    :type path: str
    :return: The loaded classifier model object.
    :rtype: sklearn.base.ClassifierMixin
    :raises FileNotFoundError: If the specified file does not exist.
    :raises TypeError: If the loaded object is not a ClassifierMixin.
    :raises ValueError: If the path is not a valid string or is empty.
    :raises FileNotFoundError: If the specified file does not exist.
    """
    from sklearn.base import ClassifierMixin

    if not isinstance(path, str):
        raise ValueError("The path must be a string.")
    if not path:
        raise ValueError("The path cannot be empty.")
    if not os.path.exists(path):
        raise FileNotFoundError(f"The specified file does not exist: {path}")

    model = load_model(path)
    if not isinstance(model, ClassifierMixin):
        raise TypeError(
            f"Expected type 'ClassifierMixin', got '{type(model).__name__}' instead."
        )
    return model
