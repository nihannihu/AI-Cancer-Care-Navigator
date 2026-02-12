
import os
import numpy as np
import cv2
from glob import glob
import tensorflow as tf
from tensorflow.keras import layers, models, backend
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from sklearn.model_selection import train_test_split

# --- Configuration ---
IMG_SIZE = 256
BATCH_SIZE = 2
EPOCHS = 50  # Can be increased for better accuracy
# Adjust these paths based on your Docker container structure
DATASET_PATH = "dataset/Dataset_BUSI_with_GT"
MODEL_SAVE_PATH = "ml/attention_unet.h5"

def load_data(path):
    """
    Loads image and mask paths from the BUSI dataset.
    """
    images = sorted(glob(os.path.join(path, "*", "*).png")))
    masks = sorted(glob(os.path.join(path, "*", "*_mask.png")))
    
    # Filter out normal images if you want to focus on lesions only, 
    # but U-Net handles empty masks fine usually.
    # For now, let's keep everything but ensure alignment.
    
    # A robust way to pair images and masks is needed because some images 
    # might have multiple masks (mask_1, mask_2).
    # The snippet below simplifies to 1 mask per image or merges them.
    # For simplicity in this v1 script, we assume 1 mask or take the primary one.
    
    X = []
    Y = []
    
    for img_path in images:
        # Construct expected mask path
        # Example: benign (10).png -> benign (10)_mask.png
        base_name = os.path.splitext(img_path)[0]
        mask_path = base_name + "_mask.png"
        
        if os.path.exists(mask_path):
            X.append(img_path)
            Y.append(mask_path)
            
    return X, Y

def read_image(path):
    path = path.decode()
    x = cv2.imread(path, cv2.IMREAD_COLOR)
    x = cv2.resize(x, (IMG_SIZE, IMG_SIZE))
    x = x / 255.0
    return x.astype(np.float32)

def read_mask(path):
    path = path.decode()
    x = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    x = cv2.resize(x, (IMG_SIZE, IMG_SIZE))
    # Threshold to make it binary
    _, x = cv2.threshold(x, 127, 255, cv2.THRESH_BINARY)
    x = x / 255.0
    x = np.expand_dims(x, axis=-1)
    return x.astype(np.float32)

def tf_parse(x, y):
    def _parse(x, y):
        x = read_image(x)
        y = read_mask(y)
        return x, y

    x, y = tf.numpy_function(_parse, [x, y], [tf.float32, tf.float32])
    x.set_shape([IMG_SIZE, IMG_SIZE, 3])
    y.set_shape([IMG_SIZE, IMG_SIZE, 1])
    return x, y

def tf_dataset(X, Y, batch=8):
    dataset = tf.data.Dataset.from_tensor_slices((X, Y))
    dataset = dataset.map(tf_parse, num_parallel_calls=tf.data.AUTOTUNE)
    dataset = dataset.batch(batch)
    dataset = dataset.prefetch(tf.data.AUTOTUNE)
    return dataset

# --- Attention U-Net Model ---
def conv_block(x, filter_size, size, dropout, batch_norm=False):
    conv = layers.Conv2D(size, (filter_size, filter_size), padding="same")(x)
    if batch_norm:
        conv = layers.BatchNormalization(axis=3)(conv)
    conv = layers.Activation("relu")(conv)

    conv = layers.Conv2D(size, (filter_size, filter_size), padding="same")(conv)
    if batch_norm:
        conv = layers.BatchNormalization(axis=3)(conv)
    conv = layers.Activation("relu")(conv)

    if dropout > 0:
        conv = layers.Dropout(dropout)(conv)

    return conv

def repeat_elem(tensor, rep):
    # lambda function to repeat One Element like (1, 1, filter) to (W, H, filter)
    # Not explicitly needed if broadcasting works, but good for attention gate.
    return layers.Lambda(lambda x, repnum: backend.repeat_elements(x, repnum, axis=3),
                          arguments={'repnum': rep})(tensor)

def attention_gate(g, s, num_filters):
    Wg = layers.Conv2D(num_filters, 1, padding="same")(g)
    Wg = layers.BatchNormalization()(Wg)
    
    Ws = layers.Conv2D(num_filters, 1, padding="same")(s)
    Ws = layers.BatchNormalization()(Ws)
    
    out = layers.Activation("relu")(layers.add([Wg, Ws]))
    out = layers.Conv2D(1, 1, padding="same")(out)
    out = layers.Activation("sigmoid")(out)
    
    return layers.multiply([out, s])

def attention_unet(input_shape):
    inputs = layers.Input(shape=input_shape)

    # Downsampling
    # 256
    c1 = conv_block(inputs, 3, 64, 0.1, True)
    p1 = layers.MaxPooling2D((2, 2))(c1)

    # 128
    c2 = conv_block(p1, 3, 128, 0.1, True)
    p2 = layers.MaxPooling2D((2, 2))(c2)

    # 64
    c3 = conv_block(p2, 3, 256, 0.1, True)
    p3 = layers.MaxPooling2D((2, 2))(c3)

    # 32
    c4 = conv_block(p3, 3, 512, 0.1, True)
    p4 = layers.MaxPooling2D((2, 2))(c4)

    # Bridge
    c5 = conv_block(p4, 3, 1024, 0.1, True)

    # Upsampling with Attention
    # 32
    u6 = layers.UpSampling2D((2, 2))(c5)
    u6 = layers.Conv2D(512, 2, padding="same")(u6)
    
    # Attention
    s6 = attention_gate(u6, c4, 256) # 512 filters reduced for gate
    # Standard skip connection would be concat([u6, c4])
    # Attention skip connection is concat([u6, s6])
    # Note: Logic above usually matches filters. Let's align filters:
    # Here we typically reduce `g` (u6) and `x` (c4) to intermediate space.
    # Correct implementation of Attention Gate:
    #   g: gating signal (u6), x: skip connection (c4)
    #   The attention gate learns where to look in 'x' based on 'g'.
    
    # Let's use a simpler verified AG implementation block or fix filters:
    # Re-calling `attention_gate(g=u6, s=c4, num_filters=256)`
    # This returns weighted `c4`.
    
    c6 = layers.concatenate([u6, s6]) 
    c6 = conv_block(c6, 3, 512, 0.1, True)

    # 64
    u7 = layers.UpSampling2D((2, 2))(c6)
    u7 = layers.Conv2D(256, 2, padding="same")(u7)
    s7 = attention_gate(u7, c3, 128)
    c7 = layers.concatenate([u7, s7])
    c7 = conv_block(c7, 3, 256, 0.1, True)

    # 128
    u8 = layers.UpSampling2D((2, 2))(c7)
    u8 = layers.Conv2D(128, 2, padding="same")(u8)
    s8 = attention_gate(u8, c2, 64)
    c8 = layers.concatenate([u8, s8])
    c8 = conv_block(c8, 3, 128, 0.1, True)

    # 256
    u9 = layers.UpSampling2D((2, 2))(c8)
    u9 = layers.Conv2D(64, 2, padding="same")(u9)
    s9 = attention_gate(u9, c1, 32)
    c9 = layers.concatenate([u9, s9])
    c9 = conv_block(c9, 3, 64, 0.1, True)

    outputs = layers.Conv2D(1, 1, activation="sigmoid")(c9)

    model = models.Model(inputs=inputs, outputs=outputs)
    return model

def dice_coef(y_true, y_pred):
    y_true_f = backend.flatten(y_true)
    y_pred_f = backend.flatten(y_pred)
    intersection = backend.sum(y_true_f * y_pred_f)
    return (2. * intersection + 1.0) / (backend.sum(y_true_f) + backend.sum(y_pred_f) + 1.0)

def dice_loss(y_true, y_pred):
    return 1 - dice_coef(y_true, y_pred)

def train():
    print(f"Loading data from {DATASET_PATH}...")
    X, Y = load_data(DATASET_PATH)
    
    if len(X) == 0:
        print("No images found! Check path.")
        return

    print(f"Found {len(X)} images.")
    
    train_x, valid_x, train_y, valid_y = train_test_split(X, Y, test_size=0.2, random_state=42)
    
    train_dataset = tf_dataset(train_x, train_y, batch=BATCH_SIZE)
    valid_dataset = tf_dataset(valid_x, valid_y, batch=BATCH_SIZE)
    
    model = attention_unet((IMG_SIZE, IMG_SIZE, 3))
    model.compile(loss=dice_loss, optimizer=tf.keras.optimizers.Adam(1e-4), metrics=[dice_coef, 'accuracy'])
    # model.summary()
    
    callbacks = [
        ModelCheckpoint(MODEL_SAVE_PATH, verbose=1, save_best_only=True),
        ReduceLROnPlateau(monitor='val_loss', factor=0.1, patience=5, min_lr=1e-7, verbose=1),
        EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    ]
    
    print("Starting training...")
    # Save untrained model first to ensure we have something to load if training crashes
    model.save(MODEL_SAVE_PATH)
    
    history = model.fit(
        train_dataset,
        epochs=EPOCHS,
        validation_data=valid_dataset,
        callbacks=callbacks
    )
    print("Training finished.")

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
    train()
