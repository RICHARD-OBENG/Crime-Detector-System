# pipelines/training_pipeline.py

from models.training.train import train_model
from models.training.evaluate import evaluate_model
import pandas as pd

def run_training():
    X_train = pd.read_parquet("data/processed/X_train.parquet")
    y_train = pd.read_parquet("data/processed/y_train.parquet")

    model = train_model(X_train, y_train)
    metrics = evaluate_model(model, X_train, y_train)

    return model, metrics

if __name__ == "__main__":
    run_training()
