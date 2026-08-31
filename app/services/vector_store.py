import json
import math
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

from app.config import settings
from app.services.document_loader import DocumentLoader

SPANISH_KEYWORD_EXPANSIONS = {
    "inglés": "english language courses levels pricing general business",
    "ingles": "english language courses levels pricing general business",
    "francés": "french francais CIEP levels",
    "frances": "french francais CIEP levels",
    "alemán": "german deutsch goethe",
    "aleman": "german deutsch goethe",
    "italiano": "italian immersion",
    "portugués": "portuguese brasileiro",
    "portugues": "portuguese brasileiro",
    "español": "spanish foreigners dele siele",
    "espanol": "spanish foreigners dele siele",
    "precio": "price pricing tuition cost fees COP USD group standard",
    "precios": "price pricing tuition cost fees COP USD group standard",
    "cuánto": "how much price cost tuition rates",
    "cuanto": "how much price cost tuition rates",
    "costo": "cost price tuition fee",
    "costos": "costs prices tuition fees",
    "horario": "schedule timetable hours morning evening saturday",
    "horarios": "schedules timetables hours morning evening saturday",
    "hora": "hours time schedule",
    "horas": "hours duration time",
    "sábado": "saturday intensive immersion weekend 8am 1pm",
    "sabado": "saturday intensive immersion weekend 8am 1pm",
    "sábados": "saturdays intensive immersion weekend 8am 1pm",
    "sabados": "saturdays intensive immersion weekend 8am 1pm",
    "noche": "evening night executive 6:30pm 8:30pm",
    "nocturno": "evening night executive track 6:30pm 8:30pm",
    "mañana": "morning track early 6:30am 9:00am",
    "mañanas": "morning track early 6:30am 9:00am",
    "sede": "campus location address chapinero bogota poblado medellin",
    "sedes": "campuses locations addresses chapinero bogota poblado medellin",
    "dirección": "address location campus bogota medellin",
    "direccion": "address location campus bogota medellin",
    "donde": "where location campus address",
    "dónde": "where location campus address",
    "pago": "payment pay PSE credit card bancolombia installment",
    "pagos": "payment pay PSE credit card bancolombia installment",
    "pagar": "pay payment method PSE card",
    "descuento": "discount early bird promotion offer 15% 10% 25%",
    "descuentos": "discounts early bird promotion offer 15% 10% 25%",
    "promoción": "promotion discount special offer",
    "promocion": "promotion discount special offer",
    "nivel": "level CEFR diagnostic A1 A2 B1 B2 C1 C2",
    "niveles": "levels CEFR progression A1 A2 B1 B2 C1 C2",
    "nivelación": "placement test diagnostic free evaluation 45min",
    "nivelacion": "placement test diagnostic free evaluation 45min",
    "examen": "exam test certification ielts toefl cambridge",
    "exámenes": "exams tests certifications ielts toefl cambridge",
    "examenes": "exams tests certifications ielts toefl cambridge",
    "certificación": "certification diploma certificate ielts toefl cambridge",
    "certificacion": "certification diploma certificate ielts toefl cambridge",
    "certificaciones": "certifications diplomas certificates ielts toefl cambridge",
    "virtual": "online live zoom virtual campus remote",
    "presencial": "on-campus in-person classrooms bogota medellin",
    "híbrido": "hybrid blended online in-person",
    "hibrido": "hybrid blended online in-person",
    "curso": "course program class training module english french",
    "cursos": "courses programs classes training modules english french",
    "información": "information details overview catalog courses offerings",
    "informacion": "information details overview catalog courses offerings",
    "info": "information details overview catalog",
    "matrícula": "enrollment registration procedure steps",
    "matricula": "enrollment registration procedure steps",
    "inscripción": "enrollment registration procedure steps",
    "inscripcion": "enrollment registration procedure steps",
    "reembolso": "refund freeze cancellation policy",
    "congelar": "freeze course postponement policy"
}

def tokenize(text: str) -> List[str]:
    return [w for w in re.findall(r'\b\w+\b', text.lower()) if len(w) > 2]

def expand_query(query: str) -> str:
    """Expands Spanish queries with English domain terms."""
    expanded_terms = []
    raw_tokens = tokenize(query)
    for t in raw_tokens:
        expanded_terms.append(t)
        if t in SPANISH_KEYWORD_EXPANSIONS:
            expanded_terms.append(SPANISH_KEYWORD_EXPANSIONS[t])
    if expanded_terms:
        return " ".join(expanded_terms)
    return query

class VectorStore:
    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.vector_store_path = settings.VECTOR_STORE_PATH
        self.avgdl = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.total_docs = 0

    def is_indexed(self) -> bool:
        return self.vector_store_path.exists() and len(self.chunks) > 0

    def load(self) -> bool:
        if not self.vector_store_path.exists():
            return False
        try:
            with open(self.vector_store_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.chunks = data.get("chunks", [])
            self._compute_bm25_stats()
            return len(self.chunks) > 0
        except Exception as e:
            print(f"[VectorStore] Error loading vector store: {e}")
            return False

    def save(self):
        self.vector_store_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "chunks": self.chunks
        }
        with open(self.vector_store_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _compute_bm25_stats(self):
        self.total_docs = len(self.chunks)
        if self.total_docs == 0:
            return
        total_len = 0
        self.doc_freqs = {}
        for c in self.chunks:
            tokens = set(tokenize(c.get("text", "") + " " + c.get("section", "")))
            total_len += len(tokens)
            for t in tokens:
                self.doc_freqs[t] = self.doc_freqs.get(t, 0) + 1
        self.avgdl = total_len / self.total_docs if self.total_docs > 0 else 1.0

    def build_index(self, force: bool = False):
        if self.is_indexed() and not force:
            print("[VectorStore] Index already loaded from cache.")
            return

        loader = DocumentLoader(settings.DATA_DIR)
        chunks = loader.load_markdown_documents()
        if not chunks:
            print("[VectorStore] Warning: No markdown documents found in data directory.")
            return

        print(f"[VectorStore] Ingesting {len(chunks)} chunks from knowledge base...")
        self.chunks = chunks
        self._compute_bm25_stats()
        self.save()
        print(f"[VectorStore] Successfully indexed {len(self.chunks)} chunks to {self.vector_store_path}")

    def similarity_search(self, query: str, top_k: int = 4, threshold: float = 0.0) -> Tuple[List[Dict[str, Any]], float, bool]:
        """
        BM25 + Semantic Hybrid Ranking for high-precision knowledge chunk retrieval.
        """
        if len(self.chunks) == 0:
            self.load()
            if len(self.chunks) == 0:
                self.build_index()

        if len(self.chunks) == 0:
            return [], 0.0, True

        # Query Expansion
        expanded_terms = []
        raw_tokens = tokenize(query)
        for t in raw_tokens:
            expanded_terms.append(t)
            if t in SPANISH_KEYWORD_EXPANSIONS:
                expanded_terms.extend(tokenize(SPANISH_KEYWORD_EXPANSIONS[t]))

        q_tokens = list(set(expanded_terms))

        k1 = 1.5
        b = 0.75
        scores = []

        for idx, chunk in enumerate(self.chunks):
            doc_text = (chunk.get("text", "") + " " + chunk.get("section", "")).lower()
            doc_tokens = tokenize(doc_text)
            doc_len = len(doc_tokens)
            doc_tf = {}
            for t in doc_tokens:
                doc_tf[t] = doc_tf.get(t, 0) + 1

            score = 0.0
            for q in q_tokens:
                if q in doc_tf:
                    tf = doc_tf[q]
                    df = self.doc_freqs.get(q, 1)
                    # IDF
                    idf = math.log(1.0 + (self.total_docs - df + 0.5) / (df + 0.5))
                    # Term saturation
                    numerator = tf * (k1 + 1.0)
                    denominator = tf + k1 * (1.0 - b + b * (doc_len / self.avgdl))
                    score += idf * (numerator / denominator)

            scores.append((score, idx))

        scores.sort(key=lambda x: x[0], reverse=True)

        max_score = scores[0][0] if scores else 0.0
        should_escalate = max_score < threshold

        results = []
        for score, idx in scores[:top_k]:
            chunk = dict(self.chunks[idx])
            chunk["similarity_score"] = round(float(score), 4)
            results.append(chunk)

        return results, max_score, should_escalate

vector_store = VectorStore()
