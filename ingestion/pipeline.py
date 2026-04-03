from ingestion.chunker import chunk_text
from ingestion.embedder import embed_texts
from ingestion.store import upsert_chunks
from ingestion.sources.pdf import extract_text_from_pdf
from ingestion.sources.text import extract_text_from_raw
from ingestion.sources.github import fetch_github_readme
from ingestion.sources.github import fetch_all_github_projects

async def ingest_document(user_id: str, source_type: str, content, metadata: dict):
    """
    source_type: "pdf" | "text" | "github_url" | "github_profile"
    content: bytes (for pdf) | str (for text/github_url/github_profile)
    """
    if source_type == "pdf":
        text = extract_text_from_pdf(content)
    elif source_type == "text":
        text = extract_text_from_raw(content)
    elif source_type == "github_url":
        text = await fetch_github_readme(content)
    elif source_type == "github_profile":
        text = await fetch_all_github_projects(content)
    else:
        raise ValueError(f"Unknown source type: {source_type}")

    chunks = chunk_text(text)
    vectors = embed_texts(chunks)
    upsert_chunks(user_id, chunks, vectors, metadata)
    return len(chunks)