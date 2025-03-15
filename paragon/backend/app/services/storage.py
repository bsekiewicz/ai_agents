import os
from PIL import Image
from app.core.config import settings


def ensure_directory_exists(directory: str) -> None:
    """Upewnia się, że katalog istnieje"""
    os.makedirs(directory, exist_ok=True)


def save_receipt_files(
        receipt_date: str,
        file_hash: str,
        original_image: Image.Image,
        fixed_image: Image.Image,
        ocr_text: str,
        prompt_version: str
) -> None:
    """Zapisuje pliki paragonu w odpowiedniej strukturze katalogów"""

    # Ścieżka do katalogu z plikami
    output_dir = os.path.join(settings.DATA_DIR, receipt_date, file_hash)
    ensure_directory_exists(output_dir)

    # Zapis obrazków
    original_image.save(os.path.join(output_dir, f"{file_hash}.jpg"), format="JPEG")
    fixed_image.save(os.path.join(output_dir, f"{file_hash}_fixed.jpg"), format="JPEG")

    # Zapis OCR
    with open(os.path.join(output_dir, f"{file_hash}_ocr_{prompt_version}.txt"), "w",
              encoding="utf-8") as text_file:
        text_file.write(ocr_text)
