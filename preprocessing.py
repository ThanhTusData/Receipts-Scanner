from PIL import Image, ImageFilter, ImageOps
import numpy as np
import cv2

def preprocess_image(image, mode='auto'):
    """Return a PIL.Image suitable for OCR. Accepts path, PIL.Image, or numpy array."""
    if image is None:
        return None

    # Load if path
    if isinstance(image, str):
        image = Image.open(image)

    # Convert numpy -> PIL
    if not isinstance(image, Image.Image):
        try:
            image = Image.fromarray(image)
        except Exception:
            return None

    # Basic pipeline: convert to grayscale, resize if small, apply slight sharpen
    img = image.convert('RGB')

    # Resize if image is small
    w, h = img.size
    if w < 800:
        scale = 800 / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), resample=Image.LANCZOS)

    gray = ImageOps.grayscale(img)
    gray = gray.filter(ImageFilter.MedianFilter(size=3))

    # Optional adaptive threshold using OpenCV
    try:
        arr = np.array(gray)
        arr = cv2.adaptiveThreshold(
            arr, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )
        return Image.fromarray(arr)
    except Exception:
        return gray
