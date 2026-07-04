import json
import re
from pathlib import Path
from typing import Iterator

import chromadb
from sentence_transformers import SentenceTransformer

from app.config import settings

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DOCS_DIR = DATA_DIR / "docs"
TICKETS_PATH = DATA_DIR / "tickets.jsonl"
COLLECTION_NAME = "cloudbox_support"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    raw_meta, body = match.groups()
    meta = {}
    for line in raw_meta.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, body


def _chunk_doc(doc_id: str, title: str, body: str) -> Iterator[dict]:
    sections = re.split(r"\n(?=## )", body.strip())
    for section in sections:
        section = section.strip()
        if not section:
            continue
        heading_match = re.match(r"^## (.+)", section)
        heading = heading_match.group(1).strip() if heading_match else "Overview"
        content = re.sub(r"^## .+\n", "", section).strip()
        yield {
            "id": f"{doc_id}::{heading}",
            "text": f"{title} — {heading}\n\n{content}",
            "metadata": {"doc_id": doc_id, "source_type": "doc", "title": title},
        }


def load_doc_chunks() -> list[dict]:
    chunks = []
    for path in sorted(DOCS_DIR.glob("*.md")):
        raw = path.read_text()
        meta, body = _parse_frontmatter(raw)
        doc_id = meta.get("doc_id", path.stem)
        title = meta.get("title", path.stem)
        body = re.sub(r"^# .+\n", "", body.strip(), count=1)
        chunks.extend(_chunk_doc(doc_id, title, body))
    return chunks


def load_ticket_chunks() -> list[dict]:
    chunks = []
    if not TICKETS_PATH.exists():
        return chunks
    with TICKETS_PATH.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            ticket = json.loads(line)
            text = (
                f"Past resolved ticket — Q: {ticket['question']}\n"
                f"Resolution: {ticket['resolution_summary']}"
            )
            chunks.append({
                "id": f"ticket::{ticket['id']}",
                "text": text,
                "metadata": {
                    "doc_id": ticket.get("doc_id") or "",
                    "source_type": "ticket",
                    "title": ticket["id"],
                },
            })
    return chunks


def build_index(persist_dir: str | None = None) -> None:
    persist_dir = persist_dir or settings.chroma_dir
    client = chromadb.PersistentClient(path=persist_dir)

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    model = SentenceTransformer(settings.embedding_model)
    chunks = load_doc_chunks() + load_ticket_chunks()

    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True).tolist()

    collection.add(
        ids=[c["id"] for c in chunks],
        documents=texts,
        embeddings=embeddings,
        metadatas=[c["metadata"] for c in chunks],
    )
    print(f"Indexed {len(chunks)} chunks ({len(load_doc_chunks())} doc sections, "
          f"{len(load_ticket_chunks())} tickets) into '{persist_dir}'.")


if __name__ == "__main__":
    build_index()
