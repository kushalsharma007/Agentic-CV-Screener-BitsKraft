# config.py
import os

def get_save_directory(default=None):
    try:
        # Read the path from the file
        with open("cv_save_path.txt", "r", encoding="utf-8") as f:
            path = f.read().strip()

        # Check if path is valid and exists
        if path and os.path.exists(path) and os.path.isdir(path):
            return os.path.abspath(path)
        else:
            print(f"⚠️  Saved path not found or invalid: {path}")
    except Exception as e:
        print(f"⚠️  Could not read cv_save_path.txt: {e}")

    # Fallback to default
    print(f"📁 Using default save directory: {default}")
    return default