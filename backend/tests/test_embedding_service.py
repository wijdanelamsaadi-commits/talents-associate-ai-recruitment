from app.services.embedding_service import cosine_similarity


def test_cosine_similarity_identical_vectors():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_cosine_similarity_rejects_mismatched_vectors():
    assert cosine_similarity([1.0, 0.0], [1.0]) == 0.0


def test_cosine_similarity_empty_vectors():
    assert cosine_similarity([], [1.0]) == 0.0
