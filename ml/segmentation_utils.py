
import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras import backend as K
import base64
from io import BytesIO
from PIL import Image

# Re-define custom objects needed for loading the model
def dice_coef(y_true, y_pred):
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + 1.0) / (K.sum(y_true_f) + K.sum(y_pred_f) + 1.0)

def dice_loss(y_true, y_pred):
    return 1 - dice_coef(y_true, y_pred)

class SegmentationModel:
    def __init__(self, model_path="ml/attention_unet.h5"):
        self.model_path = model_path
        self.model = None
        self.img_size = 256
        self.load()

    def load(self):
        if os.path.exists(self.model_path):
            try:
                self.model = load_model(self.model_path, custom_objects={'dice_loss': dice_loss, 'dice_coef': dice_coef})
                print(f"Segmentation model loaded from {self.model_path}")
            except Exception as e:
                print(f"Error loading segmentation model: {e}")
        else:
            print(f"Segmentation model not found at {self.model_path}")

    def predict_mask(self, image_bytes):
        """
        Input: Raw image bytes
        Output: Base64 encoded mask image overlay or side-by-side
        """
        if self.model is None:
            return None, "Model not loaded"

        try:
            # 1. Preprocess
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            original_shape = img.shape[:2] # h, w
            
            x = cv2.resize(img, (self.img_size, self.img_size))
            x = x / 255.0
            x = np.expand_dims(x, axis=0) # (1, 256, 256, 3)

            # 2. Predict
            pred_mask = self.model.predict(x)[0] # (256, 256, 1)
            
            # 3. Post-process mask
            pred_mask = (pred_mask > 0.5).astype(np.uint8) * 255
            pred_mask = cv2.resize(pred_mask, (original_shape[1], original_shape[0])) # Resize back to original
            
            # 4. Create visualization
            # Create a green overlay
            # mask is (H, W), make it (H, W, 3)
            colored_mask = np.zeros_like(img)
            colored_mask[:, :, 1] = pred_mask # Green channel
            
            # Blend
            alpha = 0.4
            overlay = cv2.addWeighted(img, 1, colored_mask, alpha, 0)
            
            # Encode to base64
            _, buffer = cv2.imencode('.jpg', overlay)
            overlay_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return f"data:image/jpeg;base64,{overlay_base64}", None

        except Exception as e:
            print(f"Prediction error: {e}")
            return None, str(e)

    def generate_comparison(self, image_bytes):
        """
        Generates a side-by-side comparison: Original | Mask Overlay | Binary Mask
        Useful for the 'Hard Verification' artifacts.
        """
        if self.model is None:
            return None
            
        try:
             # 1. Preprocess
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            original_shape = img.shape[:2]
            
            x = cv2.resize(img, (self.img_size, self.img_size)) / 255.0
            x = np.expand_dims(x, axis=0)

            # 2. Predict
            pred_mask = self.model.predict(x)[0]
            pred_mask = (pred_mask > 0.5).astype(np.uint8) * 255
            pred_mask = cv2.resize(pred_mask, (original_shape[1], original_shape[0]))
            
            # 3. Create Visualize: Vertical stack or Horizontal? Let's do Horizontal
            # Original
            vis_img = img.copy()
            
            # Overlay (Green)
            colored_mask = np.zeros_like(img)
            colored_mask[:, :, 1] = pred_mask
            vis_overlay = cv2.addWeighted(img, 1, colored_mask, 0.4, 0)
            
            # Binary Mask (White on Black)
            vis_mask = cv2.cvtColor(pred_mask, cv2.COLOR_GRAY2BGR)
            
            # Stack: Original | Overlay | Mask
            # Ensure heights match if needed, but they are from same source
            combined = np.hstack((vis_img, vis_overlay, vis_mask))
            
            # Optimize size if too large
            if combined.shape[1] > 1200:
                scale = 1200 / combined.shape[1]
                combined = cv2.resize(combined, (0,0), fx=scale, fy=scale)
            
            _, buffer = cv2.imencode('.jpg', combined)
            return base64.b64encode(buffer).decode('utf-8')
            
        except Exception as e:
            print(f"Comparison gen error: {e}")
            return None

# Global instance
segmentor = None

def get_segmentor():
    global segmentor
    if segmentor is None:
        segmentor = SegmentationModel()
    return segmentor
