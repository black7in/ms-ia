import os
from pathlib import Path

import joblib
import pandas as pd
import xgboost as xgb


def train_demand_model(data_path: str, model_output: str) -> None:
    df = pd.read_csv(data_path)

    feature_cols = [
        "dia_semana",
        "es_feriado",
        "mes",
        "semana_del_anio",
        "es_temporada_alta",
        "ocupacion_semana_anterior",
        "ocupacion_mismo_dia_semana_pasada",
    ]
    target_col = "ocupacion"

    X = df[feature_cols]
    y = df[target_col]

    model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
    )
    model.fit(X, y)

    Path(model_output).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_output)

    score = model.score(X, y)
    print(f"XGBoost entrenado. R²={score:.4f}. Guardado en {model_output}")


if __name__ == "__main__":
    base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "tmp", "training_data")
    model_dir = os.path.join(os.path.dirname(__file__), "..")

    train_demand_model(
        data_path=os.path.join(base_dir, "demand_data.csv"),
        model_output=os.path.join(model_dir, "demand_model.pkl"),
    )
