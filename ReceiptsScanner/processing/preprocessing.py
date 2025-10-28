"""
Image preprocessing for better OCR results
"""
import cv2
import numpy as np
from PIL import Image
import os
from monitoring.logging_config import get_logger

logger = get_logger(__name__)

def preprocess_image(image_path: str, dpi: int = 300) -> np.ndarray:
    """
    Preprocess receipt image for better OCR accuracy
    
    Args:
        image_path: Path to the image file
        dpi: Target DPI for image (default: 300)
        
    Returns:
        np.ndarray: Preprocessed image
    """
    try:
        logger.info(f"Preprocessing image: {image_path}")
        
        # Read image
        image = cv2.imread(image_path)
        
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        # Deskew if needed
        deskewed = deskew_image(thresh)
        
        # Resize to target DPI if image is too small
        resized = resize_to_dpi(deskewed, target_dpi=dpi)
        
        # Enhance contrast
        enhanced = enhance_contrast(resized)
        
        logger.info(f"Image preprocessed: {enhanced.shape}")
        
        return enhanced
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}")
        # Return original grayscale image if preprocessing fails
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        return image if image is not None else np.zeros((100, 100), dtype=np.uint8)


def deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Detect and correct skew in image
    
    Args:
        image: Grayscale image
        
    Returns:
        np.ndarray: Deskewed image
    """
    try:
        # Calculate skew angle
        coords = np.column_stack(np.where(image > 0))
        
        if len(coords) < 5:
            return image
        
        angle = cv2.minAreaRect(coords)[-1]
        
        # Adjust angle
        if angle < -45:
            angle = 90 + angle
        elif angle > 45:
            angle = angle - 90
        
        # Only deskew if angle is significant
        if abs(angle) > 0.5:
            # Get image center and rotation matrix
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            
            # Rotate image
            rotated = cv2.warpAffine(
                image,
                M,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            
            logger.info(f"Image deskewed by {angle:.2f} degrees")
            return rotated
        
        return image
        
    except Exception as e:
        logger.warning(f"Deskew failed: {str(e)}")
        return image


def resize_to_dpi(image: np.ndarray, target_dpi: int = 300, current_dpi: int = 72) -> np.ndarray:
    """
    Resize image to target DPI
    
    Args:
        image: Input image
        target_dpi: Desired DPI
        current_dpi: Current DPI of image
        
    Returns:
        np.ndarray: Resized image
    """
    try:
        scale_factor = target_dpi / current_dpi
        
        # Only upscale, don't downscale
        if scale_factor > 1.0:
            new_width = int(image.shape[1] * scale_factor)
            new_height = int(image.shape[0] * scale_factor)
            
            resized = cv2.resize(
                image,
                (new_width, new_height),
                interpolation=cv2.INTER_CUBIC
            )
            
            logger.info(f"Image resized to {resized.shape}")
            return resized
        
        return image
        
    except Exception as e:
        logger.warning(f"Resize failed: {str(e)}")
        return image


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Enhance image contrast using CLAHE
    
    Args:
        image: Grayscale image
        
    Returns:
        np.ndarray: Contrast-enhanced image
    """
    try:
        # Create CLAHE object
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        
        # Apply CLAHE
        enhanced = clahe.apply(image)
        
        return enhanced
        
    except Exception as e:
        logger.warning(f"Contrast enhancement failed: {str(e)}")
        return image


def remove_borders(image: np.ndarray, threshold: int = 240) -> np.ndarray:
    """
    Remove white borders from image
    
    Args:
        image: Grayscale image
        threshold: Pixel value threshold for border detection
        
    Returns:
        np.ndarray: Image with borders removed
    """
    try:
        # Find non-white pixels
        non_white_pixels = np.where(image < threshold)
        
        if len(non_white_pixels[0]) == 0 or len(non_white_pixels[1]) == 0:
            return image
        
        # Get bounding box
        top = non_white_pixels[0].min()
        bottom = non_white_pixels[0].max()
        left = non_white_pixels[1].min()
        right = non_white_pixels[1].max()
        
        # Crop image
        cropped = image[top:bottom+1, left:right+1]
        
        return cropped
        
    except Exception as e:
        logger.warning(f"Border removal failed: {str(e)}")
        return image