from backend.app.services.rag_service import rag_service

def test_chunk_document():
    text = "Word " * 500
    chunks = rag_service.chunk_document("Test Doc", text, chunk_size=200, overlap=50)
    assert len(chunks) >= 2
    assert chunks[0].document_title == "Test Doc"
    assert chunks[0].chunk_index == 0

def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]
    assert rag_service.cosine_similarity(v1, v2) == 1.0
    assert rag_service.cosine_similarity(v1, v3) == 0.0

def test_calculate_faithfulness():
    context = "The Eiffel Tower is in Paris, France. It was built in 1889."
    grounded_answer = "The Eiffel Tower was built in 1889 in Paris."
    hallucinated_answer = "The Eiffel Tower is in London, England."

    score_grounded = rag_service.calculate_faithfulness(grounded_answer, context)
    score_hallucinated = rag_service.calculate_faithfulness(hallucinated_answer, context)

    assert score_grounded > score_hallucinated
    assert score_grounded > 0.6
