"""
app.py
FastAPI backend for the Industrial Knowledge Intelligence prototype (PS8).

Endpoints:
  POST /api/ingest        -> (re)load and index the sample document corpus
  GET  /api/stats         -> corpus / graph stats
  GET  /api/graph         -> knowledge graph in vis-network JSON format
  POST /api/query         -> RAG query: {"question": "..."} -> answer + citations
  GET  /api/related/{tag} -> documents related to an equipment tag / doc ref
  GET  /api/documents     -> list ingested documents with metadata

Run with: uvicorn app:app --reload --port 8000
"""
import os
import csv
import re
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from entity_extraction import extract_entities
from knowledge_graph import IndustrialKnowledgeGraph
from rag_engine import RagEngine

DOCS_DIR = Path(__file__).resolve().parent.parent / "sample_docs"
SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".tsv", ".pdf"}

app = FastAPI(title="Industrial Knowledge Intelligence API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

kg = IndustrialKnowledgeGraph()
rag = RagEngine()
DOC_STORE = {}  # doc_id -> {title, doc_type, text}

DOC_TYPE_MAP = {
    "work_order": "Maintenance Work Order",
    "sop": "Safety Procedure",
    "inspection": "Inspection Report",
    "incident": "Incident / Near-Miss Report",
    "audit": "Audit Finding",
    "pid": "Engineering Drawing / P&ID",
    "pandid": "Engineering Drawing / P&ID",
    "manual": "OEM / Operating Manual",
    "quality": "Quality Record",
    "email": "Email Archive",
}


def infer_doc_type(filename: str) -> str:
    for key, label in DOC_TYPE_MAP.items():
        if key in filename:
            return label
    return "General Document"


def title_from_text(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:80]
    return "Untitled Document"


def load_document_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")
    if suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = csv.reader(f, delimiter=delimiter)
            return "\n".join(" | ".join(cell.strip() for cell in row) for row in rows)
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF ingestion requires pypdf. Install it with `pip install pypdf`.") from exc
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    raise ValueError(f"Unsupported document type: {path.suffix}")


def evidence_items(keywords):
    items = []
    pattern = re.compile("|".join(re.escape(k) for k in keywords), re.IGNORECASE)
    for doc_id, doc in DOC_STORE.items():
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", doc["text"]) if p.strip()]
        for para in paragraphs:
            if pattern.search(para):
                items.append({
                    "doc_id": doc_id,
                    "title": doc["title"],
                    "doc_type": doc["doc_type"],
                    "evidence": para[:700],
                    "source_url": f"/api/documents/{doc_id}/source",
                })
                break
    return items


class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 4


def ingest_corpus():
    DOC_STORE.clear()
    kg.graph.clear()
    documents = []

    paths = sorted(p for p in DOCS_DIR.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS)
    for path in paths:
        doc_id = path.stem
        text = load_document_text(path)
        doc_type = infer_doc_type(doc_id)
        title = title_from_text(text)

        DOC_STORE[doc_id] = {
            "title": title,
            "doc_type": doc_type,
            "text": text,
            "source_name": path.name,
            "source_ext": path.suffix.lower(),
        }
        documents.append({"doc_id": doc_id, "title": title, "doc_type": doc_type, "text": text})

        ents = extract_entities(doc_id, text)
        kg.add_document(doc_id, doc_type, title, ents)

    rag.index_documents(documents)
    return {"ingested": len(documents)}


@app.on_event("startup")
def startup_event():
    ingest_corpus()


@app.post("/api/ingest")
def api_ingest():
    result = ingest_corpus()
    return {"status": "ok", **result, "stats": kg.stats()}


@app.get("/api/stats")
def api_stats():
    return kg.stats()


@app.get("/api/graph")
def api_graph():
    return kg.to_vis_json()


@app.get("/api/documents")
def api_documents():
    return [
        {
            "doc_id": doc_id,
            "title": d["title"],
            "doc_type": d["doc_type"],
            "source_name": d["source_name"],
            "source_url": f"/api/documents/{doc_id}/source",
        }
        for doc_id, d in DOC_STORE.items()
    ]


@app.get("/api/documents/{doc_id}/source", response_class=PlainTextResponse)
def api_document_source(doc_id: str):
    if doc_id not in DOC_STORE:
        raise HTTPException(404, "document not found")
    return DOC_STORE[doc_id]["text"]


@app.get("/api/related/{tag}")
def api_related(tag: str):
    docs = kg.related_documents(tag)
    return [
        {"doc_id": doc_id, "title": DOC_STORE.get(doc_id, {}).get("title", doc_id)}
        for doc_id in docs
    ]


@app.post("/api/query")
def api_query(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(400, "question must not be empty")
    retrieved = rag.retrieve(req.question, top_k=req.top_k or 4)
    result = rag.compose_answer(req.question, retrieved)
    return result


@app.get("/api/compliance-gaps")
def api_compliance_gaps():
    items = evidence_items([
        "regulatory reference",
        "regulatory basis",
        "non-conformance",
        "compliance",
        "gap",
        "corrective action",
        "risk rating",
    ])
    return {
        "summary": "Compliance intelligence flags unresolved SCADA/PTW cross-system alerting and maps it to OISD, Factory Act, and DGMS evidence.",
        "items": items,
    }


@app.get("/api/maintenance-intelligence")
def api_maintenance_intelligence():
    items = evidence_items([
        "root cause",
        "recommendation",
        "failure",
        "bearing",
        "recalibration",
        "trend",
        "backlog",
        "corrective action",
    ])
    return {
        "summary": "Maintenance intelligence links fan bearing failures, PM backlog, sensor drift, and required corrective actions for RCA support.",
        "items": items,
    }


@app.get("/api/lessons-learned")
def api_lessons_learned():
    items = evidence_items([
        "lesson learned",
        "near-miss",
        "systemic",
        "pattern",
        "compound condition",
        "manual vigilance",
        "stop-work",
    ])
    return {
        "summary": "Lessons learned intelligence surfaces repeated compound-risk conditions before they recur in operations.",
        "items": items,
    }


@app.get("/")
def root():
    return {"message": "Industrial Knowledge Intelligence API. See /docs for the interactive API explorer."}
