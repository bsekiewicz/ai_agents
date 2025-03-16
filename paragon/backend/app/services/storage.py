import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

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

    # Zapis metadanych (nowa funkcjonalność)
    metadata = {
        "file_hash": file_hash,
        "receipt_date": receipt_date,
        "prompt_version": prompt_version,
        "created_at": datetime.now().isoformat(),
        "file_paths": {
            "original": os.path.join(output_dir, f"{file_hash}.jpg"),
            "fixed": os.path.join(output_dir, f"{file_hash}_fixed.jpg"),
            "ocr": os.path.join(output_dir, f"{file_hash}_ocr_{prompt_version}.txt")
        }
    }

    with open(os.path.join(output_dir, f"{file_hash}_metadata.json"), "w", encoding="utf-8") as json_file:
        json.dump(metadata, json_file, indent=2)


async def get_receipt_history(limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Pobiera historię przetworzonych paragonów.

    Args:
        limit: Maksymalna liczba wyników.
        offset: Przesunięcie do paginacji.

    Returns:
        Lista metadanych paragonów.
    """
    receipts = []

    if not os.path.exists(settings.DATA_DIR):
        return receipts

    # Przeszukaj wszystkie katalogi z datami
    for date_dir in sorted(os.listdir(settings.DATA_DIR), reverse=True):
        date_path = os.path.join(settings.DATA_DIR, date_dir)

        if not os.path.isdir(date_path):
            continue

        # Przeszukaj wszystkie katalogi z hashami
        for hash_dir in os.listdir(date_path):
            hash_path = os.path.join(date_path, hash_dir)

            if not os.path.isdir(hash_path):
                continue

            # Znajdź plik metadanych
            metadata_path = os.path.join(hash_path, f"{hash_dir}_metadata.json")

            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                        receipts.append(metadata)
                except Exception:
                    # Zignoruj uszkodzone pliki metadanych
                    pass

    # Sortuj według daty utworzenia (od najnowszych)
    receipts.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    # Zastosuj limit i offset
    return receipts[offset:offset + limit]


async def get_receipt_by_hash(file_hash: str) -> Optional[Dict[str, Any]]:
    """
    Pobiera dane paragonu na podstawie hasza.

    Args:
        file_hash: Hash pliku obrazu.

    Returns:
        Słownik z danymi paragonu lub None, jeśli nie znaleziono.
    """
    if not os.path.exists(settings.DATA_DIR):
        return None

    # Przeszukaj wszystkie katalogi z datami
    for date_dir in os.listdir(settings.DATA_DIR):
        hash_dir_path = os.path.join(settings.DATA_DIR, date_dir, file_hash)

        if os.path.isdir(hash_dir_path):
            # Znajdź plik metadanych
            metadata_path = os.path.join(hash_dir_path, f"{file_hash}_metadata.json")

            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    # Plik metadanych uszkodzony, spróbuj utworzyć go na podstawie dostępnych plików
                    try:
                        # Znajdź pliki OCR i obrazy
                        files = os.listdir(hash_dir_path)
                        ocr_files = [f for f in files if f.endswith('.txt')]

                        if not ocr_files:
                            return None

                        # Wybierz najnowszy plik OCR
                        ocr_file = sorted(ocr_files)[-1]
                        prompt_version = ocr_file.split('_ocr_')[1].split('.txt')[0]

                        # Stwórz słownik metadanych
                        metadata = {
                            "file_hash": file_hash,
                            "receipt_date": date_dir,
                            "prompt_version": prompt_version,
                            "created_at": datetime.now().isoformat(),
                            "file_paths": {
                                "original": os.path.join(hash_dir_path, f"{file_hash}.jpg"),
                                "fixed": os.path.join(hash_dir_path, f"{file_hash}_fixed.jpg"),
                                "ocr": os.path.join(hash_dir_path, ocr_file)
                            }
                        }

                        # Zapisz metadane
                        with open(metadata_path, "w", encoding="utf-8") as f:
                            json.dump(metadata, f, indent=2)

                        return metadata
                    except Exception:
                        return None

    return None
