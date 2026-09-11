from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status, UploadFile, File, Form, Request, Query
from typing import List, Optional, Dict, Any
from app.core.dependencies import get_current_user
from app.schemas.documents import DocumentResponse
from app.services.document_service import document_service

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

@router.post("", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    import os
    
    # Validate file size (50MB max)
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB.")
    await file.seek(0)  # Reset after reading
    
    # Validate extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".pdf", ".txt", ".csv", ".docx", ".pptx"}:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Allowed: .pdf, .txt, .csv, .docx, .pptx")

    try:
        doc = await document_service.create_document(
            owner_id=current_user["_id"],
            file=file,
            title=title,
            description=description,
            background_tasks=background_tasks
        )
        return doc
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=dict)
def list_documents(
    skip: int = 0, limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    docs = document_service.list_documents(current_user["_id"], skip, limit)
    return {"documents": docs, "total": len(docs)}

@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    doc = document_service.get_document(doc_id, current_user["_id"])
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.get("/{doc_id}/content")
def get_document_content(
    doc_id: str,
    request: Request,
    token: Optional[str] = Query(None),
):
    from app.core.security import decode_access_token
    auth_token = None
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        auth_token = auth_header[7:].strip()
    elif token:
        auth_token = token.strip()
    
    if not auth_token:
        raise HTTPException(status_code=401, detail="Authentication required to view document")

    payload = decode_access_token(auth_token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = str(payload["sub"])
    doc = document_service.get_document(doc_id, user_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or access denied")
    
    import os
    import pathlib
    from fastapi.responses import FileResponse
    ext = os.path.splitext(doc.filename)[1] if doc.filename else ""
    
    upload_dir = (pathlib.Path(__file__).parent.parent.parent / "data" / "uploads").resolve()
    file_path = (upload_dir / f"{doc_id}{ext}").resolve()
    
    if not file_path.exists():
        matching = list(upload_dir.glob(f"{doc_id}*"))
        if matching:
            file_path = matching[0]

    # Security check: Ensure the resolved path is within the UPLOAD_DIR
    if not str(file_path).startswith(str(upload_dir)):
        raise HTTPException(status_code=403, detail="Invalid file path")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File content not found on server")
        
    return FileResponse(
        str(file_path),
        media_type=doc.mime_type or "application/pdf",
        filename=doc.filename,
        content_disposition_type="inline"
    )

@router.delete("/{doc_id}")
def delete_document(doc_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    success = document_service.delete_document(doc_id, current_user["_id"])
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "success"}

@router.post("/{doc_id}/retry")
async def retry_document(doc_id: str, background_tasks: BackgroundTasks, current_user: Dict[str, Any] = Depends(get_current_user)):
    success = await document_service.retry_document(doc_id, current_user["_id"], background_tasks)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or not in failed state")
    return {"status": "processing"}
