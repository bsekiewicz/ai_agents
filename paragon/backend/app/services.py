import base64
import hashlib
import io
import os

import pytesseract
from PIL import Image
from dotenv import load_dotenv
from fastapi import UploadFile
from openai import OpenAI

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


def load_prompt(name, version="1_0_0"):
    prompt_path = f"app/data/prompts/{name}_v{version}.txt"
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"⚠️ Plik prompta {prompt_path} nie istnieje!")

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def calculate_sha256(image_data):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(image_data)
    return sha256_hash.hexdigest()


def detect_rotation(image):
    """
    Wykrywa kąt obrotu tekstu w obrazie i zwraca wymagany kąt do poprawnego obrócenia.
    TODO: Naprawić, bo nie zawsze dobrze obraca
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


async def ocr_image(file: UploadFile, prompt_version: str):
    image_data = await file.read()
    file_hash = calculate_sha256(image_data)
    image = Image.open(io.BytesIO(image_data))

    rotate_angle = detect_rotation(image)
    if rotate_angle != 0:
        image_fixed = image.rotate(-90, expand=True)
    else:
        image_fixed = image

    buffered = io.BytesIO()
    image_fixed.save(buffered, format="JPEG")

    base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

    llm_model = "gpt-4o"
    ocr_prompt_version = prompt_version
    ocr_prompt = load_prompt(name="ocr", version=ocr_prompt_version)

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=llm_model,
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

    # check
    check_date = [
        x.split('|')[2].strip()
        for x in receipt_text.split("\n")
        if x.count('|') > 2 and x.split('|')[1].strip() == 'DATE'
    ]
    check_date = check_date[0] if len(check_date) > 0 else '19000101'
    check_company = [
        x.split('|')[2].strip()
        for x in receipt_text.split("\n")
        if x.count('|') > 2 and x.split('|')[1].strip() == 'COMPANY'
    ]
    check_company = check_company[0] if len(check_company) > 0 else 'UNKNOWN'
    check_total = [
        x.split('|')[2].strip()
        for x in receipt_text.split("\n")
        if x.count('|') > 2 and x.split('|')[1].strip() == 'TOTAL'
    ]
    check_total = check_total[0] if len(check_total) > 0 else '0.00'

    # add model and tokens to response
    tokens_in = response.usage.prompt_tokens
    tokens_out = response.usage.completion_tokens
    receipt_text += f'\n| LLM MODEL | {llm_model} |\n| TOKENS IN | {tokens_in} |\n| TOKENS OUT | {tokens_out} |'

    # add file sha to response
    receipt_text += f'\n| HASH | {file_hash} |'

    # add ocr version to response
    receipt_text += f'\n| OCR PROMPT VERSION | {ocr_prompt_version} |'

    # Ścieżka do katalogu z plikami
    output_dir = f"data/{check_date}/{file_hash}"
    os.makedirs(output_dir, exist_ok=True)

    # Zapis obrazka
    image.save(os.path.join(output_dir, f"{file_hash}.jpg"), format="JPEG")
    image_fixed.save(os.path.join(output_dir, f"{file_hash}_fixed.jpg"), format="JPEG")

    # Zapis OCR
    with open(os.path.join(output_dir, f"{file_hash}_ocr_{ocr_prompt_version}.txt"), "w",
              encoding="utf-8") as text_file:
        text_file.write(receipt_text)

    # Zwracam dane do ewentualnej walidacji w aplikacji
    return {
        'file_hash': file_hash,
        'check_date': check_date,
        'check_company': check_company,
        'check_total': check_total,
        'llm_model': llm_model,
        'tokens_in': tokens_in,
        'tokens_out': tokens_out,
        'ocr_prompt_version': ocr_prompt_version,
    }
