from PIL import Image
import pytesseract
import time


class TesseractAdapter:
    def __init__(self, lang='vie', config='--oem 3 --psm 6'):
        self.lang = lang
        self.config = config


    def extract(self, image):
        """Accepts a PIL.Image or numpy array. Returns dict {raw_text, ocr_meta}"""
        start = time.time()
        if not image:
            return {'raw_text': '', 'ocr_meta': {'engine': 'tesseract', 'duration': 0}}

        try:
            # PIL.Image expected
            if not isinstance(image, Image.Image):
                image = Image.fromarray(image)

            text = pytesseract.image_to_string(
                image,
                lang=self.lang,
                config=self.config
            ).strip()
        except Exception as e:
            text = ''

        return {
            'raw_text': text,
            'ocr_meta': {
                'engine': 'tesseract',
                'duration': time.time() - start
            }
        }
