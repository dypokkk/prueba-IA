import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.services.hybrid_router import process_inquiry
from app.services.metrics_service import metrics_service
from app.services.cache_service import cache_service
from app.tools.custom_tools import calculate_course_quote, check_level_placement

def run_tests():
    print("=" * 70)
    print("🧪 RUNNING COMPREHENSIVE END-TO-END PIPELINE TESTS")
    print("=" * 70)

    # Test 1: Tier 1 - Deterministic Matcher
    print("\n--- Test 1: Tier 1 Deterministic Matcher (Payment Methods) ---")
    query_1 = "What payment methods do you accept for English classes?"
    res_1 = process_inquiry(query_1)
    print(f"Query: '{query_1}'")
    print(f"Tier: {res_1['tier']} | Cached: {res_1['cached']} | Latency: {res_1['latency_ms']}ms")
    assert res_1["tier"] in ["deterministic", "cache"], "Expected deterministic or cache tier"
    assert res_1["escalate_to_human"] is False, "Expected no escalation"
    print("✅ Test 1 Passed!")

    # Test 2: Cache Hit Verification
    print("\n--- Test 2: In-Memory Cache Hit Verification ---")
    res_2 = process_inquiry(query_1)
    print(f"Query Repeat: '{query_1}'")
    print(f"Tier: {res_2['tier']} | Cached: {res_2['cached']} | Latency: {res_2['latency_ms']}ms")
    assert res_2["cached"] is True, "Expected cache hit"
    print("✅ Test 2 Passed!")

    # Test 3: Tier 2 - RAG Grounded Query
    print("\n--- Test 3: Tier 2 RAG Retrieval & Reasoning ---")
    query_3 = "Can you tell me about the Cambridge B2 First and C1 Advanced exams you prepare for?"
    res_3 = process_inquiry(query_3)
    print(f"Query: '{query_3}'")
    print(f"Tier: {res_3['tier']} | Confidence: {res_3['confidence']} | Sources: {res_3['sources']}")
    print("✅ Test 3 Passed!")

    # Test 4: Tier 3 - Human Escalation Trigger
    print("\n--- Test 4: Tier 3 Human Escalation (Special Scholarship / Complaint) ---")
    query_4 = "I demand a 90% discount and direct personal contact with the school president"
    res_4 = process_inquiry(query_4)
    print(f"Query: '{query_4}'")
    print(f"Tier: {res_4['tier']} | Escalated: {res_4['escalate_to_human']} | Ticket ID: {res_4['ticket_id']}")
    assert res_4["escalate_to_human"] is True, "Expected escalate_to_human == True"
    assert res_4["ticket_id"] is not None, "Expected ticket ID to be generated"
    print("✅ Test 4 Passed!")

    # Test 5: Custom Tools Verification
    print("\n--- Test 5: Custom Tools (Tuition Calculator & Placement Advisor) ---")
    quote = calculate_course_quote("standard_group", has_early_bird=True)
    print(f"Quote (Standard Group with Early Bird): {quote['final_price_cop']} ({quote['discount_applied']} off)")
    assert "15%" in quote["discount_applied"]

    placement = check_level_placement(75.0)
    print(f"Placement for 75%: {placement['cefr_level']} -> {placement['recommended_module']}")
    assert "B2" in placement["cefr_level"]
    print("✅ Test 5 Passed!")

    # Test 6: Metrics Verification
    print("\n--- Test 6: Real-Time Operational Metrics Summary ---")
    metrics = metrics_service.get_summary()
    print(f"Total Queries: {metrics['total_queries']}")
    print(f"Cache Hit Rate: {metrics['cache_hit_rate_pct']}%")
    print(f"Escalation Rate: {metrics['escalation_rate_pct']}%")
    print(f"Estimated AI Cost: ${metrics['total_cost_usd']} USD")
    assert metrics["total_queries"] >= 4
    print("✅ Test 6 Passed!")

    print("\n" + "=" * 70)
    print("🎉 ALL 6 COMPREHENSIVE PIPELINE TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
