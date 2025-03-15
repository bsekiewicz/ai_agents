from pydantic import BaseModel
from typing import List, Optional


class OCRCheckResult(BaseModel):
    """Model dla kontrolnych danych z OCR"""
    date: str
    company: str
    total: str


class OCRLine(BaseModel):
    """Model dla linii z OCR paragonu"""
    line_number: int
    category: str
    content: str


class OCRResult(BaseModel):
    """Model dla pełnego wyniku OCR"""
    file_hash: str
    check: OCRCheckResult
    lines: List[OCRLine]
    llm_model: str
    tokens_in: int
    tokens_out: int
    ocr_prompt_version: str


class OCRResponse(BaseModel):
    """Model odpowiedzi z API"""
    file_hash: str
    check_date: str
    check_company: str
    check_total: str
    llm_model: str
    tokens_in: int
    tokens_out: int
    ocr_prompt_version: str
