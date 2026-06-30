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
