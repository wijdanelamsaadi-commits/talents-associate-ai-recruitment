import json
import re
import urllib.error
import urllib.request
from typing import Any

from app.core.config import settings
from app.services.cv_parser import ParsedCV, parse_cv_text


CV_PARSER_PROMPT = """
Tu es un service d'extraction de CV pour Talents Associate.

Règles strictes :
- Extrais uniquement les informations présentes dans le texte fourni.
- N'invente jamais une information absente ou ambiguë.
- Si une information n'est pas trouvée, retourne null pour une valeur simple ou [] pour une liste.
- Le sexe doit être renseigné uniquement s'il est clairement présent dans le CV.
- Garde les valeurs originales si possible, notamment les intitulés de poste, entreprises, dates et diplômes.
- Réponds uniquement avec un objet JSON valide.
- N'ajoute aucun commentaire, aucun markdown et aucun texte autour du JSON.

Format JSON obligatoire :
{
  "prenom": null,
  "nom": null,
  "first_name": null,
  "last_name": null,
  "email": null,
  "phone": null,
  "linkedin_url": null,
  "current_company": null,
  "current_title": null,
  "total_experience_years": null,
  "experience": [],
  "detailed_experience": [
    {
      "company": null,
      "title": null,
      "start_date": null,
      "end_date": null,
      "location": null,
      "description": null
    }
  ],
  "education": [
    {
      "degree": null,
      "school": null,
      "obtained_date": null,
      "description": null
    }
  ],
  "skills": [],
  "languages": [],
  "certifications": [],
  "soft_skills": [],
  "gender": null,
  "parser_confidence": null
}
""".strip()


EXPECTED_FIELDS: dict[str, Any] = {
    "prenom": None,
    "nom": None,
    "first_name": None,
    "last_name": None,
    "email": None,
    "phone": None,
    "linkedin_url": None,
    "current_company": None,
    "current_title": None,
    "total_experience_years": None,
    "experience": [],
    "detailed_experience": [],
    "education": [],
    "skills": [],
    "languages": [],
    "certifications": [],
    "soft_skills": [],
    "gender": None,
    "parser_confidence": None,
}


class LLMParserError(RuntimeError):
    pass


def parse_cv_text_configurable(raw_text: str) -> ParsedCV:
    if not _is_llm_available():
        return _heuristic_result(raw_text)

    try:
        llm_data = _parse_with_openai(raw_text)
        normalized = _normalize_llm_payload(llm_data)
        confidence_score = _coerce_confidence(normalized.get("parser_confidence"))
        normalized["parser_confidence"] = confidence_score
        normalized["parser_used"] = "llm"
        return ParsedCV(data=normalized, confidence_score=confidence_score)
    except Exception:
        return _heuristic_result(raw_text)


def _is_llm_available() -> bool:
    return (
        settings.LLM_ENABLED
        and settings.LLM_PROVIDER.lower() == "openai"
        and bool(settings.OPENAI_API_KEY)
    )


def _parse_with_openai(raw_text: str) -> dict[str, Any]:
    model = settings.LLM_MODEL or "gpt-4o-mini"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": CV_PARSER_PROMPT},
            {"role": "user", "content": f"Texte du CV :\n{raw_text[:30000]}"},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise LLMParserError("OpenAI CV parsing request failed.") from exc

    content = (
        response_payload.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    return _loads_json_object(content)


def _loads_json_object(content: str) -> dict[str, Any]:
    cleaned = _strip_code_fence(content).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise LLMParserError("LLM response did not contain a JSON object.")
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise LLMParserError("LLM response JSON is not an object.")
    return parsed


def _strip_code_fence(content: str) -> str:
    return re.sub(r"^```(?:json)?|```$", "", content.strip(), flags=re.IGNORECASE | re.MULTILINE)


def _normalize_llm_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(EXPECTED_FIELDS)
    for key in EXPECTED_FIELDS:
        normalized[key] = _clean_value(payload.get(key), EXPECTED_FIELDS[key])

    normalized["first_name"] = normalized["first_name"] or normalized["prenom"]
    normalized["last_name"] = normalized["last_name"] or normalized["nom"]
    normalized["prenom"] = normalized["prenom"] or normalized["first_name"]
    normalized["nom"] = normalized["nom"] or normalized["last_name"]

    if normalized["detailed_experience"] and not normalized["experience"]:
        normalized["experience"] = [
            item
            for item in (
                _experience_to_label(experience)
                for experience in normalized["detailed_experience"]
            )
            if item
        ]

    return normalized


def _clean_value(value: Any, default: Any) -> Any:
    if isinstance(default, list):
        return value if isinstance(value, list) else []
    if value in ("", [], {}, "null", "None", "N/A"):
        return None
    return value if value is not None else None


def _experience_to_label(experience: Any) -> str | None:
    if not isinstance(experience, dict):
        return str(experience).strip() or None
    parts = [
        str(experience.get("title") or "").strip(),
        str(experience.get("company") or "").strip(),
        str(experience.get("start_date") or "").strip(),
        str(experience.get("end_date") or "").strip(),
    ]
    clean_parts = [part for part in parts if part]
    return " - ".join(clean_parts) if clean_parts else None


def _coerce_confidence(value: Any) -> float:
    if value is None:
        return 0.85
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.85
    if numeric > 1:
        numeric = numeric / 100
    return round(max(0.0, min(numeric, 1.0)), 2)


def _heuristic_result(raw_text: str) -> ParsedCV:
    parsed = parse_cv_text(raw_text)
    data = dict(EXPECTED_FIELDS)
    data.update(parsed.data)
    data["prenom"] = parsed.data.get("first_name") or None
    data["nom"] = parsed.data.get("last_name") or None
    data["first_name"] = parsed.data.get("first_name") or None
    data["last_name"] = parsed.data.get("last_name") or None
    data["email"] = parsed.data.get("email") or None
    data["phone"] = parsed.data.get("phone") or None
    data["parser_used"] = "heuristic"
    data["parser_confidence"] = parsed.confidence_score
    return ParsedCV(data=data, confidence_score=parsed.confidence_score)
