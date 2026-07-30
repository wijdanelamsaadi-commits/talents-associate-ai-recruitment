import json
import logging
import re
import time
import urllib.error
import urllib.request
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.core.config import settings
from app.services.cv_parser import ParsedCV, parse_cv_text


logger = logging.getLogger(__name__)

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
  "telephone": null,
  "ville": null,
  "location": null,
  "linkedin_url": null,
  "linkedin": null,
  "current_company": null,
  "entreprise_actuelle": null,
  "current_title": null,
  "poste_actuel": null,
  "total_experience_years": null,
  "experience_totale": null,
  "experience": [],
  "detailed_experience": [
    {
      "company": null,
      "entreprise": null,
      "title": null,
      "poste": null,
      "start_date": null,
      "date_debut": null,
      "end_date": null,
      "date_fin": null,
      "location": null,
      "description": null
    }
  ],
  "experiences_detaillees": [],
  "education": [
    {
      "degree": null,
      "diplome": null,
      "school": null,
      "etablissement": null,
      "obtained_date": null,
      "date_obtention": null,
      "description": null
    }
  ],
  "diplomes": [],
  "skills": [],
  "competences": [],
  "technical_skills": [],
  "competences_techniques": [],
  "functional_skills": [],
  "competences_fonctionnelles": [],
  "languages": [],
  "langues": [],
  "certifications": [],
  "soft_skills": [],
  "gender": null,
  "sexe": null,
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
    "telephone": None,
    "ville": None,
    "location": None,
    "linkedin_url": None,
    "linkedin": None,
    "current_company": None,
    "entreprise_actuelle": None,
    "current_title": None,
    "poste_actuel": None,
    "total_experience_years": None,
    "experience_totale": None,
    "experience": [],
    "detailed_experience": [],
    "experiences_detaillees": [],
    "education": [],
    "diplomes": [],
    "skills": [],
    "competences": [],
    "technical_skills": [],
    "competences_techniques": [],
    "functional_skills": [],
    "competences_fonctionnelles": [],
    "languages": [],
    "langues": [],
    "certifications": [],
    "soft_skills": [],
    "gender": None,
    "sexe": None,
    "parser_confidence": None,
}


class LLMParserError(RuntimeError):
    pass


class LLMExperienceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: str | None = None
    entreprise: str | None = None
    title: str | None = None
    poste: str | None = None
    start_date: str | None = None
    date_debut: str | None = None
    end_date: str | None = None
    date_fin: str | None = None
    location: str | None = None
    description: str | None = None


class LLMEducationItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    degree: str | None = None
    diplome: str | None = None
    school: str | None = None
    etablissement: str | None = None
    obtained_date: str | None = None
    date_obtention: str | None = None
    description: str | None = None


class LLMCVPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prenom: str | None = None
    nom: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    telephone: str | None = None
    ville: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    linkedin: str | None = None
    current_company: str | None = None
    entreprise_actuelle: str | None = None
    current_title: str | None = None
    poste_actuel: str | None = None
    total_experience_years: float | None = Field(default=None, ge=0)
    experience_totale: float | None = Field(default=None, ge=0)
    experience: list[str] = Field(default_factory=list)
    detailed_experience: list[LLMExperienceItem] = Field(default_factory=list)
    experiences_detaillees: list[LLMExperienceItem] = Field(default_factory=list)
    education: list[LLMEducationItem] = Field(default_factory=list)
    diplomes: list[LLMEducationItem] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    competences: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    competences_techniques: list[str] = Field(default_factory=list)
    functional_skills: list[str] = Field(default_factory=list)
    competences_fonctionnelles: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    langues: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    gender: str | None = None
    sexe: str | None = None
    parser_confidence: float | None = Field(default=None, ge=0, le=1)

    @field_validator(
        "skills",
        "competences",
        "technical_skills",
        "competences_techniques",
        "functional_skills",
        "competences_fonctionnelles",
        "languages",
        "langues",
        "certifications",
        "soft_skills",
        "experience",
        mode="before",
    )
    @classmethod
    def coerce_string_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item or "").strip()]


def parse_cv_text_configurable(raw_text: str) -> ParsedCV:
    if not _is_llm_available():
        return _heuristic_result(raw_text)

    try:
        llm_data = _parse_with_openai(raw_text)
        validated_payload = LLMCVPayload.model_validate(llm_data).model_dump()
        normalized = _normalize_llm_payload(validated_payload)
        confidence_score = _coerce_confidence(normalized.get("parser_confidence"))
        normalized["parser_confidence"] = confidence_score
        normalized["parser_used"] = "llm"
        return ParsedCV(data=normalized, confidence_score=confidence_score)
    except (LLMParserError, ValidationError) as exc:
        logger.warning("OpenAI CV parsing failed; fallback heuristic used: %s", type(exc).__name__)
        return _heuristic_result(raw_text)


def _is_llm_available() -> bool:
    return (
        settings.LLM_ENABLED
        and settings.LLM_PROVIDER.lower() == "openai"
        and bool(settings.OPENAI_API_KEY)
    )


def _parse_with_openai(raw_text: str) -> dict[str, Any]:
    model = settings.effective_llm_model
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": CV_PARSER_PROMPT},
            {"role": "user", "content": f"Texte du CV :\n{raw_text[:30000]}"},
        ],
        "temperature": 0,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "talents_cv_parser",
                "schema": _openai_cv_json_schema(),
                "strict": True,
            },
        },
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

    response_payload = _open_url_with_retries(request, settings.LLM_REQUEST_TIMEOUT_SECONDS, settings.LLM_MAX_RETRIES)

    content = (
        response_payload.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    return _loads_json_object(content)


def _open_url_with_retries(request: urllib.request.Request, timeout_seconds: int, max_retries: int) -> dict[str, Any]:
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
    raise LLMParserError("OpenAI CV parsing request failed.") from last_error


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
    normalized["phone"] = normalized["phone"] or normalized["telephone"]
    normalized["telephone"] = normalized["telephone"] or normalized["phone"]
    normalized["location"] = normalized["location"] or normalized["ville"]
    normalized["ville"] = normalized["ville"] or normalized["location"]
    normalized["linkedin_url"] = normalized["linkedin_url"] or normalized["linkedin"]
    normalized["linkedin"] = normalized["linkedin"] or normalized["linkedin_url"]
    normalized["current_company"] = normalized["current_company"] or normalized["entreprise_actuelle"]
    normalized["entreprise_actuelle"] = normalized["entreprise_actuelle"] or normalized["current_company"]
    normalized["current_title"] = normalized["current_title"] or normalized["poste_actuel"]
    normalized["poste_actuel"] = normalized["poste_actuel"] or normalized["current_title"]
    normalized["total_experience_years"] = normalized["total_experience_years"] or normalized["experience_totale"]
    normalized["experience_totale"] = normalized["experience_totale"] or normalized["total_experience_years"]
    normalized["detailed_experience"] = _normalize_experience_items(
        normalized["detailed_experience"] or normalized["experiences_detaillees"]
    )
    normalized["experiences_detaillees"] = normalized["detailed_experience"]
    normalized["education"] = _normalize_education_items(normalized["education"] or normalized["diplomes"])
    normalized["diplomes"] = normalized["education"]
    normalized["skills"] = normalized["skills"] or normalized["competences"] or normalized["technical_skills"] or normalized["competences_techniques"]
    normalized["competences"] = normalized["competences"] or normalized["skills"]
    normalized["technical_skills"] = normalized["technical_skills"] or normalized["skills"]
    normalized["competences_techniques"] = normalized["competences_techniques"] or normalized["skills"]
    normalized["functional_skills"] = normalized["functional_skills"] or normalized["competences_fonctionnelles"]
    normalized["competences_fonctionnelles"] = normalized["competences_fonctionnelles"] or normalized["functional_skills"]
    normalized["languages"] = normalized["languages"] or normalized["langues"]
    normalized["langues"] = normalized["langues"] or normalized["languages"]
    normalized["gender"] = normalized["gender"] or normalized["sexe"]
    normalized["sexe"] = normalized["sexe"] or normalized["gender"]

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


def _openai_cv_json_schema() -> dict[str, Any]:
    nullable_string = {"anyOf": [{"type": "string"}, {"type": "null"}]}
    nullable_number = {"anyOf": [{"type": "number"}, {"type": "null"}]}
    string_array = {"type": "array", "items": {"type": "string"}}
    experience_item = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "company": nullable_string,
            "entreprise": nullable_string,
            "title": nullable_string,
            "poste": nullable_string,
            "start_date": nullable_string,
            "date_debut": nullable_string,
            "end_date": nullable_string,
            "date_fin": nullable_string,
            "location": nullable_string,
            "description": nullable_string,
        },
        "required": ["company", "entreprise", "title", "poste", "start_date", "date_debut", "end_date", "date_fin", "location", "description"],
    }
    education_item = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "degree": nullable_string,
            "diplome": nullable_string,
            "school": nullable_string,
            "etablissement": nullable_string,
            "obtained_date": nullable_string,
            "date_obtention": nullable_string,
            "description": nullable_string,
        },
        "required": ["degree", "diplome", "school", "etablissement", "obtained_date", "date_obtention", "description"],
    }
    properties = {
        "prenom": nullable_string,
        "nom": nullable_string,
        "first_name": nullable_string,
        "last_name": nullable_string,
        "email": nullable_string,
        "phone": nullable_string,
        "telephone": nullable_string,
        "ville": nullable_string,
        "location": nullable_string,
        "linkedin_url": nullable_string,
        "linkedin": nullable_string,
        "current_company": nullable_string,
        "entreprise_actuelle": nullable_string,
        "current_title": nullable_string,
        "poste_actuel": nullable_string,
        "total_experience_years": nullable_number,
        "experience_totale": nullable_number,
        "experience": string_array,
        "detailed_experience": {"type": "array", "items": experience_item},
        "experiences_detaillees": {"type": "array", "items": experience_item},
        "education": {"type": "array", "items": education_item},
        "diplomes": {"type": "array", "items": education_item},
        "skills": string_array,
        "competences": string_array,
        "technical_skills": string_array,
        "competences_techniques": string_array,
        "functional_skills": string_array,
        "competences_fonctionnelles": string_array,
        "languages": string_array,
        "langues": string_array,
        "certifications": string_array,
        "soft_skills": string_array,
        "gender": nullable_string,
        "sexe": nullable_string,
        "parser_confidence": nullable_number,
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties.keys()),
    }


def _normalize_experience_items(items: Any) -> list[Any]:
    if not isinstance(items, list):
        return []
    normalized_items = []
    for item in items:
        if not isinstance(item, dict):
            normalized_items.append(item)
            continue
        normalized_item = dict(item)
        normalized_item["company"] = normalized_item.get("company") or normalized_item.get("entreprise")
        normalized_item["entreprise"] = normalized_item.get("entreprise") or normalized_item.get("company")
        normalized_item["title"] = normalized_item.get("title") or normalized_item.get("poste")
        normalized_item["poste"] = normalized_item.get("poste") or normalized_item.get("title")
        normalized_item["start_date"] = normalized_item.get("start_date") or normalized_item.get("date_debut")
        normalized_item["date_debut"] = normalized_item.get("date_debut") or normalized_item.get("start_date")
        normalized_item["end_date"] = normalized_item.get("end_date") or normalized_item.get("date_fin")
        normalized_item["date_fin"] = normalized_item.get("date_fin") or normalized_item.get("end_date")
        normalized_items.append(normalized_item)
    return normalized_items


def _normalize_education_items(items: Any) -> list[Any]:
    if not isinstance(items, list):
        return []
    normalized_items = []
    for item in items:
        if not isinstance(item, dict):
            normalized_items.append(item)
            continue
        normalized_item = dict(item)
        normalized_item["degree"] = normalized_item.get("degree") or normalized_item.get("diplome")
        normalized_item["diplome"] = normalized_item.get("diplome") or normalized_item.get("degree")
        normalized_item["school"] = normalized_item.get("school") or normalized_item.get("etablissement")
        normalized_item["etablissement"] = normalized_item.get("etablissement") or normalized_item.get("school")
        normalized_item["obtained_date"] = normalized_item.get("obtained_date") or normalized_item.get("date_obtention")
        normalized_item["date_obtention"] = normalized_item.get("date_obtention") or normalized_item.get("obtained_date")
        normalized_items.append(normalized_item)
    return normalized_items


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
    data["telephone"] = data["phone"]
    data["location"] = parsed.data.get("location") or None
    data["ville"] = parsed.data.get("ville") or data["location"]
    data["linkedin"] = data["linkedin_url"]
    data["entreprise_actuelle"] = data["current_company"]
    data["poste_actuel"] = data["current_title"]
    data["experience_totale"] = data["total_experience_years"]
    data["experiences_detaillees"] = data["detailed_experience"]
    data["diplomes"] = data["education"]
    data["competences"] = data["skills"]
    data["technical_skills"] = parsed.data.get("technical_skills") or data["skills"]
    data["competences_techniques"] = parsed.data.get("competences_techniques") or data["skills"]
    data["functional_skills"] = parsed.data.get("functional_skills") or []
    data["competences_fonctionnelles"] = parsed.data.get("competences_fonctionnelles") or data["functional_skills"]
    data["langues"] = data["languages"]
    data["sexe"] = data["gender"]
    data["parser_used"] = "heuristic"
    data["parser_confidence"] = parsed.confidence_score
    return ParsedCV(data=data, confidence_score=parsed.confidence_score)
