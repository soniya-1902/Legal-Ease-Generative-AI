from __future__ import annotations

import base64
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator

from backend.ai_core.gemini_generator import GeminiDocumentGenerator
from backend.config import get_settings
from backend.services.document_formatter import format_docx, format_pdf
from backend.utils.text_utils import sanitize_text

router = APIRouter()


class DocumentRequest(BaseModel):
    document_type: str = Field(..., min_length=2, max_length=150)
    parties: str = Field(..., min_length=2, max_length=5000)
    terms: str = Field(default="", max_length=10000)
    effective_date: str = Field(default="", max_length=100)
    # Compatibility with the PDF wording, which sometimes calls the field "dates".
    dates: Optional[str] = Field(default=None, max_length=100)

    @field_validator("document_type", "parties", "terms", "effective_date", "dates")
    @classmethod
    def clean(cls, value):
        return sanitize_text(value) if value is not None else value

    def resolved_date(self) -> str:
        return self.effective_date or self.dates or ""


class ExportRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=30000)
    document_type: str = Field(default="Legal Document", max_length=150)
    logo_base64: Optional[str] = None
    font_name: str = Field(default="Times New Roman", max_length=80)


generator = GeminiDocumentGenerator()


@router.get("/health")
def health():
    settings = get_settings()
    return {"status": "ok", "service": settings.app_name, "mock_ai": settings.mock_ai, "model": settings.gemini_model}


@router.post("/generate")
def generate(request: DocumentRequest):
    settings = get_settings()
    if len(request.parties) > 5000 or len(request.terms) > 10000:
        raise HTTPException(status_code=422, detail="Input is too long.")
    try:
        result = generator.generate_document(
            request.document_type,
            request.parties,
            request.terms,
            request.resolved_date(),
        )
        return {
            "document_type": request.document_type,
            "content": result.text,
            "model": result.model,
            "mock": result.mock,
            "notice": "Draft only; review for accuracy and applicable legal requirements before use.",
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _decode_logo(value: Optional[str]) -> Optional[bytes]:
    if not value:
        return None
    try:
        if "," in value and value.startswith("data:"):
            value = value.split(",", 1)[1]
        return base64.b64decode(value, validate=True)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Invalid logo data.") from exc


@router.post("/export/txt")
def export_txt(request: ExportRequest):
    return Response(content=sanitize_text(request.content), media_type="text/plain; charset=utf-8")


@router.post("/export/docx")
def export_docx(request: ExportRequest):
    try:
        data = format_docx(
            request.content,
            request.document_type,
            logo_bytes=_decode_logo(request.logo_base64),
            font_name=request.font_name,
        )
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": 'attachment; filename="legalease-document.docx"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DOCX export failed: {exc}") from exc


@router.post("/export/pdf")
def export_pdf(request: ExportRequest):
    try:
        data = format_pdf(
            request.content,
            request.document_type,
            logo_bytes=_decode_logo(request.logo_base64),
        )
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="legalease-document.pdf"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF export failed: {exc}") from exc
