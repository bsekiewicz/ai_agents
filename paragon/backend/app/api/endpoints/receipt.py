from fastapi import APIRouter, File, UploadFile, Form
from app.services.ocr import process_receipt_image
from app.models.receipt import OCRResponse

router = APIRouter()


@router.post("/ocr-receipt", response_model=OCRResponse)
async def upload_and_ocr_receipt(
        file: UploadFile = File(...),
        prompt_version: str = Form(None),
):
    """
    Przetwarza przesłany obraz paragonu za pomocą OCR i zwraca wyniki.

    - **file**: Plik obrazu paragonu do przetworzenia
    - **prompt_version**: Opcjonalna wersja promptu OCR (domyślnie używana jest wersja z konfiguracji)
    """
    result = await process_receipt_image(file, prompt_version=prompt_version)
    return result
