from sklearn.metrics import roc_auc_score

def evaluate_model(model, X, y):
    preds = model.predict_proba(X)[:, 1]
    return {
        "roc_auc": roc_auc_score(y, preds)
    }
