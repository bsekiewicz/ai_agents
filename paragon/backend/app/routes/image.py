from app.services import ocr_image
from fastapi import APIRouter, File, UploadFile

router = APIRouter()


@router.post("/ocr-image")
async def upload_and_ocr_image(file: UploadFile = File(...)):
    result = await ocr_image(file)
    return result
