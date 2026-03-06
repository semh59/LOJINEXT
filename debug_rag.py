import asyncio
import sys
import os
import numpy as np

# Add project root to path
sys.path.insert(0, os.getcwd())

from app.core.ai.rag_engine import RAGEngine, get_rag_engine


async def debug_rag():
    print("--- RAG Debug Start ---")

    # Try singleton first
    print("Getting RAG Engine singleton...")
    rag = get_rag_engine()

    print(f"Initial Status: {rag.status}")
    print("Waiting for readiness (60s timeout)...")

    ready = rag.wait_until_ready(timeout=60.0)
    print(f"Ready: {ready}, Status: {rag.status}")

    if not ready:
        print("FAIL: RAG not ready")
        return

    print(f"Is Initialized: {rag.is_initialized}")
    print(f"Vector Store Dimension: {rag.vector_store.embedding_dim}")
    print(f"Vector Store count: {rag.get_stats()['total_documents']}")

    # Check for dimension mismatch
    expected_dim = rag.EMBEDDING_DIM
    actual_dim = rag.vector_store.embedding_dim
    if actual_dim != expected_dim:
        print(
            f"CRITICAL: Dimension mismatch! Expected: {expected_dim}, Actual: {actual_dim}"
        )
        print("Clearing index for fresh test...")
        rag.clear_index()
        print(f"Vector Store count after clear: {rag.vector_store.count()}")

    # Test Indexing
    print("Testing index_vehicle...")
    vehicle_data = {
        "id": 999,
        "plaka": "DEBUG-PLK",
        "marka": "Volvo",
        "model": "FH",
        "yil": 2024,
    }

    try:
        success = await rag.index_vehicle(vehicle_data)
        print(f"Index success: {success}")
        if not success:
            print("Why failed? Checking attributes...")
            print(f"rag.embedder is None: {rag.embedder is None}")
            print(f"rag.vector_store is None: {rag.vector_store is None}")
    except Exception as e:
        print(f"Exception during indexing: {e}")
        import traceback

        traceback.print_exc()

    # Test Search
    if success:
        print("Testing search...")
        results = await rag.search("Volvo araç", top_k=1)
        print(f"Search results count: {len(results)}")
        for r in results:
            print(f" - Result: {r.document[:50]}... Score: {r.score}")

    print("--- RAG Debug End ---")


if __name__ == "__main__":
    asyncio.run(debug_rag())
