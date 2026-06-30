import re
from dataclasses import dataclass
from typing import Any


EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?:(?:\+|00)\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,5}\d{2,4}")

SECTION_ALIASES = {
    "skills": {
        "skills",
        "technical skills",
        "core skills",
        "competencies",
        "technologies",
        "competences",
        "competences et outils",
        "competences techniques",
        "outils informatiques et bureautiques",
        "programmation et bases de donnees",
        "savoir etre",
        "savoir-être",
        "soft skills",
    },
    "languages": {"languages", "language skills", "langues", "langue"},
    "education": {
        "education",
        "academic background",
        "academic history",
        "formation",
        "formations",
        "diplome",
        "diplomes",
        "diplôme",
        "diplômes",
        "parcours academique",
    },
    "experience": {
        "experience",
        "experiences",
        "work experience",
        "professional experience",
        "employment history",
        "career history",
        "experience professionnelle",
        "experiences professionnelles",
        "projets academiques",
    },
    "certifications": {"certifications", "certificates", "licenses", "certification", "certificats", "certificat"},
}

KNOWN_SKILLS = {
    "ai",
    "ia",
    "n8n",
    "php",
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "vite",
    "node.js",
    "fastapi",
    "django",
    "flask",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "docker",
    "git",
    "github",
    "html",
    "css",
    "tailwind",
    "excel",
    "power bi",
    "tableau",
    "cloud",
    "devops",
    "data",
    "data engineering",
    "deep learning",
    "machine learning",
    "nlp",
    "data analysis",
    "matlab",
    "c",
    "microsoft office",
    "word",
    "powerpoint",
    "excel vba",
    "microsoft access",
    "access",
    "minitab",
    "automates programmables",
    "tia portal",
    "automation studio p7",
    "arduino",
    "catia v5",
    "catia",
    "iso 9001",
    "iatf 16949",
    "8d",
    "qrqc",
    "qqoqcp",
    "doe",
    "5 why",
    "odoo",
    "erp",
    "gmao",
    "vsm",
    "teamwork",
    "communication",
    "coordination",
    "adaptability",
    "adaptabilite",
    "leadership",
    "problem solving",
}

KNOWN_LANGUAGES = {
    "arabic",
    "arabe",
    "french",
    "francais",
    "français",
    "english",
    "anglais",
    "spanish",
    "espagnol",
    "german",
    "allemand",
    "italian",
    "italien",
    "amazigh",
}

KNOWN_FUNCTIONAL_SKILLS = {
    "gestion de la qualite",
    "gestion de la qualité",
    "amelioration continue",
    "amélioration continue",
    "supply chain",
    "logistique",
    "planification",
    "approvisionnement",
    "maintenance",
    "organisation",
    "adaptation",
    "initiative",
    "management",
    "teamwork",
    "communication",
    "coordination",
    "adaptability",
    "adaptabilite",
    "leadership",
    "problem solving",
}

KNOWN_CITIES = {
    "casablanca",
    "rabat",
    "el jadida",
    "marrakech",
    "tanger",
    "fes",
    "fès",
    "meknes",
    "agadir",
    "kenitra",
    "settat",
    "mohammedia",
    "safi",
    "oujda",
}

COMMON_FIRST_NAMES = {
    "marwa",
    "mawa",
    "wijdane",
    "oumaima",
    "fatima",
    "imane",
    "ikram",
    "sara",
    "sarah",
    "aya",
    "hajar",
    "nada",
    "yasmine",
    "mohamed",
    "mohammed",
    "ahmed",
    "amine",
    "anas",
    "ayoub",
    "youssef",
    "mehdi",
}

BROKEN_WORD_REPAIRS = {
    "T eam w ork": "Teamwork",
    "T eamwork": "Teamwork",
    "Comm unication": "Communication",
    "Co ordination": "Coordination",
    "A daptabilit y": "Adaptability",
    "A daptability": "Adaptability",
    "P ython": "Python",
    "M ySQL": "MySQL",
    "J avaScript": "JavaScript",
    "F astAPI": "FastAPI",
}

KNOWN_REPAIR_WORDS = {
    "teamwork",
    "communication",
    "coordination",
    "adaptability",
    "adaptabilite",
    "leadership",
    "python",
    "fastapi",
    "javascript",
    "typescript",
    "mysql",
    "postgresql",
    "devops",
    "cloud",
}


@dataclass(frozen=True)
class ParsedCV:
    data: dict[str, Any]
    confidence_score: float


def parse_cv_text(raw_text: str) -> ParsedCV:
    normalized_text = _normalize_text(raw_text)
    sections = _detect_sections(normalized_text)

    email = _extract_email(normalized_text)
    phone = _extract_phone(normalized_text)
    first_name, last_name = _extract_name(normalized_text, email)
    city = _extract_city(normalized_text)

    skills = _extract_skills(normalized_text, sections.get("skills", ""))
    functional_skills = _extract_functional_skills(normalized_text)
    languages = _extract_languages(normalized_text, sections.get("languages", ""))
    education = _extract_section_items(sections.get("education", ""), normalized_text, "education")
    experience = _extract_section_items(sections.get("experience", ""), normalized_text, "experience")
    certifications = _extract_section_items(sections.get("certifications", ""), normalized_text, "certifications")
    current_title = _extract_current_title(normalized_text)

    parsed = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "location": city,
        "ville": city,
        "current_title": current_title,
        "poste_actuel": current_title,
        "skills": skills,
        "technical_skills": skills,
        "competences": skills,
        "competences_techniques": skills,
        "functional_skills": functional_skills,
        "competences_fonctionnelles": functional_skills,
        "languages": languages,
        "langues": languages,
        "education": education,
        "diplomes": education,
        "experience": experience,
        "detailed_experience": _extract_detailed_experience(experience),
        "experiences_detaillees": _extract_detailed_experience(experience),
        "certifications": certifications,
    }

    return ParsedCV(data=parsed, confidence_score=_estimate_confidence(parsed))


def _normalize_text(raw_text: str) -> str:
    lines = [_repair_spaced_line(line.strip()) for line in raw_text.replace("\r", "\n").splitlines()]
    return "\n".join(line for line in lines if line)


def _repair_spaced_line(line: str) -> str:
    if not line:
        return ""

    line = _repair_known_spaced_words(line)
    tokens = line.split()
    if len(tokens) < 4:
        return _repair_known_spaced_words(line)

    short_tokens = sum(1 for token in tokens if len(token.strip(".,:;()[]{}'’\"-–/")) <= 1)
    if short_tokens / len(tokens) < 0.6:
        return _repair_known_spaced_words(line)

    repaired_parts = []
    for part in re.split(r"\s{2,}", line):
        clean_part = part.strip()
        if not clean_part:
            continue
        if re.fullmatch(r"[-–—/:|]+", clean_part):
            repaired_parts.append(clean_part)
        else:
            repaired_parts.append(re.sub(r"(?<=\S)\s(?=\S)", "", clean_part))

    repaired = " ".join(repaired_parts)
    repaired = re.sub(r"\s+([,.;:!?)])", r"\1", repaired)
    repaired = re.sub(r"([(])\s+", r"\1", repaired)
    return _repair_known_spaced_words(repaired.strip())


def _repair_known_spaced_words(text: str) -> str:
    repaired = text
    for broken, fixed in BROKEN_WORD_REPAIRS.items():
        repaired = re.sub(re.escape(broken), fixed, repaired, flags=re.IGNORECASE)

    for word in KNOWN_REPAIR_WORDS:
        pattern = r"\b" + r"\s*".join(re.escape(char) for char in word) + r"\b"
        replacement = _format_repaired_word(word)
        repaired = re.sub(pattern, replacement, repaired, flags=re.IGNORECASE)
    return repaired


def _format_repaired_word(word: str) -> str:
    labels = {
        "fastapi": "FastAPI",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "mysql": "MySQL",
        "postgresql": "PostgreSQL",
        "devops": "DevOps",
        "teamwork": "Teamwork",
        "communication": "Communication",
        "coordination": "Coordination",
        "adaptability": "Adaptability",
        "adaptabilite": "Adaptabilité",
        "leadership": "Leadership",
        "python": "Python",
        "cloud": "Cloud",
    }
    return labels.get(word, word)


def _first_match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group(0).strip() if match else ""


def _extract_email(text: str) -> str:
    match = EMAIL_PATTERN.search(text)
    if not match:
        return ""
    email = match.group(0).strip()
    email = re.sub(r"\.(com|net|org|ma|fr|io|co|edu|gov)(?:tel|t)$", r".\1", email, flags=re.IGNORECASE)
    return email


def _extract_phone(text: str) -> str:
    for match in PHONE_PATTERN.finditer(text):
        candidate = match.group(0).strip(" .-")
        digits = re.sub(r"\D", "", candidate)
        if 8 <= len(digits) <= 15:
            return candidate
    return ""


def _extract_city(text: str) -> str:
    normalized_text = _strip_accents(text.lower())
    for city in KNOWN_CITIES:
        if re.search(rf"\b{re.escape(_strip_accents(city.lower()))}\b", normalized_text):
            return city.title()
    return ""


def _extract_name(text: str, email: str) -> tuple[str, str]:
    for line in text.splitlines()[:8]:
        if EMAIL_PATTERN.search(line) or PHONE_PATTERN.search(line):
            continue
        words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ'-]{2,}", line)
        if 2 <= len(words) <= 4:
            if _strip_accents(words[-1].lower()) in COMMON_FIRST_NAMES:
                return words[-1], " ".join(words[:-1])
            return words[0], " ".join(words[1:])

    if email:
        local_part = email.split("@", 1)[0]
        tokens = [token for token in re.split(r"[._-]+", local_part) if token]
        if len(tokens) >= 2:
            return tokens[0].title(), tokens[1].title()

    return "", ""


def _detect_sections(text: str) -> dict[str, str]:
    lines = text.splitlines()
    heading_positions: list[tuple[int, str, str]] = []

    for index, line in enumerate(lines):
        raw_heading = line.strip()
        inline_content = ""
        split_parts = re.split(r"\s*[:|]\s*", raw_heading, maxsplit=1)
        heading_part = split_parts[0]
        if len(split_parts) == 2:
            inline_content = split_parts[1]
        else:
            split_match = re.match(r"^(.{2,45}?)[\s\-–—]{2,}(.+)$", raw_heading)
            if split_match:
                heading_part = split_match.group(1)
                inline_content = split_match.group(2)
        normalized_heading = _strip_accents(re.sub(r"[:\-–—]+$", "", heading_part.strip().lower()))
        for canonical_name, aliases in SECTION_ALIASES.items():
            normalized_aliases = {_strip_accents(alias.lower()) for alias in aliases}
            if normalized_heading in normalized_aliases:
                heading_positions.append((index, canonical_name, inline_content.strip()))
                break

    sections: dict[str, str] = {}
    for position, (start_index, section_name, inline_content) in enumerate(heading_positions):
        end_index = heading_positions[position + 1][0] if position + 1 < len(heading_positions) else len(lines)
        body_lines = [inline_content] if inline_content else []
        body_lines.extend(lines[start_index + 1 : end_index])
        sections[section_name] = "\n".join(line for line in body_lines if line).strip()

    return sections


def _extract_skills(full_text: str, skills_section: str) -> list[str]:
    search_text = _strip_accents(f"{skills_section}\n{full_text}".lower())
    found = {
        skill
        for skill in KNOWN_SKILLS
        if re.search(rf"\b{re.escape(_strip_accents(skill.lower()))}\b", search_text)
    }

    for item in _split_inline_items(skills_section):
        if 1 <= len(item.split()) <= 4:
            found.add(item)

    return sorted(_title_preserving_items(found))


def _extract_functional_skills(full_text: str) -> list[str]:
    search_text = _strip_accents(full_text.lower())
    found = {
        skill
        for skill in KNOWN_FUNCTIONAL_SKILLS
        if re.search(rf"\b{re.escape(_strip_accents(skill.lower()))}\b", search_text)
    }
    return sorted(_title_preserving_items(found))


def _extract_languages(full_text: str, languages_section: str) -> list[str]:
    search_text = _strip_accents(f"{languages_section}\n{full_text}".lower())
    found = {
        language
        for language in KNOWN_LANGUAGES
        if re.search(rf"\b{re.escape(_strip_accents(language.lower()))}\b", search_text)
    }

    for item in _split_inline_items(languages_section):
        clean_item = item.split("(", 1)[0].strip()
        if clean_item.lower() in KNOWN_LANGUAGES:
            found.add(clean_item.lower())

    return sorted(_title_preserving_items(found))


def _extract_current_title(text: str) -> str:
    title_patterns = (
        r"(eleve ingenieure?.{0,90})",
        r"(élève ingénieure?.{0,90})",
        r"(ingenieure?.{0,90})",
        r"(développeur.{0,90})",
        r"(developpeur.{0,90})",
        r"(data analyst.{0,90})",
    )
    normalized_text = _strip_accents(text.lower())
    for pattern in title_patterns:
        match = re.search(pattern, normalized_text)
        if match:
            raw_value = text[match.start() : match.end()]
            return raw_value.strip(" .,:;")
    return ""


def _extract_detailed_experience(experience_items: list[str]) -> list[dict[str, str | None]]:
    detailed = []
    for item in experience_items:
        if not item:
            continue
        company = None
        title = item
        match = re.search(r"\b(?:stage|projet).{0,80}?[–-]\s*([^()]+)", item, flags=re.IGNORECASE)
        if match:
            company = match.group(1).strip(" .,:;")
        detailed.append(
            {
                "title": title,
                "poste": title,
                "company": company,
                "entreprise": company,
                "start_date": None,
                "date_debut": None,
                "end_date": None,
                "date_fin": None,
                "description": item,
            }
        )
    return detailed[:20]


def _extract_section_items(section_text: str, full_text: str = "", section_type: str = "") -> list[str]:
    items = []
    for line in section_text.splitlines():
        clean_line = re.sub(r"^[\-*•\d.)\s]+", "", line).strip()
        if clean_line:
            items.append(_clean_extracted_item(clean_line))
    if not items and full_text and section_type:
        items = _extract_fallback_section_items(full_text, section_type)
    return _dedupe_preserve_order(items)[:20]


def _extract_fallback_section_items(full_text: str, section_type: str) -> list[str]:
    patterns: dict[str, tuple[str, ...]] = {
        "education": (
            r"\b(?:dipl[oô]me|diploma|master|licence|bachelor|baccalaur[eé]at|formation|universit[eé]|[ée]cole|institut|ing[eé]nieur)\b",
            r"\b(?:dut|bts|deug|deust|mba|phd|doctorat)\b",
        ),
        "experience": (
            r"\b(?:exp[eé]rience|stage|internship|emploi|poste|projet|mission|responsable|d[eé]veloppeur|developer|engineer|ing[eé]nieur|consultant|analyst|analyste)\b",
            r"\b(?:janvier|f[eé]vrier|mars|avril|mai|juin|juillet|ao[uû]t|septembre|octobre|novembre|d[eé]cembre|20\d{2}|19\d{2})\b.*\b(?:stage|projet|mission|poste|emploi)\b",
        ),
        "certifications": (
            r"\b(?:certification|certificat|certificate|license|licence professionnelle|coursera|udemy|aws|azure|google|scrum|pmp|cisco|oracle)\b",
        ),
    }
    selected_patterns = patterns.get(section_type, ())
    if not selected_patterns:
        return []

    items: list[str] = []
    for line in full_text.splitlines():
        clean_line = re.sub(r"^[\-*•\d.)\s]+", "", line).strip()
        if len(clean_line) < 4 or len(clean_line) > 220:
            continue
        normalized_line = _strip_accents(clean_line.lower())
        if any(re.search(pattern, normalized_line, flags=re.IGNORECASE) for pattern in selected_patterns):
            items.append(_clean_extracted_item(clean_line))
    return items


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        clean_item = _clean_extracted_item(item)
        key = _strip_accents(clean_item.lower())
        if clean_item and key not in seen:
            seen.add(key)
            deduped.append(clean_item)
    return deduped


def _split_inline_items(section_text: str) -> set[str]:
    items = set()
    for raw_item in re.split(r"[,;|/\n]", section_text):
        clean_item = raw_item.strip(" \n\t-•").lower()
        if clean_item:
            items.add(clean_item)
    return items


def _clean_extracted_item(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" \n\t-â€¢•")


def _title_preserving_items(items: set[str]) -> set[str]:
    titled = set()
    seen = set()
    for item in sorted(items):
        normalized_item = item.lower()
        dedupe_key = _strip_accents(normalized_item)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        if normalized_item in {"html", "css", "sql", "nlp", "ia", "ai", "vba", "erp", "gmao", "vsm", "doe"}:
            titled.add(item.upper())
        elif normalized_item in {"mysql"}:
            titled.add("MySQL")
        elif normalized_item in {"matlab"}:
            titled.add("MATLAB")
        elif normalized_item in {"n8n"}:
            titled.add("n8n")
        elif normalized_item in {"php"}:
            titled.add("PHP")
        elif normalized_item in {"node.js"}:
            titled.add("Node.js")
        elif normalized_item in {"power bi"}:
            titled.add("Power BI")
        elif normalized_item in {"excel vba"}:
            titled.add("Excel VBA")
        elif normalized_item in {"catia v5"}:
            titled.add("CATIA V5")
        elif normalized_item in {"tia portal"}:
            titled.add("TIA Portal")
        elif normalized_item in {"iatf 16949"}:
            titled.add("IATF 16949")
        elif normalized_item in {"iso 9001"}:
            titled.add("ISO 9001")
        elif normalized_item in {"5 why"}:
            titled.add("5 Why")
        elif normalized_item in {"8d"}:
            titled.add("8D")
        elif normalized_item in {"qrqc", "qqoqcp"}:
            titled.add(normalized_item.upper())
        else:
            titled.add(item.title())
    return titled


def _strip_accents(value: str) -> str:
    replacements = str.maketrans(
        {
            "à": "a",
            "â": "a",
            "ä": "a",
            "á": "a",
            "ã": "a",
            "å": "a",
            "ç": "c",
            "é": "e",
            "è": "e",
            "ê": "e",
            "ë": "e",
            "í": "i",
            "ì": "i",
            "î": "i",
            "ï": "i",
            "ñ": "n",
            "ó": "o",
            "ò": "o",
            "ô": "o",
            "ö": "o",
            "õ": "o",
            "ù": "u",
            "û": "u",
            "ü": "u",
            "ú": "u",
            "ý": "y",
            "ÿ": "y",
            "’": "'",
        }
    )
    return value.translate(replacements)


def _estimate_confidence(parsed: dict[str, Any]) -> float:
    score = 0.0
    if parsed["first_name"] and parsed["last_name"]:
        score += 0.2
    if parsed["email"]:
        score += 0.2
    if parsed["phone"]:
        score += 0.15
    if parsed["skills"]:
        score += 0.2
    if parsed.get("location"):
        score += 0.05
    if parsed["education"]:
        score += 0.1
    if parsed["experience"]:
        score += 0.1
    if parsed["languages"]:
        score += 0.05
    return round(min(score, 1.0), 2)
