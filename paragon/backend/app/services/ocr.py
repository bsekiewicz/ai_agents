import io
from PIL import Image
from openai import OpenAI
from fastapi import UploadFile
from app.core.config import settings
from app.utils.image import calculate_sha256, fix_rotation, convert_to_base64
from app.services.storage import save_receipt_files


def load_prompt(version: str = "1_0_3") -> str:
    """Wczytuje prompt dla danej wersji"""
    prompt_path = f"{settings.PROMPT_DIR}/ocr_v{version}.txt"
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"⚠️ Plik prompta {prompt_path} nie istnieje!")


def extract_check_data(receipt_text: str) -> tuple:
    """Wyciąga dane kontrolne z tekstu OCR"""
    # Ekstrakcja daty
    check_date = [
        x.split('|')[2].strip()
        for x in receipt_text.split("\n")
        if x.count('|') > 2 and x.split('|')[1].strip() == 'DATE'
    ]
    check_date = check_date[0] if len(check_date) > 0 else '19000101'

    # Ekstrakcja firmy
    check_company = [
        x.split('|')[2].strip()
        for x in receipt_text.split("\n")
        if x.count('|') > 2 and x.split('|')[1].strip() == 'COMPANY'
    ]
    check_company = check_company[0] if len(check_company) > 0 else 'UNKNOWN'

    # Ekstrakcja kwoty całkowitej
    check_total = [
        x.split('|')[2].strip()
        for x in receipt_text.split("\n")
        if x.count('|') > 2 and x.split('|')[1].strip() == 'TOTAL'
    ]
    check_total = check_total[0] if len(check_total) > 0 else '0.00'

    return check_date, check_company, check_total


async def process_receipt_image(file: UploadFile, prompt_version: str = None) -> dict:
    """Przetwarza obraz paragonu i wykonuje OCR"""
    if prompt_version is None:
        prompt_version = settings.DEFAULT_PROMPT_VERSION

    # Wczytaj obraz
    image_data = await file.read()
    file_hash = calculate_sha256(image_data)
    image = Image.open(io.BytesIO(image_data))

    # Popraw orientację obrazu
    image_fixed = fix_rotation(image)

    # Przekonwertuj obraz do base64
    base64_image = convert_to_base64(image_fixed)

    # Wczytaj prompt i skonfiguruj OpenAI
    ocr_prompt = load_prompt(version=prompt_version)
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # Wykonaj OCR przy użyciu OpenAI
    response = client.chat.completions.create(
        model=settings.DEFAULT_LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": ocr_prompt,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please analyze the following image and extract all text exactly as displayed, without modifications."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
        max_tokens=2500
    )

    receipt_text = response.choices[0].message.content

    # Wyciągnij dane kontrolne
    check_date, check_company, check_total = extract_check_data(receipt_text)

    # Dodaj informacje o modelu i tokenach
    tokens_in = response.usage.prompt_tokens
    tokens_out = response.usage.completion_tokens
    receipt_text += f'\n| LLM MODEL | {settings.DEFAULT_LLM_MODEL} |\n| TOKENS IN | {tokens_in} |\n| TOKENS OUT | {tokens_out} |'

    # Dodaj hash pliku
    receipt_text += f'\n| HASH | {file_hash} |'

    # Dodaj wersję promptu OCR
    receipt_text += f'\n| OCR PROMPT VERSION | {prompt_version} |'

    # Zapisz pliki
    save_receipt_files(
        receipt_date=check_date,
        file_hash=file_hash,
        original_image=image,
        fixed_image=image_fixed,
        ocr_text=receipt_text,
        prompt_version=prompt_version
    )

    # Zwróć dane
    return {
        'file_hash': file_hash,
        'check_date': check_date,
        'check_company': check_company,
        'check_total': check_total,
        'llm_model': settings.DEFAULT_LLM_MODEL,
        'tokens_in': tokens_in,
        'tokens_out': tokens_out,
        'ocr_prompt_version': prompt_version,
    }
