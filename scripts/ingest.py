import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.services.vector_store import vector_store
from app.config import settings

def run_ingestion():
    print("=" * 60)
    print("🚀 GLOBAL LANGUAGE ACADEMY - KNOWLEDGE INGESTION PIPELINE")
    print("=" * 60)
    print(f"Knowledge Directory: {settings.DATA_DIR}")
    print(f"Target Vector Store: {settings.VECTOR_STORE_PATH}")
    print(f"AI Provider: {settings.AI_PROVIDER}")

    vector_store.build_index(force=True)

    print("\n✅ Ingestion complete! Summary:")
    print(f"Total Chunks Indexed: {len(vector_store.chunks)}")
    print(f"Average Document Length: {vector_store.avgdl:.1f} tokens")

    # Sample query verification
    print("\n🔍 Running Sample Verification Query: 'quiero información sobre los cursos de inglés'")
    results, max_score, should_escalate = vector_store.similarity_search(
        "quiero información sobre los cursos de inglés",
        top_k=3
    )

    print(f"Max Relevance Score: {round(max_score, 4)} (Should escalate: {should_escalate})")
    for i, res in enumerate(results, 1):
        print(f"  [{i}] Source: {res.get('filename')} | Section: {res.get('section')} | Score: {res.get('similarity_score')}")

if __name__ == "__main__":
    run_ingestion()
