import os
from pathlib import Path

# Check if static directory exists
static_dir = Path("static")
print(f"Static directory exists: {static_dir.exists()}")

# Check if uploads directory exists
uploads_dir = static_dir / "uploads"
print(f"Uploads directory exists: {uploads_dir.exists()}")

# Create uploads directory if it doesn't exist
uploads_dir.mkdir(parents=True, exist_ok=True)
print(f"Uploads directory exists after creation: {uploads_dir.exists()}")

# Check if placeholder image exists
placeholder = static_dir / "placeholder-image.png"
print(f"Placeholder image exists: {placeholder.exists()}")

# List contents of static directory
print("\nStatic directory contents:")
for item in static_dir.iterdir():
    print(f"  {item.name}")

# List contents of uploads directory
print("\nUploads directory contents:")
if uploads_dir.exists():
    for item in uploads_dir.iterdir():
        print(f"  {item.name}")