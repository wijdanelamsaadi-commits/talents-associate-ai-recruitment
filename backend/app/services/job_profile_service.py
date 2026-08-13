import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from app.data.job_reference_titles import JOB_REFERENCE_TITLES


@dataclass(frozen=True)
class JobProfileClassification:
    title: str | None
    confidence: float
    score: int
    matched_terms: list[str]


ROLE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Data Analyst": (
        "data analyst", "analyse de donnees", "analyse donnees", "power bi", "tableau", "sql",
        "reporting", "dashboard", "dashboards", "kpi", "business intelligence", "bi",
    ),
    "Data Scientist": (
        "data scientist", "machine learning", "deep learning", "modelisation", "python",
        "scikit", "tensorflow", "pytorch", "statistique", "predictif",
    ),
    "Data Engineer": (
        "data engineer", "etl", "pipeline data", "data warehouse", "spark", "hadoop",
        "airflow", "bigquery", "snowflake",
    ),
    "DevOps Engineer": (
        "devops", "ci cd", "ci/cd", "docker", "kubernetes", "cloud", "ansible",
        "terraform", "jenkins", "github actions", "deploiement", "automatisation",
    ),
    "Cloud Engineer": (
        "cloud engineer", "aws", "azure", "gcp", "cloud", "infrastructure cloud",
        "serverless", "kubernetes",
    ),
    "Cybersecurity Engineer": (
        "cybersecurity", "cybersecurite", "securite informatique", "soc", "siem",
        "pentest", "vulnerability", "incident response",
    ),
    "Développeur Full Stack": (
        "developpeur full stack", "full stack", "fullstack", "react", "node", "php",
        "laravel", "fastapi", "backend", "frontend", "javascript", "typescript",
    ),
    "Développeur Back-End": (
        "backend", "back end", "api", "fastapi", "django", "spring", "node", "php", "laravel",
    ),
    "Développeur Front-End": (
        "frontend", "front end", "react", "vue", "angular", "javascript", "typescript", "html", "css",
    ),
    "Software Engineer": (
        "software engineer", "genie logiciel", "developpement logiciel", "java", "python",
        "architecture logicielle", "api",
    ),
    "Comptable": (
        "comptable", "comptabilite", "ecritures comptables", "bilan", "tva",
        "lettrage", "rapprochement bancaire", "sage", "facturation",
    ),
    "Responsable Comptable": (
        "responsable comptable", "supervision comptable", "cloture comptable", "bilan",
        "management comptable",
    ),
    "Contrôleur de Gestion": (
        "controleur de gestion", "controle de gestion", "budget", "reporting financier",
        "analyse des ecarts", "tableaux de bord", "forecast",
    ),
    "Chargé de Recrutement": (
        "charge de recrutement", "recrutement", "sourcing", "entretiens rh", "ats",
        "selection candidats",
    ),
    "Responsable RH": (
        "responsable rh", "ressources humaines", "gestion rh", "droit social",
        "formation", "paie", "gpec",
    ),
    "Product Manager": (
        "product manager", "roadmap", "strategie produit", "go to market", "product strategy",
        "discovery", "user stories",
    ),
    "Product Owner": (
        "product owner", "scrum", "backlog", "user stories", "sprint", "agile",
    ),
    "Chef de Projet": (
        "chef de projet", "project manager", "gestion de projet", "planning", "budget projet",
        "coordination projet",
    ),
    "Business Analyst": (
        "business analyst", "analyse fonctionnelle", "besoins metier", "processus metier",
        "specifications fonctionnelles",
    ),
    "Responsable Qualité": (
        "responsable qualite", "qualite", "iso 9001", "audit qualite", "amelioration continue",
    ),
    "Responsable HSE": (
        "responsable hse", "hse", "qhse", "securite au travail", "environnement",
    ),
}


def get_job_reference_titles() -> list[str]:
    return list(JOB_REFERENCE_TITLES)


def is_reference_title(value: str | None) -> bool:
    normalized_value = _normalize(value)
    return bool(normalized_value) and any(_normalize(title) == normalized_value for title in JOB_REFERENCE_TITLES)


def classify_candidate_profile(parsed_data: dict[str, Any] | None, raw_text: str | None = None) -> JobProfileClassification:
    payload = parsed_data or {}
    profile_text = _build_profile_text(payload, raw_text)
    normalized_text = _normalize(profile_text)
    existing_title = _string_value(payload.get("current_title") or payload.get("poste_actuel"))

    scores: list[tuple[int, str, list[str]]] = []
    for title in JOB_REFERENCE_TITLES:
        matched_terms = _matched_terms_for_title(title, normalized_text, existing_title)
        token_score = _title_token_score(title, normalized_text)
        score = min(100, (len(matched_terms) * 18) + token_score)
        if existing_title and _normalize(existing_title) == _normalize(title):
            score = max(score, 95)
            matched_terms.append(existing_title)
        if score > 0:
            scores.append((score, title, sorted(set(matched_terms))))

    if not scores:
        return JobProfileClassification(title=None, confidence=0.0, score=0, matched_terms=[])

    scores.sort(key=lambda item: (item[0], _specificity(item[1])), reverse=True)
    best_score, best_title, best_terms = scores[0]
    if best_score < 24:
        return JobProfileClassification(title=None, confidence=0.0, score=best_score, matched_terms=best_terms)
    confidence = round(min(0.99, best_score / 100), 2)
    return JobProfileClassification(title=best_title, confidence=confidence, score=best_score, matched_terms=best_terms)


def enrich_parsed_data_with_profile(parsed_data: dict[str, Any], raw_text: str | None = None) -> JobProfileClassification:
    classification = classify_candidate_profile(parsed_data, raw_text)
    if classification.title:
        parsed_data["identified_job_profile"] = classification.title
        parsed_data["job_profile_confidence"] = classification.confidence
        parsed_data["job_profile_matched_terms"] = classification.matched_terms
    return classification


def _build_profile_text(payload: dict[str, Any], raw_text: str | None) -> str:
    parts = [
        payload.get("current_title"),
        payload.get("poste_actuel"),
        payload.get("summary"),
        payload.get("sector"),
        payload.get("secteur"),
        payload.get("skills"),
        payload.get("competences"),
        payload.get("technical_skills"),
        payload.get("competences_techniques"),
        payload.get("soft_skills"),
        payload.get("experience"),
        payload.get("detailed_experience"),
        payload.get("experiences_detaillees"),
        payload.get("education"),
        payload.get("diplomes"),
        raw_text,
    ]
    return " ".join(_flatten_text(part) for part in parts if part)


def _matched_terms_for_title(title: str, normalized_text: str, existing_title: str | None) -> list[str]:
    terms = set(ROLE_KEYWORDS.get(title, ()))
    terms.update(_title_variants(title))
    if existing_title:
        terms.update(_title_variants(existing_title))
    return [term for term in terms if _term_in_text(term, normalized_text)]


def _title_token_score(title: str, normalized_text: str) -> int:
    tokens = {token for token in _normalize(title).split() if len(token) > 2}
    if not tokens:
        return 0
    matched = {token for token in tokens if re.search(rf"\b{re.escape(token)}\b", normalized_text)}
    if not matched:
        return 0
    return round((len(matched) / len(tokens)) * 22)


def _title_variants(title: str) -> set[str]:
    normalized = _normalize(title)
    variants = {normalized}
    if "developpeur" in normalized:
        variants.add(normalized.replace("developpeur", "developer"))
    if "ingenieur" in normalized:
        variants.add(normalized.replace("ingenieur", "engineer"))
    if normalized == "devops engineer":
        variants.add("devops")
    return variants


def _term_in_text(term: str, normalized_text: str) -> bool:
    normalized_term = _normalize(term).replace("/", " ")
    normalized_term = re.sub(r"\s+", " ", normalized_term).strip()
    if not normalized_term:
        return False
    return re.search(rf"\b{re.escape(normalized_term)}\b", normalized_text) is not None


def _specificity(title: str) -> int:
    return len(_normalize(title).split())


def _flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(_flatten_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    return str(value)


def _string_value(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalize(value: str | None) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("’", "'").replace("-", " ").replace("_", " ").replace("/", " ")
    text = re.sub(r"[^a-z0-9+#.]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()
