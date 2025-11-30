from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras import layers, models

# Project root assumed to be the directory containing this file's parent
ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "csv"
JPEG_DIR = ROOT / "jpeg"
MODEL_DIR = ROOT / "ml"
MODEL_PATH = MODEL_DIR / "breast_cancer_cnn.h5"

DICOM_INFO_CSV = CSV_DIR / "dicom_info.csv"
META_CSV = CSV_DIR / "meta.csv"
CALC_DESC_CSV = CSV_DIR / "calc_case_description_train_set.csv"
MASS_DESC_CSV = CSV_DIR / "mass_case_description_train_set.csv"

IMG_SIZE = (224, 224)


def _uid_from_path(path: str) -> str | None:
    """Extract a SeriesInstanceUID-like token from a path string.

    The CBIS-DDSM paths contain UIDs like 1.3.6.1.4.1.9590.100.1.2.xxxxx.
    We scan tokens and return the last such token if present.
    """
    parts = str(path).split("/")
    for token in reversed(parts):
        if token.startswith("1.3.6.1.4.1.9590.100.1.2."):
            return token
    return None


def load_labeled_examples(limit: int | None = 2000) -> Tuple[List[Path], np.ndarray]:
    """Build (image_path, label) pairs from local CSV/JPEG files.

    Label: 1 = malignant, 0 = benign / benign without callback.
    """
    if not DICOM_INFO_CSV.exists():
        raise FileNotFoundError(f"Missing {DICOM_INFO_CSV}")
    if not META_CSV.exists():
        raise FileNotFoundError(f"Missing {META_CSV}")

    dicom_df = pd.read_csv(DICOM_INFO_CSV)
    meta_df = pd.read_csv(META_CSV)

    # Keep only cropped images (ROI-like) for training
    meta_cropped = meta_df[meta_df["SeriesDescription"] == "cropped images"]
    merged = dicom_df.merge(
        meta_cropped[["SeriesInstanceUID", "SeriesDescription"]],
        on="SeriesInstanceUID",
        how="inner",
    )

    # Build mapping SeriesInstanceUID -> pathology from calc + mass description CSVs
    label_rows = []
    for desc_path in [CALC_DESC_CSV, MASS_DESC_CSV]:
        if not desc_path.exists():
            continue
        df = pd.read_csv(desc_path)
        for _, row in df.iterrows():
            uid = _uid_from_path(row.get("cropped image file path", ""))
            if not uid:
                continue
            label_rows.append({
                "SeriesInstanceUID": uid,
                "pathology": str(row.get("pathology", "")).upper(),
            })

    labels_df = pd.DataFrame(label_rows).drop_duplicates()
    if labels_df.empty:
        raise RuntimeError("No labels could be constructed from calc/mass CSVs.")

    merged = merged.merge(labels_df, on="SeriesInstanceUID", how="inner")

    # Binary labels: malignant vs the rest
    merged["label"] = merged["pathology"].apply(
        lambda p: 1 if "MALIGNANT" in p else 0
    )

    # Map CBIS-DDSM/jpeg prefix to local jpeg/ root
    image_paths: List[Path] = []
    labels: List[int] = []

    for _, row in merged.iterrows():
        rel = str(row["image_path"]).replace("CBIS-DDSM/jpeg", "jpeg")
        img_path = ROOT / rel
        if img_path.is_file():
            image_paths.append(img_path)
            labels.append(int(row["label"]))

    if not image_paths:
        raise RuntimeError("No image files found matching dicom_info/image_path entries.")

    if limit is not None and len(image_paths) > limit:
        image_paths = image_paths[:limit]
        labels = labels[:limit]

    return image_paths, np.asarray(labels, dtype=np.int32)


def load_image(path: Path) -> np.ndarray:
    img = Image.open(path).convert("L")
    img = img.resize(IMG_SIZE)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    arr = np.expand_dims(arr, axis=-1)  # (H, W, 1)
    return arr


def build_dataset(paths: List[Path], labels: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    X = np.stack([load_image(p) for p in paths], axis=0)
    y = labels.astype(np.float32)
    return X, y


def build_model() -> tf.keras.Model:
    inputs = layers.Input(shape=(*IMG_SIZE, 1))
    x = layers.Conv2D(32, 3, activation="relu", padding="same")(inputs)
    x = layers.MaxPooling2D()(x)
    x = layers.Conv2D(64, 3, activation="relu", padding="same")(x)
    x = layers.MaxPooling2D()(x)
    x = layers.Conv2D(128, 3, activation="relu", padding="same")(x)
    x = layers.MaxPooling2D()(x)
    x = layers.Flatten()(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.5)(x)
    outputs = layers.Dense(1, activation="sigmoid")(x)

    model = models.Model(inputs=inputs, outputs=outputs)
    model.compile(
        optimizer="adam",
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    return model


def main() -> None:
    print("[train_cnn] Loading labeled examples...")
    paths, labels = load_labeled_examples(limit=2000)  # limit for hackathon speed
    print(f"[train_cnn] Found {len(paths)} images")

    print("[train_cnn] Building dataset tensors...")
    X, y = build_dataset(paths, labels)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    print("[train_cnn] Building model...")
    model = build_model()
    model.summary()

    print("[train_cnn] Training...")
    model.fit(
        X_train,
        y_train,
        validation_data=(X_val, y_val),
        epochs=10,
        batch_size=16,
    )

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save(MODEL_PATH)
    print(f"[train_cnn] Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
