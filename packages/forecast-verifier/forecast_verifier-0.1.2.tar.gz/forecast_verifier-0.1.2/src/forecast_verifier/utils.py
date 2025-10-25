import os
import json
import joblib
import pickle


def load_model(model_path) -> object:
    """Load a model from the specified path.

    Args:
        model_path: Path to the model file.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"No file found at {model_path}")
    ext = os.path.splitext(model_path)[1].lower()

    if ext == ".pickle":
        with open(model_path, "rb") as f:
            return pickle.load(f)

    elif ext == ".json":
        with open(model_path, "r") as f:
            return json.load(f)

    elif ext == ".joblib":
        return joblib.load(model_path)

    else:
        raise ValueError(f"Unsupported model_type: {ext}")
