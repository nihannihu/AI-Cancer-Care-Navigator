import tensorflow as tf
from tensorflow.keras.applications import DenseNet121
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
import os
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# --- Configuration ---
DATASET_DIR = Path("dataset/Dataset_BUSI_with_GT")
MODEL_SAVE_PATH = Path("ml/breast_cancer_cnn.h5")
IMG_SIZE = (224, 224)
BATCH_SIZE = 16 # Small batch size for CPU/small GPU
EPOCHS = 15
LEARNING_RATE = 1e-4

def filter_mask_files(path):
    """Filter out mask files from the dataset loading."""
    # This is tricky with image_dataset_from_directory as it doesn't have a filename filter.
    # So we'll have to rely on a custom generator or cleanup first?
    # Actually, BUSI has masks in the SAME folder. This is bad for flow_from_directory.
    # image_dataset_from_directory might pick them up as valid images.
    # We must exclude files ending in '_mask.png'.
    # Since we can't easily filter valid files in tf.data without complex logic, 
    # we will use a custom list_files approach or just let the model handle it (masks look distinct).
    # BETTER APPROACH: Write a quick cleanup/prep function? 
    # No, let's use a custom generator.
    pass

def build_model(num_classes):
    base_model = DenseNet121(weights='imagenet', include_top=False, input_shape=IMG_SIZE + (3,))
    
    # Unfreeze the last few layers for fine-tuning
    base_model.trainable = True
    for layer in base_model.layers[:-30]:
        layer.trainable = False
        
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = BatchNormalization()(x)
    x = Dropout(0.5)(x)
    x = Dense(512, activation='relu')(x)
    x = BatchNormalization()(x)
    x = Dropout(0.3)(x)
    predictions = Dense(num_classes, activation='softmax')(x)
    
    model = Model(inputs=base_model.input, outputs=predictions)
    return model

def main():
    print(f"TensorFlow Version: {tf.__version__}")
    print(f"Loading dataset from: {DATASET_DIR}")
    
    # 1. Custom Data Loading (to ignore masks)
    # BUSI structure: class/image.png, class/image_mask.png
    # We must ONLY load normal images.
    
    images = []
    labels = []
    class_names = sorted([d.name for d in DATASET_DIR.iterdir() if d.is_dir()])
    class_map = {name: i for i, name in enumerate(class_names)}
    
    print(f"Classes found: {class_map}")
    
    valid_extensions = {'.png', '.jpg', '.jpeg'}
    
    for class_name in class_names:
        class_dir = DATASET_DIR / class_name
        for file_path in class_dir.iterdir():
            if file_path.suffix.lower() in valid_extensions and "_mask" not in file_path.name:
                images.append(str(file_path))
                labels.append(class_map[class_name])
                
    print(f"Found {len(images)} valid images (excluding masks).")
    
    # Conversion to dataset
    # Shuffle
    rng = np.random.default_rng(42)
    indices = np.arange(len(images))
    rng.shuffle(indices)
    images = np.array(images)[indices]
    labels = np.array(labels)[indices]
    
    # Split
    val_split = 0.2
    val_size = int(len(images) * val_split)
    
    train_x, val_x = images[val_size:], images[:val_size]
    train_y, val_y = labels[val_size:], labels[:val_size]
    
    print(f"Training on {len(train_x)} images, Validating on {len(val_x)} images.")
    
    def process_path(file_path, label):
        # Load image
        img = tf.io.read_file(file_path)
        img = tf.image.decode_png(img, channels=3)
        img = tf.image.resize(img, IMG_SIZE)
        
        # Preprocessing for DenseNet (scale to 0-1 or specific)
        # DenseNet expects 0-1 or specific mean subtraction. 
        # tf.keras.applications.densenet.preprocess_input does map 0-255 to 0-1 and normalization?
        # Actually standard DenseNet preprocess is just / 255.0 for some, or specific for others.
        # Let's use the official API
        img = tf.keras.applications.densenet.preprocess_input(img)
        return img, label

    def augment(img, label):
        img = tf.image.random_flip_left_right(img)
        img = tf.image.random_brightness(img, max_delta=0.2)
        img = tf.image.random_contrast(img, lower=0.8, upper=1.2)
        return img, label

    # Create TF Datasets
    train_ds = tf.data.Dataset.from_tensor_slices((train_x, train_y))
    train_ds = train_ds.map(process_path, num_parallel_calls=tf.data.AUTOTUNE)
    train_ds = train_ds.map(augment, num_parallel_calls=tf.data.AUTOTUNE)
    train_ds = train_ds.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
    
    val_ds = tf.data.Dataset.from_tensor_slices((val_x, val_y))
    val_ds = val_ds.map(process_path, num_parallel_calls=tf.data.AUTOTUNE)
    val_ds = val_ds.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
    
    # 2. Build Model
    model = build_model(len(class_names))
    
    model.compile(
        optimizer=Adam(learning_rate=LEARNING_RATE),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    model.summary()
    
    # 3. Attributes
    checkpoint = ModelCheckpoint(
        str(MODEL_SAVE_PATH), 
        monitor='val_accuracy', 
        save_best_only=True, 
        mode='max',
        verbose=1
    )
    
    early_stop = EarlyStopping(
        monitor='val_accuracy', 
        patience=5, 
        restore_best_weights=True
    )
    
    reduce_lr = ReduceLROnPlateau(
        monitor='val_loss', 
        factor=0.5, 
        patience=3, 
        min_lr=1e-6
    )
    
    # 4. Train
    print("Starting Training...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=[checkpoint, early_stop, reduce_lr]
    )
    
    # 5. Save Final (if distinct from best)
    # model.save(MODEL_SAVE_PATH) # Checkpoint already saves best
    print(f"Training Complete. Best Model saved to {MODEL_SAVE_PATH}")
    
    # Optional: Save Class indices for loading Later
    import json
    with open("ml/breast_cancer_classes.json", "w") as f:
        json.dump(class_map, f)
    print("Class mapping saved.")

if __name__ == "__main__":
    main()
