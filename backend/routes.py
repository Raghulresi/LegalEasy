from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from backend.ai_core.gemini_generator import GeminiDocumentGenerator
from backend.schemas import DocumentRequest, DocumentResponse
from backend.utils.document_formatter import format_docx, format_pdf

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "service": "LegalEase API"}


@router.post("/generate", response_model=DocumentResponse)
def generate_document(request: DocumentRequest):
    try:
        generator = GeminiDocumentGenerator()
        content = generator.generate_document(
            document_type=request.document_type,
            parties=request.parties,
            terms=request.terms,
            effective_date=request.effective_date,
        )
        return DocumentResponse(
            document_type=request.document_type,
            content=content,
            model=generator.model,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


@router.post("/export/docx")
async def export_docx(
    document_type: str = Form(...),
    content: str = Form(...),
    logo: UploadFile | None = File(default=None),
):
    logo_bytes = await logo.read() if logo else None
    data = format_docx(text=content, doc_type=document_type, logo_bytes=logo_bytes)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="legalease_document.docx"'},
    )


@router.post("/export/pdf")
async def export_pdf(
    document_type: str = Form(...),
    content: str = Form(...),
    logo: UploadFile | None = File(default=None),
):
    logo_bytes = await logo.read() if logo else None
    data = format_pdf(text=content, doc_type=document_type, logo_bytes=logo_bytes)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="legalease_document.pdf"'},
    )