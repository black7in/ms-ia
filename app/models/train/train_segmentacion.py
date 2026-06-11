import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


def train_segmentacion_model(data_path: str, model_output: str) -> None:
    df = pd.read_csv(data_path)

    feature_cols = [
        "frecuencia_mensual",
        "gasto_promedio",
        "variedad_rutas",
        "dia_preferido",
    ]

    X = df[feature_cols].values

    model = KMeans(n_clusters=3, random_state=42, n_init=10)
    model.fit(X)

    Path(model_output).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_output)

    inertia = model.inertia_
    counts = np.bincount(model.labels_)
    print(
        f"K-Means entrenado. Inercia={inertia:.2f}. "
        f"Clusters: {dict(zip(range(3), counts.tolist()))}. Guardado en {model_output}"
    )


if __name__ == "__main__":
    base_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "tmp", "training_data"
    )
    model_dir = os.path.join(os.path.dirname(__file__), "..")

    train_segmentacion_model(
        data_path=os.path.join(base_dir, "clientes_data.csv"),
        model_output=os.path.join(model_dir, "kmeans_model.pkl"),
    )
