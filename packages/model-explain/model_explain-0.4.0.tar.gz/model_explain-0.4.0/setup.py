"""
Setup script for the model_explain package.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-23
"""

# Import necessary modules
from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="model_explain",
    version="0.4.0",
    packages=find_packages(),
    install_requires=[
        "torch>=2.0.0,<3.0.0",
        "plotly>=5.0.0,<6.0.0",
        "fairlearn>=0.8.0,<0.11.0",
        "dice-ml>=0.9,<1.0",
        "numpy>=1.20.0,<2.0.0",
        "pandas>=1.3.0,<2.0.0",
        "scikit-learn>=1.0.0,<2.0.0",
        "shap>=0.41.0,<1.0.0",
        "lime>=0.2.0.1,<0.3.0",
        "streamlit>=1.0.0,<2.0.0",
        "xgboost>=1.5.0,<2.0.0",
        "joblib>=1.0.0,<2.0.0",
        "matplotlib>=3.4.0,<4.0.0",
        "seaborn>=0.11.0,<1.0.0",
    ],
    entry_points={"console_scripts": ["explain-cli=model_explain.cli:main"]},
    author="Vaibhav Kulshrestha",
    author_email="vaibhav1kulshrestha@gmail.com",
    description="A unified Python package for interpreting and explaining machine learning and deep learning models, including feature attention mechanisms. Supports popular explanation techniques such as LIME, SHAP, Grad-CAM, permutation importance, and saliency maps. Provides a consistent interface for tabular, image, and other data types, enabling model transparency and interpretability.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    url="https://github.com/vaibhav-k/model_explain",  # GitHub repository
    project_urls={
        "Source": "https://github.com/vaibhav-k/model_explain",
        "Tracker": "https://github.com/vaibhav-k/model_explain/issues",
    },
)
