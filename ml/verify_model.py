import os
import numpy as np
import tensorflow as tf
from ml.segmentation_utils import get_segmentor
from ml.train_segmentation import load_busi_data
from sklearn.model_selection import train_test_split

def verify_model_performance():
    print("Add 'verify_model' to your python path or run as module")
    print("Loading dataset...")
    # Re-use data loading logic
    images, masks = load_busi_data()
    
    # Split exactly as training did (random_state=42) to get the same validation set
    X_train, X_val, y_train, y_val = train_test_split(images, masks, test_size=0.15, random_state=42)
    
    print(f"Validation Set Size: {len(X_val)} images")
    
    # Load model
    print("Loading trained model...")
    model_path = "ml/attention_unet.h5"
    if not os.path.exists(model_path):
        print("Model not found!")
        return

    # Load via existing utility or direct keras
    # We use direct keras load to run .evaluate()
    model = tf.keras.models.load_model(model_path, compile=False)
    
    # Compile with same metrics to evaluate
    from ml.train_segmentation import dice_coef, dice_loss
    model.compile(optimizer='adam', loss=dice_loss, metrics=['accuracy', dice_coef])
    
    print("Running evaluation on validation set...")
    results = model.evaluate(X_val, y_val, batch_size=8)
    
    loss = results[0]
    accuracy = results[1]
    dice = results[2]
    
    print("\n" + "="*30)
    print("   MODEL VERIFICATION RESULTS   ")
    print("="*30)
    print(f"✅ Accuracy:       {accuracy*100:.2f}%")
    print(f"✅ Dice Coeff:     {dice:.4f}")
    print(f"✅ Loss:           {loss:.4f}")
    print("="*30)
    print("\nProof: These numbers are calculated live on unseen data.")

if __name__ == "__main__":
    verify_model_performance()
