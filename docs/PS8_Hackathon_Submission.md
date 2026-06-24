# Plant Brain: AI for Industrial Knowledge Intelligence

## Hackathon Problem Statement

Problem Statement: PS-08 - AI for Industrial Knowledge Intelligence: Unified Asset & Operations Brain

Theme: Industrial Intelligence, Document Management, Knowledge Engineering, Quality, Compliance, and Operations.

Plant Brain is a working prototype that turns disconnected industrial records into a unified knowledge layer. It ingests plant documents, extracts operational entities, builds a knowledge graph, and answers natural-language questions with citations and confidence scores.

## Executive Summary

Asset-intensive industries lose time, safety context, and engineering knowledge because plant information is spread across work orders, operating procedures, inspection records, incident reports, audit findings, and regulatory references.

Plant Brain demonstrates a practical solution: an offline-first Industrial Knowledge Intelligence platform that makes this fragmented corpus queryable and actionable for maintenance teams, safety teams, quality auditors, and field technicians.

The prototype currently demonstrates five core capabilities:

- Universal document ingestion for text, Markdown, CSV, TSV, and text-based PDF files.
- Entity extraction for equipment tags, document references, regulations, dates, and personnel.
- Knowledge graph linkage across documents that share the same industrial entities.
- RAG-style expert copilot answers with source citations, confidence scores, and direct source links.
- Intelligence endpoints for compliance gaps, maintenance/root-cause analysis, and lessons learned.

## Problem Fit

PS-08 asks participants to build an AI-powered Industrial Knowledge Intelligence platform that can ingest heterogeneous industrial documents and make their collective intelligence queryable, actionable, and continuously updated at the point of need.

Plant Brain directly targets this challenge by connecting five representative document classes:

- Maintenance work orders.
- Safety operating procedures.
- Inspection reports.
- Near-miss and incident records.
- Audit and compliance findings.

The sample corpus models a realistic cross-document risk pattern in Coke Oven Battery 3: gas pressure sensor drift, hot work permits, SCADA/PTW integration gaps, inspection findings, procedural escalation triggers, and audit non-conformance evidence.

## Architecture

Document corpus:

sample_docs/*.txt, *.md, *.csv, *.tsv, *.pdf

Processing pipeline:

1. FastAPI ingestion reads supported files from sample_docs.
2. Entity extraction identifies equipment tags, document references, dates, people, and regulatory references.
3. NetworkX knowledge graph links documents to entities and exposes graph JSON.
4. TF-IDF retrieval indexes chunked document text for natural-language search.
5. Extractive answer composer returns grounded answers with confidence and citations.
6. Frontend shows graph visualization, expert copilot, documents, and intelligence cards.

Runtime components:

- backend/app.py - FastAPI API and ingestion orchestration.
- backend/entity_extraction.py - industrial entity extraction.
- backend/knowledge_graph.py - unified graph model and vis-network export.
- backend/rag_engine.py - retrieval and cited answer composition.
- frontend/index.html - interactive dashboard, graph, copilot, and intelligence views.
- sample_docs/ - demo industrial document corpus.

## Requirement Mapping

Universal Document Ingestion and Knowledge Graph Agent:

- Completed in backend/app.py, backend/entity_extraction.py, and backend/knowledge_graph.py.
- Supports .txt, .md, .csv, .tsv, and text-based .pdf ingestion.
- Extracts equipment tags, document references, regulatory references, personnel, and dates.
- Builds a graph linking every document to the entities it mentions.

Expert Knowledge Copilot:

- Completed in backend/rag_engine.py and POST /api/query.
- Answers operational, maintenance, safety, and compliance questions.
- Returns source citations, confidence scores, and source-document links.
- Frontend provides a chat UI suitable for desktop and mobile screen widths.

Maintenance Intelligence and RCA Agent:

- Implemented through GET /api/maintenance-intelligence.
- Extracts evidence related to root cause, repeated failures, calibration drift, maintenance backlog, recommendations, and corrective actions.
- Demonstrates RCA support using fan bearing failures, PM backlog, and sensor drift evidence.

Quality and Regulatory Compliance Intelligence:

- Implemented through GET /api/compliance-gaps.
- Maps non-conformance, risk, regulatory references, and corrective actions to source documents.
- Highlights SCADA/PTW integration gaps linked to OISD, Factory Act, and DGMS references.

Lessons Learned and Failure Intelligence Engine:

- Implemented through GET /api/lessons-learned.
- Surfaces repeated near-miss and systemic-risk patterns.
- Demonstrates proactive warnings for compound risk: elevated gas pressure plus active hot work or confined-space permits.

## Key Features

- Offline-first demo: no external LLM API key required for judging.
- Knowledge graph visualization with document, equipment, regulation, date, and personnel nodes.
- Natural-language copilot with citations.
- Confidence score per answer.
- Direct source traceability through /api/documents/{doc_id}/source.
- Re-ingestion endpoint to refresh the corpus after new files are added.
- Dedicated intelligence panels for compliance, maintenance RCA, and lessons learned.
- Clear production swap points for LLM extraction, OCR, semantic vector retrieval, and generative answer composition.

## API Endpoints

- GET / - API status message.
- POST /api/ingest - Re-index the corpus.
- GET /api/stats - Document, entity, and graph-link counts.
- GET /api/graph - Knowledge graph JSON for visualization.
- GET /api/documents - Ingested document list with source URLs.
- GET /api/documents/{doc_id}/source - Source text for cited evidence.
- GET /api/related/{tag} - Documents related to a tag, document reference, or regulation.
- POST /api/query - RAG-style question answering with citations and confidence.
- GET /api/compliance-gaps - Compliance and audit evidence extraction.
- GET /api/maintenance-intelligence - Maintenance and RCA evidence extraction.
- GET /api/lessons-learned - Repeated-risk and failure-learning evidence extraction.

## Demo Script

1. Start backend:

cd backend
python -m uvicorn app:app --host 127.0.0.1 --port 8000

2. Start frontend:

cd frontend
python -m http.server 5500 --bind 127.0.0.1

3. Open:

http://127.0.0.1:5500/index.html

4. Show the dashboard:

- Document, entity, and link counts.
- Unified knowledge graph.
- Ingested source documents.
- Compliance, maintenance RCA, and lessons-learned intelligence panels.

5. Ask these demo questions:

- Why does GPS-COB3-07 keep coming up?
- What compliance gap was flagged in the audit?
- What caused the fan bearing failure?
- What is the escalation trigger in SOP-COB-009?

6. Click citation chips to show direct source evidence.

## Current Demo Corpus

- work_order_4471.txt - fan bearing failure and maintenance root cause.
- sop_cob_009.txt - confined-space safety procedure and escalation trigger.
- inspection_ins_2026_0341.txt - gas pressure sensor calibration drift and SCADA/PTW gap.
- incident_inc_2025_0118.txt - near-miss involving gas pressure spike and hot work permit.
- audit_finding_af_2026_002.txt - audit finding tying the system gap together.

## Evaluation Alignment

Innovation:

- Combines RAG, graph intelligence, source traceability, and workflow-specific agents in one prototype.

Business Impact:

- Reduces time spent searching across disconnected plant systems.
- Improves maintenance decision-making and compliance readiness.
- Preserves operational knowledge as experienced engineers retire.

Technical Excellence:

- Clean FastAPI backend, reusable extraction layer, graph model, retrieval engine, and frontend dashboard.
- Works offline for reliable judging.

Scalability:

- Supports additional files through a simple corpus folder and re-ingestion endpoint.
- Architecture allows replacement of TF-IDF with vector search and rule extraction with LLM/OCR pipelines.

User Experience:

- Interactive graph, chat UI, source citations, and focused intelligence panels.
- Designed for fast cross-functional knowledge discovery.

## Known Limitations and Production Roadmap

Current limitations:

- Scanned image-only PDFs need OCR before text can be indexed.
- Entity extraction is rule-based for offline demo reliability.
- Retrieval is lexical TF-IDF rather than semantic vector search.
- Answer generation is extractive, not generative.

Production roadmap:

- Add OCR for scanned forms, P&IDs, drawings, and image-heavy PDFs.
- Add LLM-based structured extraction for complex unstructured documents.
- Add a vector database such as FAISS, pgvector, or OpenSearch for semantic retrieval.
- Add role-based access control and audit logs for enterprise deployment.
- Add connectors to QMS, CMMS/EAM, SCADA historian, email archives, and document management systems.
- Add notification workflows for recurring risk patterns and compliance gaps.

## Submission Checklist

- Working prototype: complete.
- Architecture diagram: included in this PDF.
- Problem-statement requirement mapping: complete.
- Demo flow: complete.
- Source citations and explainability: complete.
- Future roadmap: complete.

