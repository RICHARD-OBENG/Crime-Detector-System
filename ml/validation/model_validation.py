def validate_model(metrics: dict):
    if metrics["roc_auc"] < 0.70:
        raise ValueError("Model performance below acceptable threshold")
