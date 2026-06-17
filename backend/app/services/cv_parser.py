import re
from dataclasses import dataclass
from typing import Any


EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?:(?:\+|00)\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,5}\d{2,4}")

SECTION_ALIASES = {
    "skills": {"skills", "technical skills", "core skills", "competencies", "technologies"},
    "languages": {"languages", "language skills"},
    "education": {"education", "academic background", "academic history", "formation"},
    "experience": {"experience", "work experience", "professional experience", "employment history", "career history"},
    "certifications": {"certifications", "certificates", "licenses", "certification"},
}

KNOWN_SKILLS = {
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
    "machine learning",
    "nlp",
    "data analysis",
}

KNOWN_LANGUAGES = {
    "arabic",
    "french",
    "english",
    "spanish",
    "german",
    "italian",
    "amazigh",
}


@dataclass(frozen=True)
class ParsedCV:
    data: dict[str, Any]
    confidence_score: float


def parse_cv_text(raw_text: str) -> ParsedCV:
    normalized_text = _normalize_text(raw_text)
    sections = _detect_sections(normalized_text)

    email = _first_match(EMAIL_PATTERN, normalized_text)
    phone = _extract_phone(normalized_text)
    first_name, last_name = _extract_name(normalized_text, email)

    skills = _extract_skills(normalized_text, sections.get("skills", ""))
    languages = _extract_languages(normalized_text, sections.get("languages", ""))
    education = _extract_section_items(sections.get("education", ""))
    experience = _extract_section_items(sections.get("experience", ""))
    certifications = _extract_section_items(sections.get("certifications", ""))

    parsed = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "languages": languages,
        "education": education,
        "experience": experience,
        "certifications": certifications,
    }

    return ParsedCV(data=parsed, confidence_score=_estimate_confidence(parsed))


def _normalize_text(raw_text: str) -> str:
    lines = [line.strip() for line in raw_text.replace("\r", "\n").splitlines()]
    return "\n".join(line for line in lines if line)


def _first_match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group(0).strip() if match else ""


def _extract_phone(text: str) -> str:
    for match in PHONE_PATTERN.finditer(text):
        candidate = match.group(0).strip(" .-")
        digits = re.sub(r"\D", "", candidate)
        if 8 <= len(digits) <= 15:
            return candidate
    return ""


def _extract_name(text: str, email: str) -> tuple[str, str]:
    for line in text.splitlines()[:8]:
        if EMAIL_PATTERN.search(line) or PHONE_PATTERN.search(line):
            continue
        words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ'-]{2,}", line)
        if 2 <= len(words) <= 4:
            return words[0], " ".join(words[1:])

    if email:
        local_part = email.split("@", 1)[0]
        tokens = [token for token in re.split(r"[._-]+", local_part) if token]
        if len(tokens) >= 2:
            return tokens[0].title(), tokens[1].title()

    return "", ""


def _detect_sections(text: str) -> dict[str, str]:
    lines = text.splitlines()
    heading_positions: list[tuple[int, str]] = []

    for index, line in enumerate(lines):
        normalized_heading = re.sub(r"[:\-]+$", "", line.strip().lower())
        for canonical_name, aliases in SECTION_ALIASES.items():
            if normalized_heading in aliases:
                heading_positions.append((index, canonical_name))
                break

    sections: dict[str, str] = {}
    for position, (start_index, section_name) in enumerate(heading_positions):
        end_index = heading_positions[position + 1][0] if position + 1 < len(heading_positions) else len(lines)
        sections[section_name] = "\n".join(lines[start_index + 1 : end_index]).strip()

    return sections


def _extract_skills(full_text: str, skills_section: str) -> list[str]:
    search_text = f"{skills_section}\n{full_text}".lower()
    found = {skill for skill in KNOWN_SKILLS if re.search(rf"\b{re.escape(skill)}\b", search_text)}

    for item in _split_inline_items(skills_section):
        if 1 <= len(item.split()) <= 4:
            found.add(item)

    return sorted(_title_preserving_items(found))


def _extract_languages(full_text: str, languages_section: str) -> list[str]:
    search_text = f"{languages_section}\n{full_text}".lower()
    found = {language for language in KNOWN_LANGUAGES if re.search(rf"\b{re.escape(language)}\b", search_text)}

    for item in _split_inline_items(languages_section):
        clean_item = item.split("(", 1)[0].strip()
        if clean_item.lower() in KNOWN_LANGUAGES:
            found.add(clean_item.lower())

    return sorted(_title_preserving_items(found))


def _extract_section_items(section_text: str) -> list[str]:
    items = []
    for line in section_text.splitlines():
        clean_line = re.sub(r"^[\-*•\d.)\s]+", "", line).strip()
        if clean_line:
            items.append(clean_line)
    return items[:20]


def _split_inline_items(section_text: str) -> set[str]:
    items = set()
    for raw_item in re.split(r"[,;|/]", section_text):
        clean_item = raw_item.strip(" \n\t-•").lower()
        if clean_item:
            items.add(clean_item)
    return items


def _title_preserving_items(items: set[str]) -> set[str]:
    titled = set()
    for item in items:
        if item in {"html", "css", "sql", "nlp"}:
            titled.add(item.upper())
        elif item in {"node.js"}:
            titled.add("Node.js")
        else:
            titled.add(item.title())
    return titled


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
    if parsed["education"]:
        score += 0.1
    if parsed["experience"]:
        score += 0.1
    if parsed["languages"]:
        score += 0.05
    return round(min(score, 1.0), 2)
