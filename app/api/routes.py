# app/api/routes.py - FastAPI Route Definitions

import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from app.schemas import (
    HealthResponse,
    UploadResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    ErrorDetail,
)
from app.services.analysis_service import (
    process_upload_zip,
    run_analysis_for_session,
)
from app.config import settings

router = APIRouter(prefix="/api", tags=["NLP Zahir API"])
logger = logging.getLogger("nlp_zahir.routes")


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Health Check Endpoint untuk memeriksa status layanan backend."""
    return HealthResponse(
        status="ok",
        service="nlp-zahir-api",
        version=settings.VERSION
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_whatsapp_zip(file: UploadFile = File(...)):
    """Menerima file zip ekspor WhatsApp dan menjalankan ingestion."""
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Berkas file upload harus disediakan."
        )
        
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ekstensi file harus .zip"
        )
        
    try:
        content = await file.read()
        result = process_upload_zip(
            file_name=file.filename,
            file_bytes=content,
            max_size_mb=settings.UPLOAD_MAX_SIZE_MB
        )
        return UploadResponse(
            success=True,
            session_id=result["session_id"],
            message="Ingestion file ZIP berhasil",
            metadata=result
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Terjadi kesalahan internal saat memproses upload."
        )


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_conversations(req: AnalyzeRequest = AnalyzeRequest()):
    """Menjalankan existing NLP pipeline terhadap session yang sudah di-ingest."""
    session_id = req.session_id if req else None
    
    try:
        result = run_analysis_for_session(session_id=session_id)
        return AnalyzeResponse(
            success=True,
            session_id=result["session_id"],
            status="completed",
            message="Analysis completed successfully"
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e).strip("'")
        )
    except Exception as e:
        logger.error(f"Error analysis: {str(e)}")
        return AnalyzeResponse(
            success=False,
            session_id=session_id or "unknown",
            status="failed",
            error=ErrorDetail(
                code="ANALYSIS_FAILED",
                message="Terjadi kesalahan analisis pipeline NLP."
            )
        )
