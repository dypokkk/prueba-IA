import unittest
import os
import sys
from pathlib import Path

# Add project root
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.config import settings
from app.services.document_loader import DocumentLoader
from app.services.vector_store import vector_store, expand_query
from app.services.deterministic_service import deterministic_service
from app.services.cache_service import cache_service
from app.services.metrics_service import metrics_service
from app.services.escalation_service import escalation_service
from app.services.hybrid_router import process_inquiry
from app.tools.custom_tools import calculate_course_quote, check_level_placement

class TestDocumentLoader(unittest.TestCase):
    def test_load_documents_and_chunking(self):
        loader = DocumentLoader(settings.DATA_DIR, chunk_size=600, chunk_overlap=120)
        chunks = loader.load_markdown_documents()
        self.assertGreaterEqual(len(chunks), 15)
        for c in chunks:
            self.assertIn("chunk_id", c)
            self.assertIn("filename", c)
            self.assertIn("section", c)
            self.assertIn("text", c)
            self.assertTrue(c["filename"].endswith(".md"))

class TestVectorStoreBM25(unittest.TestCase):
    def setUp(self):
        vector_store.build_index(force=False)

    def test_bilingual_expansion(self):
        expanded = expand_query("cursos de inglés y precios")
        self.assertIn("english", expanded)
        self.assertIn("price", expanded)

    def test_bm25_retrieval(self):
        chunks, max_score, _ = vector_store.similarity_search("Saturday intensive class schedules", top_k=3)
        self.assertGreater(len(chunks), 0)
        self.assertGreater(max_score, 0.0)
        # Verify relevant file
        filenames = [c["filename"] for c in chunks]
        self.assertIn("02_schedules_and_modalities.md", filenames)

class TestDeterministicService(unittest.TestCase):
    def test_greetings_match(self):
        res = deterministic_service.match("hola")
        self.assertIsNotNone(res)
        self.assertEqual(res["category"], "greetings")
        self.assertFalse(res["escalate_to_human"])

    def test_payment_methods_match(self):
        res = deterministic_service.match("What payment methods do you accept?")
        self.assertIsNotNone(res)
        self.assertEqual(res["category"], "payment_methods")
        self.assertIn("PSE", res["answer"])

    def test_escalation_intent_bypass(self):
        # Queries with complaint/refund/scholarship demands should bypass deterministic matching
        res = deterministic_service.match("I want a full refund and speak with the director")
        self.assertIsNone(res)

class TestCacheService(unittest.TestCase):
    def setUp(self):
        cache_service.clear()

    def test_set_and_get(self):
        query = "How much is the English course?"
        data = {"answer": "Test Answer", "confidence": 0.95, "escalate_to_human": False}
        cache_service.set(query, data)

        cached = cache_service.get("how much is the english course???")
        self.assertIsNotNone(cached)
        self.assertEqual(cached["answer"], "Test Answer")

    def test_never_cache_escalations(self):
        query = "I want a refund"
        data = {"answer": "Escalated", "escalate_to_human": True}
        cache_service.set(query, data)
        self.assertIsNone(cache_service.get(query))

class TestCustomTools(unittest.TestCase):
    def test_calculate_course_quote(self):
        # Early bird 15% discount
        quote = calculate_course_quote("standard_group", has_early_bird=True)
        self.assertEqual(quote["discount_applied"], "15%")
        self.assertEqual(quote["final_price_cop"], "$1,062,500 COP")

        # Annual bundle 25% discount
        annual_quote = calculate_course_quote("standard_group", annual_bundle=True)
        self.assertEqual(annual_quote["discount_applied"], "25%")
        self.assertEqual(annual_quote["final_price_cop"], "$937,500 COP")

    def test_check_level_placement(self):
        # A1 Beginner
        p_a1 = check_level_placement(20.0)
        self.assertIn("A1", p_a1["cefr_level"])

        # B2 Upper Intermediate
        p_b2 = check_level_placement(75.0)
        self.assertIn("B2", p_b2["cefr_level"])
        self.assertTrue(p_b2["official_prep_eligible"])

class TestEscalationService(unittest.TestCase):
    def test_create_and_resolve_ticket(self):
        ticket = escalation_service.create_ticket(
            user_query="Customer demanding special terms",
            escalation_reason="DISPUTE_TEST",
            channel="web"
        )
        self.assertIn("ticket_id", ticket)
        self.assertEqual(ticket["status"], "PENDING")

        success = escalation_service.resolve_ticket(ticket["ticket_id"], notes="Handled by senior advisor")
        self.assertTrue(success)

        resolved_ticket = next(t for t in escalation_service.get_tickets() if t["ticket_id"] == ticket["ticket_id"])
        self.assertEqual(resolved_ticket["status"], "RESOLVED")

class TestHybridPipeline(unittest.TestCase):
    def setUp(self):
        cache_service.clear()

    def test_deterministic_flow(self):
        res = process_inquiry("What payment methods and financing options do you have?")
        self.assertEqual(res["tier"], "deterministic")
        self.assertFalse(res["escalate_to_human"])
        self.assertIn("PSE", res["answer"])

    def test_cache_flow(self):
        query = "What payment methods and financing options do you have?"
        process_inquiry(query)
        res_cached = process_inquiry(query)
        self.assertTrue(res_cached["cached"])
        self.assertEqual(res_cached["tier"], "cache")

    def test_human_escalation_flow(self):
        res = process_inquiry("I demand a 90% scholarship and personal phone number of the director")
        self.assertTrue(res["escalate_to_human"])
        self.assertIsNotNone(res["ticket_id"])

class TestMetricsService(unittest.TestCase):
    def test_metrics_calculation(self):
        summary = metrics_service.get_summary()
        self.assertIn("total_queries", summary)
        self.assertIn("cache_hit_rate_pct", summary)
        self.assertIn("total_cost_usd", summary)
        self.assertIn("escalation_rate_pct", summary)
        self.assertGreaterEqual(summary["total_queries"], 1)

if __name__ == "__main__":
    unittest.main()
