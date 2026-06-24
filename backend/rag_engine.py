"""
rag_engine.py
TF-IDF based retrieval over the document corpus (chunk-level), plus an
extractive answer composer with source citations. This runs fully offline
(no external LLM API key required) so the hackathon demo is self-contained.

Swap point for production: replace `compose_answer` with a call to the
Anthropic API (claude-sonnet-4-6), passing the retrieved chunks as context
and asking for a grounded, cited answer. The retrieval layer below would
not need to change.
"""
import re
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def chunk_text(doc_id: str, text: str, chunk_size: int = 350) -> List[Dict]:
    """Split into overlapping word-based chunks, preserving paragraph boundaries loosely."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    buf = ""
    idx = 0
    for para in paragraphs:
        if len(buf.split()) + len(para.split()) > chunk_size and buf:
            chunks.append({"chunk_id": f"{doc_id}#{idx}", "doc_id": doc_id, "text": buf.strip()})
            idx += 1
            buf = para
        else:
            buf = (buf + "\n" + para).strip()
    if buf:
        chunks.append({"chunk_id": f"{doc_id}#{idx}", "doc_id": doc_id, "text": buf.strip()})
    return chunks


class RagEngine:
    def __init__(self):
        self.chunks: List[Dict] = []
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = None

    def index_documents(self, documents: List[Dict]):
        """documents: list of {doc_id, title, doc_type, text}"""
        self.chunks = []
        for doc in documents:
            self.chunks.extend(chunk_text(doc["doc_id"], doc["text"]))
            for c in self.chunks:
                if c["doc_id"] == doc["doc_id"]:
                    c["title"] = doc["title"]
                    c["doc_type"] = doc["doc_type"]
        if self.chunks:
            self._matrix = self.vectorizer.fit_transform([c["text"] for c in self.chunks])

    def retrieve(self, query: str, top_k: int = 4) -> List[Dict]:
        if self._matrix is None or not self.chunks:
            return []
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self._matrix)[0]
        ranked_idx = sims.argsort()[::-1][:top_k]
        results = []
        for i in ranked_idx:
            if sims[i] <= 0:
                continue
            c = dict(self.chunks[i])
            c["score"] = float(sims[i])
            results.append(c)
        return results

    def compose_answer(self, query: str, retrieved: List[Dict]) -> Dict:
        """
        Extractive composer: pulls the most relevant sentences from each
        retrieved chunk and stitches them into an answer with citations.
        Not an LLM - a transparent, offline stand-in that still demonstrates
        grounded, cited retrieval (the core RAG behaviour being judged).
        """
        if not retrieved:
            return {
                "answer": "No relevant information found in the indexed document corpus for this query.",
                "confidence": 0.0,
                "citations": [],
            }

        query_terms = set(re.findall(r"\w+", query.lower()))
        answer_lines = []
        citations = []
        for c in retrieved:
            sentences = re.split(r"(?<=[.!?])\s+", c["text"])
            best_sentence, best_overlap = None, -1
            for s in sentences:
                terms = set(re.findall(r"\w+", s.lower()))
                overlap = len(terms & query_terms)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_sentence = s
            if best_sentence:
                answer_lines.append(f"- {best_sentence.strip()} [{c['title']}]")
                citations.append({
                    "doc_id": c["doc_id"],
                    "title": c["title"],
                    "doc_type": c["doc_type"],
                    "score": round(c["score"], 3),
                    "source_url": f"/api/documents/{c['doc_id']}/source",
                })
        answer = "\n".join(answer_lines)
        confidence = max((c["score"] for c in retrieved), default=0.0)
        return {"answer": answer, "confidence": round(float(confidence), 3), "citations": citations}
