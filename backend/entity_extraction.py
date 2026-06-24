"""
entity_extraction.py
Extracts structured entities from heterogeneous industrial documents:
equipment tags, document IDs, regulatory references, personnel, dates.

This is a regex/rule-based extractor designed to run with zero external
API dependency, so the hackathon demo works fully offline. In a production
system this layer would be augmented with an LLM-based extractor (e.g. an
Anthropic API call with a structured-output prompt) for unstructured prose
and OCR'd scans - the interface below is written so that swap is a drop-in
change (see `llm_extract_stub`).
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class ExtractedEntity:
    text: str
    label: str  # EQUIPMENT_TAG, DOC_REF, REGULATION, PERSON, DATE, ORG
    span: tuple


@dataclass
class DocumentEntities:
    doc_id: str
    entities: List[ExtractedEntity] = field(default_factory=list)


# --- Patterns -----------------------------------------------------------

EQUIPMENT_TAG_RE = re.compile(
    r"\b(?:[A-Z0-9]{2,8}-){1,4}[A-Z0-9]{1,8}\b"
)

DOC_REF_RE = re.compile(
    r"\b(?:WO|INC|INS|SOP|AF|NC|PTW|HWP)-[\w-]+\b"
)

REGULATION_RE = re.compile(
    r"\b(?:OISD-STD-\d+|Factory Act 1948(?: Section \d+)?|DGMS Circular [\d/]+|"
    r"PESO\b|BICSI\b|TIA-942\b)\b"
)

DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")

PERSON_RE = re.compile(
    r"\b(?:By|Inspector|Auditor|Owner|Engineer|In-Charge)[:\s]+([A-Z]\.?\s?[A-Z][a-z]+(?:\s[A-Z][a-z]+)?)"
)


def extract_entities(doc_id: str, text: str) -> DocumentEntities:
    result = DocumentEntities(doc_id=doc_id)

    seen = set()

    for m in EQUIPMENT_TAG_RE.finditer(text):
        tok = m.group()
        # filter false positives that are actually doc refs / regs
        if DOC_REF_RE.fullmatch(tok) or DATE_RE.fullmatch(tok) or tok.replace("-", "").isdigit():
            continue
        key = ("EQUIPMENT_TAG", tok)
        if key not in seen:
            seen.add(key)
            result.entities.append(ExtractedEntity(tok, "EQUIPMENT_TAG", m.span()))

    for m in DOC_REF_RE.finditer(text):
        tok = m.group()
        key = ("DOC_REF", tok)
        if key not in seen:
            seen.add(key)
            result.entities.append(ExtractedEntity(tok, "DOC_REF", m.span()))

    for m in REGULATION_RE.finditer(text):
        tok = m.group()
        key = ("REGULATION", tok)
        if key not in seen:
            seen.add(key)
            result.entities.append(ExtractedEntity(tok, "REGULATION", m.span()))

    for m in DATE_RE.finditer(text):
        tok = m.group()
        key = ("DATE", tok)
        if key not in seen:
            seen.add(key)
            result.entities.append(ExtractedEntity(tok, "DATE", m.span()))

    for m in PERSON_RE.finditer(text):
        tok = m.group(1)
        key = ("PERSON", tok)
        if key not in seen:
            seen.add(key)
            result.entities.append(ExtractedEntity(tok, "PERSON", m.span()))

    return result


def llm_extract_stub(doc_id: str, text: str) -> Dict:
    """
    Placeholder showing where an LLM-based extraction call would plug in
    for unstructured/scanned content (e.g. P&IDs after OCR). Not called
    in the offline demo. Would call the Anthropic API with a structured
    JSON-only extraction prompt and parse the result.
    """
    raise NotImplementedError(
        "Wire this to an Anthropic API call with response_format=json "
        "for production-grade extraction on free-text / OCR'd content."
    )
