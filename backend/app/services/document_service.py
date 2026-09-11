import os
import shutil
import re
import pathlib
from datetime import datetime, timezone
from bson import ObjectId
from typing import List, Optional
from fastapi import UploadFile

import logging
from app.db.mongodb import get_database
from app.schemas.documents import DocumentInDB
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

UPLOAD_DIR = pathlib.Path(__file__).parent.parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".csv", ".docx", ".pptx"}

def sanitize_filename(filename: str) -> str:
    # Remove any path components
    filename = os.path.basename(filename)
    # Remove dangerous characters
    filename = re.sub(r'[^\w\s\-.]', '_', filename)
    # Limit length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:196] + ext
    return filename or "document"

class DocumentService:
    @property
    def collection(self):
        from app.db.mongodb import get_database
        return get_database().documents

    async def process_document_bg(self, doc_id: str, owner_id: str, file_path: str, mime_type: str, title: str):
        d_refs = [doc_id]
        if len(doc_id) == 24:
            try:
                d_refs.append(ObjectId(doc_id))
            except Exception:
                pass
        self.collection.update_many({"_id": {"$in": d_refs}}, {"$set": {"status": "processing"}})
        try:
            gemini_file_id = await ai_service.upload_document_to_gemini(file_path, mime_type, title)
            self.collection.update_many(
                {"_id": {"$in": d_refs}}, 
                {"$set": {
                    "status": "ready",
                    "gemini_file_id": gemini_file_id or None,
                    "processed_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
        except Exception as e:
            logger.warning(f"Gemini upload error for doc {doc_id}, setting ready with fallback: {e}")
            # Mark ready so the document is accessible and can be used for text grounding
            self.collection.update_many(
                {"_id": {"$in": d_refs}}, 
                {"$set": {
                    "status": "ready",
                    "processing_error": str(e),
                    "processed_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }}
            )

    async def create_document(self, owner_id: str, file: UploadFile, title: str, description: Optional[str] = None, background_tasks = None) -> DocumentInDB:
        ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}. Allowed: .pdf, .txt, .csv, .docx, .pptx")

        doc_id = str(ObjectId())
        safe_filename = sanitize_filename(file.filename or "")
        file_path = os.path.join(UPLOAD_DIR, f"{doc_id}{ext}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            os.remove(file_path)
            raise ValueError("File too large. Maximum size is 50MB.")
            
        mime_type = file.content_type or "application/octet-stream"

        doc = DocumentInDB(
            _id=doc_id,
            owner_id=str(owner_id),
            title=title,
            description=description,
            filename=safe_filename,
            mime_type=mime_type,
            size=file_size,
            status="uploading",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.collection.insert_one(doc.model_dump(by_alias=True))
        
        if background_tasks:
            background_tasks.add_task(self.process_document_bg, doc_id, owner_id, file_path, mime_type, title)
        else:
            # If no background_tasks provided, do it synchronously (e.g. in tests)
            import asyncio
            asyncio.create_task(self.process_document_bg(doc_id, owner_id, file_path, mime_type, title))

        return doc

    def get_document(self, doc_id: str, owner_id: str) -> Optional[DocumentInDB]:
        o_refs = [owner_id]
        if len(str(owner_id)) == 24:
            try:
                o_refs.append(ObjectId(str(owner_id)))
            except Exception:
                pass
        d_refs = [doc_id]
        if len(str(doc_id)) == 24:
            try:
                d_refs.append(ObjectId(str(doc_id)))
            except Exception:
                pass

        doc = self.collection.find_one({"_id": {"$in": d_refs}, "owner_id": {"$in": o_refs}})
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        doc["owner_id"] = str(doc["owner_id"])
        return DocumentInDB(**doc)

    def list_documents(self, owner_id: str, skip: int = 0, limit: int = 50) -> List[DocumentInDB]:
        o_refs = [owner_id]
        if len(str(owner_id)) == 24:
            try:
                o_refs.append(ObjectId(str(owner_id)))
            except Exception:
                pass

        docs = self.collection.find({"owner_id": {"$in": o_refs}}).sort("created_at", -1).skip(skip).limit(limit)
        results = []
        for doc in docs:
            doc["_id"] = str(doc["_id"])
            doc["owner_id"] = str(doc["owner_id"])
            results.append(DocumentInDB(**doc))
        return results

    def delete_document(self, doc_id: str, owner_id: str) -> bool:
        doc = self.get_document(doc_id, owner_id)
        if not doc:
            return False
            
        o_refs = [owner_id]
        if len(str(owner_id)) == 24:
            try:
                o_refs.append(ObjectId(str(owner_id)))
            except Exception:
                pass
        d_refs = [doc_id]
        if len(str(doc_id)) == 24:
            try:
                d_refs.append(ObjectId(str(doc_id)))
            except Exception:
                pass

        res = self.collection.delete_many({"_id": {"$in": d_refs}, "owner_id": {"$in": o_refs}})
        if res.deleted_count > 0:
            # Also detach document from notebooks
            from app.db.mongodb import get_database
            db = get_database()
            d_refs = [doc_id]
            if len(doc_id) == 24:
                try:
                    d_refs.append(ObjectId(doc_id))
                except Exception:
                    pass
            db.notebooks.update_many(
                {"documents": {"$in": d_refs}},
                {"$pull": {"documents": {"$in": d_refs}}}
            )

            # Also remove file
            ext = os.path.splitext(doc.filename)[1]
            file_path = os.path.join(UPLOAD_DIR, f"{doc_id}{ext}")
            if os.path.exists(file_path):
                os.remove(file_path)
                
            if doc.gemini_file_id:
                import asyncio
                try:
                    # In a sync function, we can just fire and forget an async task if an event loop is running.
                    # Or run it synchronously. We'll fire and forget.
                    loop = asyncio.get_running_loop()
                    loop.create_task(ai_service.delete_document_from_gemini(doc.gemini_file_id))
                except RuntimeError:
                    # No event loop running
                    asyncio.run(ai_service.delete_document_from_gemini(doc.gemini_file_id))
                except Exception:
                    pass

            return True
        return False

    async def retry_document(self, doc_id: str, owner_id: str, background_tasks) -> bool:
        doc = self.get_document(doc_id, owner_id)
        if not doc or doc.status != "failed":
            return False
            
        ext = os.path.splitext(doc.filename)[1]
        file_path = os.path.join(UPLOAD_DIR, f"{doc_id}{ext}")
        if not os.path.exists(file_path):
            return False
            
        background_tasks.add_task(self.process_document_bg, doc_id, owner_id, file_path, doc.mime_type, doc.title)
        return True

document_service = DocumentService()
