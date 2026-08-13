import json
import logging
import math
import time
import urllib.error
import urllib.request
import warnings
from typing import Any

from app.core.config import settings
from app.models import ExtractedCVData, JobOffer


_model = None
logger = logging.getLogger(__name__)


def generate_embedding(text: str) -> list[float]:
    clean_text = text.strip()
    if not clean_text:
        return []
    if settings.EMBEDDING_PROVIDER.lower() == "openai":
        return _generate_openai_embedding(clean_text)
    model = _get_model()
    vector = next(model.embed([clean_text]))
    return [float(value) for value in vector.tolist()]


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    if not vector_a or not vector_b or len(vector_a) != len(vector_b):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def build_candidate_embedding_text(extracted_data: ExtractedCVData) -> str:
    data = extracted_data.ai_output or extracted_data.parsed_json or {}
    parts = [
        _string_value(data.get("identified_job_profile") or data.get("current_title") or data.get("poste_actuel")),
        _string_value(data.get("summary") or extracted_data.summary),
        _join_items(data.get("skills") or data.get("competences")),
        _join_items(data.get("experience") or data.get("detailed_experience") or data.get("experiences_detaillees")),
        _join_items(data.get("education") or data.get("diplomes")),
        _join_items(data.get("languages") or data.get("langues")),
    ]
    return "\n".join(part for part in parts if part)


def build_job_embedding_text(job: JobOffer) -> str:
    language_labels = []
    if job.languages:
        language_labels = [
            f"{entry.get('language', '')} ({entry.get('level', '')})"
            for entry in job.languages
            if isinstance(entry, dict) and entry.get("language")
        ]
    parts = [
        job.title,
        job.company_name,
        job.department,
        job.sector,
        job.description,
        job.requirements,
        _join_items(job.required_skills),
        _join_items(job.preferred_skills),
        _join_items(job.soft_skills),
        _join_items(language_labels),
        f"{job.required_experience_years} years experience" if job.required_experience_years is not None else "",
        job.education_level,
    ]
    return "\n".join(str(part).strip() for part in parts if str(part or "").strip())


def _get_model():
    global _model
    if _model is None:
        from fastembed import TextEmbedding

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*now uses mean pooling.*", category=UserWarning)
            _model = TextEmbedding(model_name=settings.EMBEDDING_MODEL_NAME)
    return _model


def _generate_openai_embedding(text: str) -> list[float]:
    api_key = settings.effective_embedding_api_key
    if not api_key:
        raise RuntimeError("OpenAI embedding API key is not configured.")

    payload = {
        "model": settings.EMBEDDING_MODEL_NAME,
        "input": text,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    response_payload = _open_embedding_request_with_retries(
        request,
        settings.EMBEDDING_REQUEST_TIMEOUT_SECONDS,
        settings.EMBEDDING_MAX_RETRIES,
    )
    embedding = response_payload.get("data", [{}])[0].get("embedding")
    if not isinstance(embedding, list):
        raise RuntimeError("OpenAI embedding response did not contain a vector.")
    vector = [float(value) for value in embedding]
    logger.info(
        "OpenAI embedding generated model=%s dimension=%s",
        settings.EMBEDDING_MODEL_NAME,
        len(vector),
    )
    return vector


def _open_embedding_request_with_retries(
    request: urllib.request.Request,
    timeout_seconds: int,
    max_retries: int,
) -> dict[str, Any]:
    attempts = max(1, max_retries)
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < attempts - 1:
                time.sleep(2**attempt)
    raise RuntimeError("OpenAI embedding request failed.") from last_error


def _join_items(items: Any) -> str:
    if isinstance(items, list):
        return ", ".join(str(item).strip() for item in items if str(item).strip())
    return _string_value(items)


def _string_value(value: Any) -> str:
    return str(value or "").strip()
