"""
Command-line interface for the Model Explainability Toolkit.

Provides various commands to compute explainability scores, generate summaries, compare models, generate counterfactual
explanations, assess fairness, and utilize different explainability techniques such as Obero, Integrated Gradients,
Permutation Importance, and Saliency Maps.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-23
"""

# Import necessary libraries
import argparse

import numpy as np
import pandas as pd
import torch
from transformers import BertTokenizer, BertForSequenceClassification

from examples import run_sandbox
from model_explain.explainers import (
    compare_models,
    generate_counterfactual,
    generate_summary,
    IntegratedGradientsExplainer,
    OberoExplainer,
    PermutationImportanceExplainer,
    SaliencyMapsExplainer,
)
from model_explain.utils import compute_explainability_score, load_model
from model_explain.utils.model_loader import load_pytorch_model, load_sklearn_classifier


def load_data(path):
    """
    Load dataset from a CSV file.

    :param path: Path to the CSV file.
    :type path: str
    :return: DataFrame containing the dataset.
    :rtype: pd.DataFrame
    :raises FileNotFoundError: If the specified file does not exist.
    :raises ValueError: If the file is not a CSV, or if the path is invalid.
    """
    if not isinstance(path, str):
        raise ValueError("The path must be a string.")
    if not path:
        raise ValueError("The path cannot be empty.")
    if not path.endswith(".csv"):
        raise ValueError("The file must be a CSV.")
    if not os.path.exists(path):
        raise FileNotFoundError(f"The specified file does not exist: {path}")
    return pd.read_csv(path)


def main():
    """
    Main function to parse arguments and execute commands.
    """
    parser = argparse.ArgumentParser(description="Model Explainability Toolkit CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Explainability Score
    score_parser = subparsers.add_parser("score", help="Compute explainability score")
    score_parser.add_argument("--model", required=True, help="Path to saved model file")
    score_parser.add_argument("--data", required=True, help="Path to dataset CSV")

    # Natural Language Summary
    summary_parser = subparsers.add_parser(
        "summary", help="Generate natural language summary"
    )
    summary_parser.add_argument("--data", required=True, help="Path to dataset CSV")
    summary_parser.add_argument(
        "--shap", required=True, help="Path to SHAP values .npy file"
    )
    summary_parser.add_argument(
        "--instance", type=int, default=0, help="Index of instance to explain"
    )
    summary_parser.add_argument(
        "--prediction", type=int, required=True, help="Predicted class index"
    )
    summary_parser.add_argument(
        "--classes", nargs="+", required=True, help="List of class names"
    )

    # Model Comparison
    compare_parser = subparsers.add_parser("compare", help="Compare models")
    compare_parser.add_argument(
        "--models", nargs="+", required=True, help="List of model paths"
    )
    compare_parser.add_argument("--data", required=True, help="Path to dataset CSV")

    # Counterfactual Explanations
    cf_parser = subparsers.add_parser(
        "counterfactual", help="Generate counterfactual explanation"
    )
    cf_parser.add_argument("--model", required=True)
    cf_parser.add_argument("--data", required=True)
    cf_parser.add_argument("--instance", type=int, default=0)

    # Fairness Assessment
    fair_parser = subparsers.add_parser("audit", help="Run fairness audit")
    fair_parser.add_argument("--data", required=True)
    fair_parser.add_argument("--predictions", required=True)
    fair_parser.add_argument("--sensitive", required=True)

    # Obero Attention Explanation
    obero_parser = subparsers.add_parser("obero", help="Run Obero attention explainer")
    obero_parser.add_argument("--model", required=True, help="Path to model file")
    obero_parser.add_argument(
        "--tokenizer", required=True, help="Path to tokenizer file"
    )
    obero_parser.add_argument("--text", required=True, help="Input text to explain")
    obero_parser.add_argument(
        "--layer", type=int, default=0, help="Layer index for attention plot"
    )
    obero_parser.add_argument(
        "--head", type=int, default=0, help="Head index for attention plot"
    )

    # Integrated Gradients Attribution
    ig_parser = subparsers.add_parser(
        "integrated_gradients", help="Run Integrated Gradients explainer"
    )
    ig_parser.add_argument("--model", required=True, help="Path to model file")
    ig_parser.add_argument(
        "--baseline", required=True, help="Path to baseline .npy file"
    )
    ig_parser.add_argument("--input", required=True, help="Path to input .npy file")
    ig_parser.add_argument(
        "--target_class", type=int, default=None, help="Target class index"
    )
    ig_parser.add_argument("--steps", type=int, default=50, help="Number of IG steps")

    # Permutation Importance
    perm_parser = subparsers.add_parser(
        "permutation_importance", help="Run Permutation Importance explainer"
    )
    perm_parser.add_argument("--model", required=True, help="Path to model file")
    perm_parser.add_argument("--data", required=True, help="Path to dataset CSV")
    perm_parser.add_argument(
        "--target", type=int, default=None, help="Target class index"
    )
    perm_parser.add_argument(
        "n_repeats", type=int, default=10, help="Number of repeats"
    )
    perm_parser.add_argument(
        "random_state", type=int, default=42, help="Random state for reproducibility"
    )

    # Saliency Map
    saliency_parser = subparsers.add_parser(
        "saliency_map", help="Run Saliency Map explainer"
    )
    saliency_parser.add_argument("--model", required=True, help="Path to model file")
    saliency_parser.add_argument(
        "--input", required=True, help="Path to input .npy file"
    )
    saliency_parser.add_argument(
        "--target_class", type=int, default=None, help="Target class index"
    )

    # Sandbox GUI
    subparsers.add_parser("sandbox", help="Launch explainability sandbox GUI")

    args = parser.parse_args()
    data = load_data(args.data)

    if args.command == "score":
        model = load_model(args.model)
        score = compute_explainability_score(model)
        print(f"Explainability Score: {score}/100")

    elif args.command == "summary":
        shap_values = np.load(args.shap)
        instance = data.iloc[args.instance]
        summary = generate_summary(
            instance,
            shap_values[args.instance],
            list(data.columns),
            args.prediction,
            args.classes,
        )
        print(f"🗣️ Summary:\n{summary}")

    elif args.command == "compare":
        models = {f"Model{i+1}": load_model(path) for i, path in enumerate(args.models)}
        comparison = compare_models(models, data)
        print("⚖️ Top Features by Model:")
        for name, features in comparison.items():
            print(f"{name}: {features}")

    elif args.command == "counterfactual":
        model = load_model(args.model)
        instance = data.iloc[args.instance]
        counterfactual = generate_counterfactual(model, instance, data)
        print(f"🔄 Counterfactual Explanation:\n{counterfactual}")

    elif args.command == "obero":
        # Load model and tokenizer (implement load_model/load_tokenizer as needed)
        model = BertForSequenceClassification.from_pretrained(args.model)
        tokenizer = BertTokenizer.from_pretrained(args.tokenizer)
        explainer = OberoExplainer(model, tokenizer, args.text)
        explainer.plot_attention_weights(args.layer, args.head)

    elif args.command == "integrated_gradients":
        model = load_pytorch_model(args.model)
        input_tensor = np.load(args.input)
        baseline = torch.tensor(np.load(args.baseline))
        input_tensor = torch.tensor(input_tensor)
        explainer = IntegratedGradientsExplainer(
            model, baseline, input_tensor, args.target_class
        )
        attributions = explainer.compute_integrated_gradients(args.steps)
        print(f"The attributions are: {attributions}")
        print("Integrated Gradients computed. Plotting attribution...")
        explainer.plot_attributions()

    elif args.command == "permutation_importance":
        model = load_sklearn_classifier(args.model)
        data = load_data(args.data)
        explainer = PermutationImportanceExplainer(model, data, args.target)
        importances = explainer.calculate_importance(args.n_repeats, args.random_state)
        print(f"Permutation Importances:\n{importances}")

    elif args.command == "saliency_map":
        model = load_pytorch_model(args.model)
        input_tensor = torch.tensor(np.load(args.input))
        explainer = SaliencyMapsExplainer(
            model, input_tensor, target_class=args.target_class
        )
        saliency = explainer.generate_saliency_map()
        print(f"Saliency Map:\n{saliency}")
        explainer.plot_saliency_map()

    elif args.command == "sandbox":
        run_sandbox()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
