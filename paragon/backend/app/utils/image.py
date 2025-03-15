import io
import hashlib
from PIL import Image
import pytesseract

def calculate_sha256(image_data: bytes) -> str:
    """Oblicza SHA256 hash dla danych obrazu"""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(image_data)
    return sha256_hash.hexdigest()

def detect_rotation(image: Image.Image) -> int:
    """
    Wykrywa kąt obrotu tekstu w obrazie i zwraca wymagany kąt do poprawnego obrócenia.
    """
    osd = pytesseract.image_to_osd(image)
    angle = int(osd.split("\n")[1].split(":")[-1].strip())

    if angle == 90:
        return 90
    elif angle == 270:
        return -90
    elif angle == 180:
        return 180
    else:
        return 0

def fix_rotation(image: Image.Image) -> Image.Image:
    """Poprawia rotację obrazu jeśli jest potrzebna"""
    rotate_angle = detect_rotation(image)
    if rotate_angle != 0:
        return image.rotate(-rotate_angle, expand=True)
    return image

def convert_to_base64(image: Image.Image, format: str = "JPEG") -> str:
    """Konwertuje obraz do formatu base64"""
    import base64
    buffered = io.BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")
