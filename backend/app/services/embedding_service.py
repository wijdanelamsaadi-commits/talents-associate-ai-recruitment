import math
import warnings
from typing import Any

from app.core.config import settings
from app.models import ExtractedCVData, JobOffer


_model = None


def generate_embedding(text: str) -> list[float]:
    clean_text = text.strip()
    if not clean_text:
        return []
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
        _string_value(data.get("summary") or extracted_data.summary),
        _join_items(data.get("skills") or data.get("competences")),
        _join_items(data.get("experience") or data.get("detailed_experience") or data.get("experiences_detaillees")),
        _join_items(data.get("education") or data.get("diplomes")),
        _join_items(data.get("languages") or data.get("langues")),
    ]
    return "\n".join(part for part in parts if part)


def build_job_embedding_text(job: JobOffer) -> str:
    parts = [
        job.title,
        job.company_name,
        job.department,
        job.description,
        job.requirements,
        _join_items(job.required_skills),
        _join_items(job.preferred_skills),
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


def _join_items(items: Any) -> str:
    if isinstance(items, list):
        return ", ".join(str(item).strip() for item in items if str(item).strip())
    return _string_value(items)


def _string_value(value: Any) -> str:
    return str(value or "").strip()
