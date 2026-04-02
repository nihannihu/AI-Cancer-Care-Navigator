
import numpy as np
from PIL import Image
import os

# Create directory if not exists
os.makedirs("static/validation_samples", exist_ok=True)

# Create a simple red 100x100 image
img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
img.save("static/validation_samples/s1_org.png")
print("Starts created mock image at static/validation_samples/s1_org.png")
