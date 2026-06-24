"""
knowledge_graph.py
Builds a unified knowledge graph linking documents <-> entities, so that
"equipment X appears in work order Y, inspection Z, and incident W" type
relationships become queryable instead of buried in 7-12 separate systems.
"""
import networkx as nx
from typing import List, Dict, Any
from entity_extraction import DocumentEntities


class IndustrialKnowledgeGraph:
    def __init__(self):
        self.graph = nx.Graph()

    def add_document(self, doc_id: str, doc_type: str, title: str, doc_entities: DocumentEntities):
        self.graph.add_node(doc_id, node_type="DOCUMENT", doc_type=doc_type, title=title)

        for ent in doc_entities.entities:
            ent_node_id = f"{ent.label}:{ent.text}"
            if not self.graph.has_node(ent_node_id):
                self.graph.add_node(ent_node_id, node_type=ent.label, label=ent.text)
            self.graph.add_edge(doc_id, ent_node_id, relation="MENTIONS")

    def related_documents(self, entity_text: str) -> List[str]:
        """Find every document mentioning a given entity (equipment tag, doc ref, etc.)"""
        matches = [n for n in self.graph.nodes if n.split(":", 1)[-1].lower() == entity_text.lower()]
        docs = set()
        for m in matches:
            for neighbor in self.graph.neighbors(m):
                if self.graph.nodes[neighbor].get("node_type") == "DOCUMENT":
                    docs.add(neighbor)
        return sorted(docs)

    def shared_entities(self, doc_id_a: str, doc_id_b: str) -> List[str]:
        if doc_id_a not in self.graph or doc_id_b not in self.graph:
            return []
        a_neighbors = set(self.graph.neighbors(doc_id_a))
        b_neighbors = set(self.graph.neighbors(doc_id_b))
        return sorted(a_neighbors & b_neighbors)

    def to_vis_json(self) -> Dict[str, Any]:
        """Export graph in a vis-network-friendly format for the frontend."""
        color_map = {
            "DOCUMENT": "#2563eb",
            "EQUIPMENT_TAG": "#dc2626",
            "DOC_REF": "#16a34a",
            "REGULATION": "#9333ea",
            "DATE": "#6b7280",
            "PERSON": "#ea580c",
        }
        nodes = []
        for n, data in self.graph.nodes(data=True):
            ntype = data.get("node_type", "DOCUMENT")
            label = data.get("title") or data.get("label") or n
            nodes.append({
                "id": n,
                "label": label if len(label) < 28 else label[:25] + "...",
                "group": ntype,
                "color": color_map.get(ntype, "#999999"),
                "title": data.get("title", n),
            })
        edges = [{"from": a, "to": b} for a, b in self.graph.edges()]
        return {"nodes": nodes, "edges": edges}

    def stats(self) -> Dict[str, int]:
        doc_count = sum(1 for _, d in self.graph.nodes(data=True) if d.get("node_type") == "DOCUMENT")
        ent_count = self.graph.number_of_nodes() - doc_count
        return {
            "documents": doc_count,
            "entities": ent_count,
            "links": self.graph.number_of_edges(),
        }
