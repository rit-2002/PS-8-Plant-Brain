# Plant Brain — AI for Industrial Knowledge Intelligence (PS-08)

A working prototype for the "Unified Asset & Operations Brain" hackathon problem
statement. It ingests heterogeneous plant documents (work orders, safety
procedures, inspection reports, incident records, audit findings), extracts
entities into a knowledge graph, and answers natural-language questions with
source citations via a RAG pipeline.

## What it demonstrates (mapped to the problem statement)

| Problem statement ask | What's built |
|---|---|
| Universal Document Ingestion & Knowledge Graph Agent | `backend/entity_extraction.py` + `backend/knowledge_graph.py` — extracts equipment tags, document refs, regulations, dates, and personnel, then links every document that shares an entity. |
| Expert Knowledge Copilot | `backend/rag_engine.py` + `/api/query` — TF-IDF retrieval over chunked documents, with an extractive, cited answer composer. |
| Lessons Learned & Failure Intelligence | The sample corpus models a real compound-risk pattern (gas pressure sensor + hot work permit, mirroring the PS-01 Vizag Steel Plant scenario) recurring across 5 linked documents — the graph and RAG layer surface that pattern instead of leaving it buried. |
| Quality & Regulatory Compliance Intelligence | Regulatory references (OISD-STD-113, Factory Act sections, DGMS circulars) are extracted as first-class graph entities, so "which documents touch this regulation" is a one-hop graph query. |

## Architecture

```
sample_docs/*.txt
      │
      ▼
entity_extraction.py  ──►  knowledge_graph.py (networkx)
      │                          │
      ▼                          ▼
rag_engine.py (TF-IDF)     /api/graph (vis-network JSON)
      │                          │
      ▼                          ▼
       FastAPI (app.py)  ──►  frontend/index.html
                               (chat UI + graph view)
```

The retrieval and graph layers run fully offline (no external API key
required), so judges can run the demo with no setup beyond `pip install`.
Two clearly marked swap points (`llm_extract_stub` in `entity_extraction.py`
and the docstring in `rag_engine.py`) show exactly where you'd plug in the
Anthropic API for production-grade entity extraction over scanned/OCR'd
documents and for generative (rather than extractive) answer composition.

## Run it

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

Then open `frontend/index.html` directly in a browser (it calls
`http://localhost:8000`). The API also has interactive docs at
`http://localhost:8000/docs`.

## Sample corpus

Five interlinked documents simulating one plant scenario across document
types (`sample_docs/`):
- `work_order_4471.txt` — fan bearing failure, maintenance
- `sop_cob_009.txt` — confined space entry safety procedure with an escalation trigger
- `inspection_ins_2026_0341.txt` — gas sensor calibration drift inspection
- `incident_inc_2025_0118.txt` — near-miss where the escalation condition occurred
- `audit_finding_af_2026_002.txt` — audit tying the system gap together

Ask the copilot "Why does GPS-COB3-07 keep coming up?" to see the cross-document
pattern get surfaced with citations — this is the demo's centerpiece.

## Requirement coverage added for PS-08

- Heterogeneous ingestion: `.txt`, `.md`, `.csv`, `.tsv`, and text-based `.pdf`
  files placed in `sample_docs/` are indexed by `POST /api/ingest`.
- Source traceability: `/api/query` returns citations, confidence scores, and
  source-document URLs. `/api/documents/{doc_id}/source` exposes the evidence.
- Maintenance Intelligence & RCA: `/api/maintenance-intelligence` extracts
  root-cause, trend, backlog, recalibration, failure, recommendation, and
  corrective-action evidence.
- Quality & Regulatory Compliance Intelligence: `/api/compliance-gaps` maps
  non-conformance, compliance gap, risk, regulatory, and corrective-action
  evidence back to source documents.
- Lessons Learned & Failure Intelligence: `/api/lessons-learned` highlights
  repeated near-miss and systemic-risk patterns before similar conditions recur.

Scanned image-only PDFs still require OCR before indexing; text-based PDFs are
handled with `pypdf`.

## Extending for a full submission

- Swap the regex extractor for an LLM-based extractor (Anthropic API,
  structured JSON output) to handle free-text and OCR'd P&IDs/scans.
- Swap the extractive answer composer for a generative one: pass retrieved
  chunks as context to claude-sonnet-4-6 and ask for a grounded, cited answer.
- Add a vector index (e.g. FAISS or pgvector) in place of TF-IDF for semantic
  (not just lexical) retrieval at scale.
- Add OCR (e.g. Tesseract) for scanned inspection forms and P&ID drawings.
