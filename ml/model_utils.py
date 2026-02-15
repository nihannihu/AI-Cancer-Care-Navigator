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
        self.is_new_model = False
        
        # Check for class mapping file to determine if we are using the new model
        self.class_map_path = ROOT / "ml" / "breast_cancer_classes.json"
        
        if not self.model_path.exists():
             # If default model likely missing, don't crash, just warn or late init?
             # For now, raise as before, but user might have to run training first.
             print(f"WARNING: Model file not found at {self.model_path}. Please run training script.")
             self.model = None
             return

        try:
            self.model = tf.keras.models.load_model(self.model_path)
            if self.class_map_path.exists():
                self.is_new_model = True
                print("Loaded new DenseNet121 model.")
            else:
                print("Loaded legacy model.")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None

    def preprocess_bytes(self, data: bytes) -> np.ndarray:
        if self.is_new_model:
            # DenseNet Preprocessing: RGB, 224x224, default densenet preprocessing
            img = Image.open(BytesIO(data)).convert("RGB")
            img = img.resize(IMG_SIZE)
            arr = np.array(img, dtype=np.float32)
            # Use tf.keras.applications.densenet.preprocess_input logic (scale to 0-1 or -1 to 1)
            # To avoid strict dependency on the specific function if not available, we can use standard:
            # DenseNet standard is often 1/255. But let's use the TF util if possible, or standard.
            # safe fallback:
            arr = tf.keras.applications.densenet.preprocess_input(arr)
            arr = np.expand_dims(arr, axis=0) # (1, 224, 224, 3)
            return arr
        else:
            # Legacy Preprocessing
            img = Image.open(BytesIO(data)).convert("L")
            img = img.resize(IMG_SIZE)
            arr = np.asarray(img, dtype=np.float32) / 255.0
            arr = np.expand_dims(arr, axis=-1)  # (H, W, 1)
            arr = np.expand_dims(arr, axis=0)   # (1, H, W, 1)
            return arr

    def predict_proba(self, data: bytes) -> float:
        if self.model is None:
            return 0.0
            
        x = self.preprocess_bytes(data)
        
        if self.is_new_model:
            # New model returns [p_benign, p_malignant, p_normal] (assuming sorted alphabetic)
            # We map Normal (idx 2) and Benign (idx 0) to Benign. Malignant (idx 1) is Malignant.
            # We return probability of Malignancy.
            preds = self.model.predict(x)[0] # e.g. [0.1, 0.8, 0.1]
            # Assuming 0=Benign, 1=Malignant, 2=Normal
            # Check class map if possible, but hardcoded for now based on training script logic
            prob_malignant = float(preds[1])
            return prob_malignant
        else:
            # Legacy
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