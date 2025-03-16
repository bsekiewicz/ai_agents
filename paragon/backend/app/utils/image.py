import io
import hashlib
from typing import Optional, Tuple
import base64
import logging
from PIL import Image
import pytesseract
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def calculate_sha256(image_data: bytes) -> str:
    """
    Oblicza SHA256 hash dla danych obrazu.

    Args:
        image_data: Dane obrazu w formacie bajtów.

    Returns:
        Hash SHA256 w formacie heksadecymalnym.
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(image_data)
    return sha256_hash.hexdigest()


def detect_rotation(image: Image.Image) -> int:
    """
    Wykrywa kąt obrotu tekstu w obrazie i zwraca wymagany kąt do poprawnego obrócenia.

    Args:
        image: Obraz w formacie PIL.Image.

    Returns:
        Kąt obrotu w stopniach (0, 90, 180, 270).

    Note:
        Wymaga zainstalowanego pytesseract i Tesseract OCR.
    """
    try:
        osd = pytesseract.image_to_osd(image)
        angle = int(osd.split("\n")[1].split(":")[-1].strip())

        if angle == 90:
            return 90
        elif angle == 270 or angle == -90:
            return -90
        elif angle == 180:
            return 180
        else:
            return 0
    except Exception as e:
        logger.warning(f"Nie udało się wykryć rotacji: {str(e)}. Używam domyślnej orientacji.")
        return 0


def fix_rotation(image: Image.Image) -> Image.Image:
    """
    Poprawia rotację obrazu jeśli jest potrzebna.

    Args:
        image: Obraz w formacie PIL.Image.

    Returns:
        Obraz po poprawieniu rotacji.
    """
    try:
        rotate_angle = detect_rotation(image)
        if rotate_angle != 0:
            return image.rotate(-rotate_angle, expand=True)
        return image
    except Exception as e:
        logger.warning(f"Nie udało się poprawić rotacji: {str(e)}. Zwracam oryginalny obraz.")
        return image


def convert_to_base64(image: Image.Image, format: str = "JPEG") -> str:
    """
    Konwertuje obraz do formatu base64.

    Args:
        image: Obraz w formacie PIL.Image.
        format: Format obrazu wyjściowego (JPEG, PNG, itp.).

    Returns:
        Ciąg znaków base64 reprezentujący obraz.
    """
    buffered = io.BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def optimize_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Optymalizuje obraz dla OCR poprzez zastosowanie filtrów.

    Args:
        image: Obraz w formacie PIL.Image.

    Returns:
        Zoptymalizowany obraz.
    """
    try:
        # Konwersja do skali szarości
        image_gray = image.convert('L')

        # Zwiększenie kontrastu (opcjonalnie)
        # from PIL import ImageEnhance
        # enhancer = ImageEnhance.Contrast(image_gray)
        # image_enhanced = enhancer.enhance(1.5)

        return image_gray
    except Exception as e:
        logger.warning(f"Nie udało się zoptymalizować obrazu: {str(e)}. Zwracam oryginalny obraz.")
        return image


def validate_image(image: Image.Image) -> Tuple[bool, Optional[str]]:
    """
    Sprawdza, czy obraz jest odpowiedni do OCR.

    Args:
        image: Obraz w formacie PIL.Image.

    Returns:
        Tuple zawierający: (czy_obraz_jest_valid, opcjonalny_komunikat_błędu)
    """
    # Sprawdź wymiary
    width, height = image.size
    if width < 100 or height < 100:
        return False, "Obraz jest zbyt mały. Minimalne wymiary to 100x100 pikseli."

    # Sprawdź format
    if image.format not in ['JPEG', 'PNG', 'TIFF', 'BMP']:
        return False, f"Nieobsługiwany format obrazu: {image.format}. Wspierane formaty: JPEG, PNG, TIFF, BMP."

    # Sprawdź, czy obraz nie jest całkowicie pusty/czarny/biały
    if len(image.getcolors(maxcolors=10)) <= 1:
        return False, "Obraz wydaje się być pusty (jednokolorowy)."

    return True, None


def preprocess_image_for_ocr(image_data: bytes) -> Image.Image:
    """
    Wykonuje pełne przetwarzanie obrazu przed OCR.

    Args:
        image_data: Dane obrazu w formacie bajtów.

    Returns:
        Obraz gotowy do OCR.

    Raises:
        HTTPException: Jeśli obraz jest nieprawidłowy.
    """
    try:
        # Wczytaj obraz
        image = Image.open(io.BytesIO(image_data))

        # Walidacja obrazu
        is_valid, error_message = validate_image(image)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=error_message
            )

        # Poprawienie rotacji
        image_fixed = fix_rotation(image)

        # Optymalizacja dla OCR
        image_optimized = optimize_image_for_ocr(image_fixed)

        return image_optimized

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Błąd przetwarzania obrazu: {str(e)}"
        )
