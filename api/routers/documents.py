from fastapi import APIRouter, UploadFile, File, Form, Depends, BackgroundTasks, HTTPException
from api.deps import get_current_user
from api.db import create_document, list_documents, delete_document, get_document, update_github_username
from ingestion.pipeline import ingest_document
from ingestion.store import delete_document_chunks
import asyncio
import uuid
from datetime import datetime, timezone

router = APIRouter()

@router.post("/users/{user_id}/documents")
async def upload_document(
    user_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(None),
    github_url: str = Form(None),
    github_username: str = Form(None),
    raw_text: str = Form(None),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    doc_id = str(uuid.uuid4())
    uploaded_at = datetime.now(timezone.utc).isoformat()
    metadata = {"user_id": user_id, "doc_id": doc_id}

    if file:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")
        if file.filename.endswith(".pdf"):
            source_type = "pdf"
        elif file.filename.endswith(".zip"):
            source_type = "linkedin"
        else:
            source_type = "text"
        filename = file.filename
        metadata["filename"] = filename
        create_document(user_id, doc_id, filename, source_type, uploaded_at)
        background_tasks.add_task(asyncio.run, ingest_document(user_id, source_type, content, metadata))

    elif github_url:
        metadata["filename"] = github_url
        create_document(user_id, doc_id, github_url, "github_url", uploaded_at)
        background_tasks.add_task(asyncio.run, ingest_document(user_id, "github_url", github_url, metadata))

    elif github_username:
        update_github_username(user_id, github_username)
        metadata["filename"] = github_username
        create_document(user_id, doc_id, github_username, "github_profile", uploaded_at)
        background_tasks.add_task(asyncio.run, ingest_document(user_id, "github_profile", github_username, metadata))

    elif raw_text:
        if len(raw_text) > 50_000:
            raise HTTPException(status_code=400, detail="Text too large. Maximum is 50,000 characters.")
        metadata["filename"] = "raw_text"
        create_document(user_id, doc_id, "raw_text", "text", uploaded_at)
        background_tasks.add_task(asyncio.run, ingest_document(user_id, "text", raw_text, metadata))

    else:
        raise HTTPException(status_code=400, detail="No content provided")

    return {"doc_id": doc_id, "status": "processing"}


@router.get("/users/{user_id}/documents")
def get_documents(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    docs = list_documents(user_id)
    return {"documents": sorted(docs, key=lambda d: d.get("uploaded_at", ""), reverse=True)}


@router.get("/users/{user_id}/documents/{doc_id}/status")
def get_document_status(user_id: str, doc_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    doc = get_document(user_id, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"doc_id": doc_id, "status": doc["status"]}


@router.delete("/users/{user_id}/documents/{doc_id}")
def remove_document(user_id: str, doc_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    delete_document_chunks(user_id, doc_id)
    delete_document(user_id, doc_id)
    return {"deleted": doc_id}
