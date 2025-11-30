from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image
import tensorflow as tf

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = ROOT / "ml" / "breast_cancer_cnn.h5"
IMG_SIZE = (224, 224)


class BreastCancerModel:
    def __init__(self, model_path: Path | None = None) -> None:
        self.model_path = model_path or DEFAULT_MODEL_PATH
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        self.model = tf.keras.models.load_model(self.model_path)

    def preprocess_bytes(self, data: bytes) -> np.ndarray:
        img = Image.open(BytesIO(data)).convert("L")
        img = img.resize(IMG_SIZE)
        arr = np.asarray(img, dtype=np.float32) / 255.0
        arr = np.expand_dims(arr, axis=-1)  # (H, W, 1)
        arr = np.expand_dims(arr, axis=0)   # (1, H, W, 1)
        return arr

    def predict_proba(self, data: bytes) -> float:
        x = self.preprocess_bytes(data)
        prob = float(self.model.predict(x)[0][0])
        return prob

    def predict_label(self, data: bytes, threshold: float = 0.5) -> Tuple[str, float]:
        prob = self.predict_proba(data)
        label = "MALIGNANT" if prob >= threshold else "BENIGN"
        return label, prob
        
    def predict_stage(self, prob: float) -> str:
        """
        Predict cancer stage based on probability score.
        This is a simplified staging system for demonstration purposes.
        """
        if prob < 0.3:
            return "Stage 0 (DCIS)"
        elif prob < 0.5:
            return "Stage I"
        elif prob < 0.7:
            return "Stage II"
        elif prob < 0.9:
            return "Stage III"
        else:
            return "Stage IV"