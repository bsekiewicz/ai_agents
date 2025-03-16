from fastapi import APIRouter, File, UploadFile, Form, Query, Path, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import List, Optional
import os

from app.services.ocr import process_receipt_image
from app.services.storage import get_receipt_history, get_receipt_by_hash
from app.models.receipt import OCRResponse
from app.core.config import settings

router = APIRouter()


@router.post("/ocr-receipt", response_model=OCRResponse)
async def upload_and_ocr_receipt(
        file: UploadFile = File(...),
        prompt_version: Optional[str] = Form(None),
):
    """
    Przetwarza przesłany obraz paragonu za pomocą OCR i zwraca wyniki.

    - **file**: Plik obrazu paragonu do przetworzenia
    - **prompt_version**: Opcjonalna wersja promptu OCR (domyślnie używana jest wersja z konfiguracji)
    """
    # Sprawdź rozszerzenie pliku
    filename = file.filename.lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.pdf']

    if not any(filename.endswith(ext) for ext in valid_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Nieprawidłowy format pliku. Dozwolone formaty: {', '.join(valid_extensions)}"
        )

    # Wykonaj OCR
    result = await process_receipt_image(file, prompt_version=prompt_version)

    # Zwróć wynik w formacie OCRResponse
    return OCRResponse(
        file_hash=result['file_hash'],
        check_date=result['check_date'],
        check_company=result['check_company'],
        check_total=result['check_total'],
        llm_model=result['llm_model'],
        tokens_in=result['tokens_in'],
        tokens_out=result['tokens_out'],
        ocr_prompt_version=result['ocr_prompt_version']
    )


@router.get("/receipts", response_model=List[dict])
async def get_receipts_history(
        limit: int = Query(10, ge=1, le=100, description="Maksymalna liczba wyników"),
        offset: int = Query(0, ge=0, description="Przesunięcie do paginacji")
):
    """
    Pobiera historię przetworzonych paragonów.

    - **limit**: Maksymalna liczba wyników (1-100)
    - **offset**: Przesunięcie do paginacji
    """
    return await get_receipt_history(limit=limit, offset=offset)


@router.get("/receipts/{file_hash}", response_model=dict)
async def get_receipt_details(
        file_hash: str = Path(..., description="Hash pliku obrazu")
):
    """
    Pobiera szczegółowe informacje o paragonie na podstawie hasza.

    - **file_hash**: Hash pliku obrazu
    """
    receipt = await get_receipt_by_hash(file_hash)

    if not receipt:
        raise HTTPException(
            status_code=404,
            detail=f"Paragon o hashu {file_hash} nie został znaleziony"
        )

    return receipt


@router.get("/receipts/{file_hash}/image")
async def get_receipt_image(
        file_hash: str = Path(..., description="Hash pliku obrazu"),
        fixed: bool = Query(True, description="Czy zwrócić poprawiony obraz (True) czy oryginalny (False)")
):
    """
    Pobiera obraz paragonu na podstawie hasza.

    - **file_hash**: Hash pliku obrazu
    - **fixed**: Czy zwrócić poprawiony obraz (True) czy oryginalny (False)
    """
    receipt = await get_receipt_by_hash(file_hash)

    if not receipt:
        raise HTTPException(
            status_code=404,
            detail=f"Paragon o hashu {file_hash} nie został znaleziony"
        )

    image_type = "fixed" if fixed else "original"
    image_path = receipt["file_paths"].get(image_type)

    if not image_path or not os.path.exists(image_path):
        raise HTTPException(
            status_code=404,
            detail=f"Obraz paragonu ({image_type}) nie został znaleziony"
        )

    return FileResponse(image_path)


@router.get("/receipts/{file_hash}/ocr")
async def get_receipt_ocr_text(
        file_hash: str = Path(..., description="Hash pliku obrazu")
):
    """
    Pobiera tekst OCR paragonu na podstawie hasza.

    - **file_hash**: Hash pliku obrazu
    """
    receipt = await get_receipt_by_hash(file_hash)

    if not receipt:
        raise HTTPException(
            status_code=404,
            detail=f"Paragon o hashu {file_hash} nie został znaleziony"
        )

    ocr_path = receipt["file_paths"].get("ocr")

    if not ocr_path or not os.path.exists(ocr_path):
        raise HTTPException(
            status_code=404,
            detail="Tekst OCR paragonu nie został znaleziony"
        )

    return FileResponse(ocr_path, media_type="text/plain")
