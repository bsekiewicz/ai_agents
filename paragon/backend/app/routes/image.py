from app.services import ocr_image
from fastapi import APIRouter, File, UploadFile, Form

router = APIRouter()

@router.post("/ocr-image")
async def upload_and_ocr_image(
    file: UploadFile = File(...),
    prompt_version: str = Form("1_0_3"),
):
    result = await ocr_image(file, prompt_version=prompt_version)
    return result
