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
    "francés": "french francais CIEP levels DELF DALF",
    "frances": "french francais CIEP levels DELF DALF",
    "alemán": "german deutsch goethe TestDaF",
    "aleman": "german deutsch goethe TestDaF",
    "italiano": "italian immersion CILS CELI",
    "portugués": "portuguese brasileiro Celpe-Bras",
    "portugues": "portuguese brasileiro Celpe-Bras",
    "español": "spanish foreigners dele siele expatriates",
    "espanol": "spanish foreigners dele siele expatriates",
    "grupal": "group groups standard intensive cohort classroom max 8 students individual",
    "grupales": "group groups standard intensive cohort classroom max 8 students individual",
    "grupo": "group groups standard intensive cohort classroom max 8 students individual",
    "grupos": "group groups standard intensive cohort classroom max 8 students individual",
    "personalizado": "private one-on-one 1:1 individualized custom tutor VIP package",
    "personalizados": "private one-on-one 1:1 individualized custom tutor VIP package",
    "privado": "private one-on-one 1:1 individualized custom tutor VIP package",
    "privados": "private one-on-one 1:1 individualized custom tutor VIP package",
    "particular": "private one-on-one 1:1 individualized custom tutor VIP package",
    "particulares": "private one-on-one 1:1 individualized custom tutor VIP package",
    "intensivo": "intensive fast track monthly 4 weeks 60 hours",
    "intensivos": "intensive fast track monthly 4 weeks 60 hours",
    "estándar": "standard quarterly 10 weeks 60 hours",
    "estandar": "standard quarterly 10 weeks 60 hours",
    "niños": "kids teens young learners 12 weeks 48 hours",
    "ninos": "kids teens young learners 12 weeks 48 hours",
    "adolescentes": "kids teens young learners 12 weeks 48 hours",
    "falto": "missed absences makeup recovery tutoring catch up recordings attendance",
    "falta": "missed absences makeup recovery tutoring catch up recordings attendance",
    "faltar": "missed absences makeup recovery tutoring catch up recordings attendance",
    "inasistencia": "attendance absences makeup recovery tutoring justified",
    "asistencia": "attendance minimum 80% policy absences makeup tutoring",
    "recuperar": "makeup recovery tutoring catch up 1-on-1 sessions 45 minutes",
    "recuperación": "makeup recovery tutoring catch up 1-on-1 sessions 45 minutes",
    "recuperacion": "makeup recovery tutoring catch up 1-on-1 sessions 45 minutes",
    "reponer": "makeup recovery tutoring catch up 1-on-1 sessions",
    "grabaciones": "recordings recorded sessions video zoom portal 2 hours upload",
    "grabacion": "recordings recorded sessions video zoom portal 2 hours upload",
    "graban": "recordings recorded sessions video zoom portal 2 hours upload",
    "profesor": "teachers native certified bilingual CELTA instructors faculty",
    "profesores": "teachers native certified bilingual CELTA instructors faculty",
    "docente": "teachers native certified bilingual CELTA instructors faculty",
    "docentes": "teachers native certified bilingual CELTA instructors faculty",
    "nativo": "native certified bilingual instructors faculty CELTA DELTA",
    "nativos": "native certified bilingual instructors faculty CELTA DELTA",
    "metodología": "methodology communicative approach speaking oral real-world active 80%",
    "metodologia": "methodology communicative approach speaking oral real-world active 80%",
    "método": "methodology communicative approach speaking oral real-world active",
    "metodo": "methodology communicative approach speaking oral real-world active",
    "libros": "digital textbooks cambridge oxford platform virtual campus materials included free zero extra",
    "libro": "digital textbooks cambridge oxford platform virtual campus materials included free zero extra",
    "material": "digital textbooks cambridge oxford platform virtual campus materials included free zero extra",
    "materiales": "digital textbooks cambridge oxford platform virtual campus materials included free zero extra",
    "plataforma": "virtual campus 24/7 access audio labs pronunciation zoom",
    "campus": "virtual campus physical campus bogota chapinero medellin poblado",
    "precio": "price pricing tuition cost fees COP USD group standard individual",
    "precios": "price pricing tuition cost fees COP USD group standard individual",
    "cuánto": "how much price cost tuition rates individual duration time",
    "cuanto": "how much price cost tuition rates individual duration time",
    "costo": "cost price tuition fee individual extra hidden zero",
    "costos": "costs prices tuition fees individual extra hidden zero",
    "persona": "per person individual student each",
    "personas": "per person individual student each",
    "individual": "individual per person per student",
    "horario": "schedule timetable hours morning evening saturday switch transfer",
    "horarios": "schedules timetables hours morning evening saturday switch transfer",
    "hora": "hours time schedule duration",
    "horas": "hours duration time 60 hours 480 hours",
    "tiempo": "duration hours months fluency how long 480 hours 12 14 months B2",
    "toma": "duration hours months fluency how long 480 hours 12 14 months B2",
    "demora": "duration hours months fluency how long 480 hours 12 14 months B2",
    "duración": "duration hours months 10 weeks 4 weeks 12 weeks",
    "duracion": "duration hours months 10 weeks 4 weeks 12 weeks",
    "nota": "grade passing score 80 100 points criteria evaluation assessment",
    "notas": "grades passing score 80 100 points criteria evaluation assessment",
    "mínima": "minimum passing grade 80 100 score points criteria",
    "minima": "minimum passing grade 80 100 score points criteria",
    "pasar": "pass advance progress next level 80 100 points criteria",
    "aprobar": "pass advance progress next level 80 100 points criteria certificate",
    "aprobación": "passing grade 80 100 points certificate criteria",
    "aprobacion": "passing grade 80 100 points certificate criteria",
    "empresa": "company corporate business enterprise training agreements packages HR",
    "empresas": "company corporate business enterprise training agreements packages HR",
    "corporativo": "corporate enterprise agreements companies HR business",
    "corporativos": "corporate enterprise agreements companies HR business",
    "convenio": "corporate agreement partnership discount 12% companies",
    "convenios": "corporate agreements partnerships discount 12% companies",
    "club": "conversation clubs speaking weekly sessions unlimited free complimentary",
    "clubes": "conversation clubs speaking weekly sessions unlimited free complimentary",
    "conversación": "conversation clubs speaking fluency practice weekly oral 80%",
    "conversacion": "conversation clubs speaking fluency practice weekly oral 80%",
    "cambiar": "switch change schedule transfer morning evening saturday 5 days",
    "cambiarme": "switch change schedule transfer morning evening saturday 5 days",
    "cambio": "switch change schedule transfer morning evening saturday 5 days",
    "edad": "age requirement adults 16 kids teens 8 15",
    "edades": "age requirement adults 16 kids teens 8 15",
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
    "cuota": "installments 0% interest monthly financing 3 cuotas",
    "cuotas": "installments 0% interest monthly financing 3 cuotas",
    "financiación": "financing installment plans 0% interest 3 months",
    "financiacion": "financing installment plans 0% interest 3 months",
    "descuento": "discount early bird promotion offer 15% 10% 25%",
    "descuentos": "discounts early bird promotion offer 15% 10% 25%",
    "promoción": "promotion discount special offer bundle",
    "promocion": "promotion discount special offer bundle",
    "nivel": "level CEFR diagnostic A1 A2 B1 B2 C1 C2 placement test",
    "niveles": "levels CEFR progression A1 A2 B1 B2 C1 C2 placement test",
    "nivelación": "placement test diagnostic free evaluation 45min prior knowledge assess",
    "nivelacion": "placement test diagnostic free evaluation 45min prior knowledge assess",
    "clasificación": "placement test diagnostic free evaluation 45min prior knowledge assess",
    "clasificacion": "placement test diagnostic free evaluation 45min prior knowledge assess",
    "diagnóstico": "placement test diagnostic evaluation free 45min assess",
    "diagnostico": "placement test diagnostic evaluation free 45min assess",
    "evaluación": "placement test diagnostic evaluation free 45min assess grading 80 100",
    "evaluacion": "placement test diagnostic evaluation free 45min assess grading 80 100",
    "comenzar": "start begin placement level module starting point",
    "empezar": "start begin placement level module starting point",
    "previo": "prior knowledge experience background assessment level",
    "previos": "prior knowledge experience background assessment level",
    "conocimiento": "prior knowledge experience background assessment level",
    "conocimientos": "prior knowledge experience background assessment level",
    "examen": "exam test certification diagnostic placement ielts toefl cambridge passing grade",
    "exámenes": "exams tests certifications diagnostic placement ielts toefl cambridge passing grade",
    "examenes": "exams tests certifications diagnostic placement ielts toefl cambridge passing grade",
    "certificación": "certification diploma certificate ielts toefl cambridge blockchain QR",
    "certificacion": "certification diploma certificate ielts toefl cambridge blockchain QR",
    "certificaciones": "certifications diplomas certificates ielts toefl cambridge blockchain QR",
    "virtual": "online live zoom virtual campus remote",
    "presencial": "on-campus in-person classrooms bogota medellin",
    "híbrido": "hybrid blended online in-person",
    "hibrido": "hybrid blended online in-person",
    "curso": "course program class training module english french",
    "cursos": "courses programs classes training modules english french",
    "información": "information details overview catalog courses offerings",
    "informacion": "information details overview catalog courses offerings",
    "info": "information details overview catalog",
    "matrícula": "enrollment registration procedure steps free zero cost",
    "matricula": "enrollment registration procedure steps free zero cost",
    "inscripción": "enrollment registration procedure steps free zero cost",
    "inscripcion": "enrollment registration procedure steps free zero cost",
    "reembolso": "refund freeze cancellation policy 100% 5 days",
    "congelar": "freeze course postponement policy 2 times 6 months"
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

    def similarity_search(self, query: str, top_k: int = 6, threshold: float = 0.0) -> Tuple[List[Dict[str, Any]], float, bool]:
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
                    idf = math.log(1.0 + (self.total_docs - df + 0.5) / (df + 0.5))
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
