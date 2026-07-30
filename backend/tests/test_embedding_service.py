from app.services.embedding_service import cosine_similarity
from app.services import embedding_service


def test_cosine_similarity_identical_vectors():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_cosine_similarity_rejects_mismatched_vectors():
    assert cosine_similarity([1.0, 0.0], [1.0]) == 0.0


def test_cosine_similarity_empty_vectors():
    assert cosine_similarity([], [1.0]) == 0.0


def test_openai_embedding_provider_uses_openai_key_and_model_without_fastembed(monkeypatch):
    captured = {}
    monkeypatch.setattr(embedding_service.settings, "EMBEDDING_PROVIDER", "openai")
    monkeypatch.setattr(embedding_service.settings, "EMBEDDING_MODEL_NAME", "text-embedding-3-small")
    monkeypatch.setattr(embedding_service.settings, "OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setattr(embedding_service.settings, "EMBEDDING_API_KEY", None)

    def fail_if_fastembed_is_used():
        raise AssertionError("FastEmbed should not be used when EMBEDDING_PROVIDER=openai")

    def fake_open_embedding_request_with_retries(request, timeout_seconds, max_retries):
        payload = json.loads(request.data.decode("utf-8"))
        captured["model"] = payload["model"]
        captured["input"] = payload["input"]
        captured["authorization_set"] = bool(request.headers.get("Authorization"))
        return {"data": [{"embedding": [0.1, 0.2, 0.3]}]}

    import json

    monkeypatch.setattr(embedding_service, "_get_model", fail_if_fastembed_is_used)
    monkeypatch.setattr(embedding_service, "_open_embedding_request_with_retries", fake_open_embedding_request_with_retries)

    vector = embedding_service.generate_embedding("Python FastAPI SQL")

    assert captured["model"] == "text-embedding-3-small"
    assert captured["input"] == "Python FastAPI SQL"
    assert captured["authorization_set"] is True
    assert vector == [0.1, 0.2, 0.3]
