"""
cv_name_cleaner.py — Validation and recovery of candidate first/last names.

A name is considered INVALID if:
- It is empty or a single character.
- Any word in it matches the SECTION_HEADER_BLOCKLIST (section headers, hobbies,
  marital status, soft-skill keywords, professions, cities, countries, etc.).
- It matches a known BLOCKED_NAME_PHRASES.
- It is longer than 60 characters (no real name is that long).
- It contains digits.
- It contains only uppercase letters that form an acronym (e.g. "RRH", "ADV", "DRH").
"""

import re
import unicodedata
from pathlib import Path


def strip_accents(text: str) -> str:
    if not text:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    ).lower()


# ---------------------------------------------------------------------------
# BLOCKLIST — any token matching this cannot be part of a person's name
# ---------------------------------------------------------------------------
SECTION_HEADER_BLOCKLIST: set[str] = {
    # ── CV Section headers ────────────────────────────────────────────────
    "langue", "langues", "language", "languages",
    "permis", "conduire", "licence", "license",
    "diplome", "diplomes", "education", "formation", "formations",
    "baccalaureat", "bac",
    "experience", "experiences", "professionnel", "professionnels",
    "professionnelle", "professionnelles", "work", "employment", "career", "parcours",
    "competence", "competences", "skill", "skills",
    "technique", "techniques", "soft", "savoir",
    "certification", "certifications", "certificat", "certificats",
    "profil", "profile", "summary", "resume", "contact", "coordonnees",
    "projet", "projets", "projects",
    "loisir", "loisirs", "hobby", "hobbies", "divers",
    "reference", "references",
    "interet", "interets", "atout", "atouts",
    "objectif", "objectifs", "mission", "missions",
    "tache", "taches",
    "realise", "realisees", "realisees",
    "informations", "infos", "autres",
    "qualification", "qualifications",
    "maitrise", "maitrise",
    "propos", "mon", "moi",
    "presentation", "apropos",
    # ── Marital / personal status ─────────────────────────────────────────
    "celibataire", "marie", "mariee", "divorce", "divorcee",
    "veuf", "veuve", "concubinage", "situation", "familiale", "civil", "etat",
    "nationalite", "nationalit", "marocain", "marocaine", "marocains",
    "ans", "age", "nee", "ne",
    # ── Languages ─────────────────────────────────────────────────────────
    "berbere", "berberes", "arabe", "anglais", "francais", "espagnol",
    "allemand", "italien", "portugais", "chinois", "russe",
    "bilingue", "trilingual", "courant", "courants", "notions",
    # ── Hobbies / interests / activities ─────────────────────────────────
    "voyage", "voyages", "sport", "sports", "lecture", "musique", "cinema",
    "football", "natation", "tennis", "basket", "fitness", "yoga",
    "internet", "gaming", "jeux", "jeu", "cuisine", "photographie",
    "dessin", "peinture", "danse", "theatre", "bénévolat", "benevolat",
    "randonnee", "escalade", "ski", "surf", "arts", "graphiques",
    "culturel", "culturelle", "artistique", "artistiques",
    # ── Education / academic ──────────────────────────────────────────────
    "gestion", "science", "sciences", "economique", "economiques", "economie",
    "academic", "academique", "academiques",
    "fsjes", "faculte", "universite", "lycee", "ecole", "centre",
    "master", "licence", "doctorat", "dess", "deug", "dut", "bts",
    "ingenieur", "ingenieure",
    "grade", "mention", "bien", "assez", "serie", "physique", "chimie",
    "obtention", "juillet", "depuis", "juin",
    "maille", "tex",
    # ── Job titles & professional functions ───────────────────────────────
    "responsable", "directeur", "directrice", "chef", "consultant", "consultante",
    "technicien", "technicienne", "assistant", "assistante",
    "specialiste", "stage", "stagiaire", "pfe",
    "administrateur", "administratrice",
    "commercial", "commerciale", "commerciaux",
    "manager", "manageur", "manageure", "project", "account",
    "analyst", "analyste", "charge", "chargee",
    "secretaire", "secretariat", "accueil",
    "directeur", "direction",
    "logistique", "achats", "achat",
    "rh", "drh", "rrh", "adv", "daf",
    "juridique", "assistance",
    "sales", "marketing", "brand", "content", "digital", "agency",
    "research", "market", "web", "developpement",
    "coordinateur", "coordinateurs", "chauffeurs", "camions",
    "culinaire", "art",
    "rayon", "grande", "surface",
    # ── Financial / accounting ────────────────────────────────────────────
    "finance", "comptabilite", "comptable", "cnss", "declaration",
    "informatique", "bureautique",
    "ressources", "humaines", "production", "methode", "methodes",
    "automatisme", "automatismes", "electromecanique", "electrique", "electronique",
    "maintenance", "industrielle", "industriel", "qualite",
    "reseaux", "telecom",
    # ── Soft skills / qualities ───────────────────────────────────────────
    "vente", "ventes", "esprit", "equipe", "capacite", "relation",
    "relations", "clientele", "relationnel", "relationnelles",
    "bon", "bonne", "bons", "bonnes",
    "organisation", "fournisseurs", "fournisseur",
    "reporting", "elaboration", "analyse", "management",
    "sens", "continuelle", "continue",
    "motivation", "dynamique", "autonome", "rigoureux",
    "rigueur", "serieux",
    "principaux", "principaux", "principales", "principales",
    "fort", "forts", "forts", "points",
    "qualite", "qualites", "sociales",
    "compreh", "comprehension", "approfond",
    # ── Cities & Countries ────────────────────────────────────────────────
    "casablanca", "rabat", "marrakech", "tanger", "fes", "meknes",
    "agadir", "oujda", "kenitra", "safi", "mohammedia", "tetouan",
    "bouskoura", "berrechid", "deroua", "temara",
    "maroc", "morocco", "france", "algerie", "tunisie", "senegal",
    "espagne", "italie", "canada",
    "ain", "sbaa", "noussair", "hay", "cite", "bloc", "imm", "rue", "lot",
    # ── Tools / Software ─────────────────────────────────────────────────
    "word", "excel", "powerpoint", "outlook", "office", "ms", "package",
    "sage", "sap", "erp", "crm", "autocad", "solidworks",
    "python", "java", "sql", "html", "css", "php", "javascript",
    "logiciel", "logiciels",
    # ── Miscellaneous non-name tokens ────────────────────────────────────
    "candidat", "candidate", "prenom", "nom",
    "undefined", "null", "none", "unknown",
    "titre", "section", "cv", "curriculum", "vitae",
    "global", "entertainment", "freight", "services", "universal",
    "land", "rover", "jaguar",
    "identification", "contribuable",
    "automates", "pl", "step", "programmation",
    "questionnaire", "quali", "quanti",
    "option", "specialise",
    "envoipare", "mailcvsalim",
    "facu",
    "etat",
    "des",
    "du", "de", "la", "le", "les", "un", "une", "et", "ou", "en",
    "par", "pour", "sur", "dans", "avec",
    "qui", "est", "sont", "ont", "fait",
    "nouveau", "nouvelle",
    "general", "generales", "specifique", "specifiques",
    "national", "regionale", "locale",
    "permanent", "temporaire", "interim",
    "bonne", "bons", "bonnes",
    "tres", "bon",
}


BLOCKED_NAME_PHRASES: list[str] = [
    # Exact production examples that got through
    "permis de conduire", "de conduire", "permis b", "permis a/b",
    "langues berberes", "langues berbères",
    "diplome baccalaureat", "baccalaureat gestion", "sciences economiques",
    "experiences professionnelles", "experience professionnelle",
    "competences techniques", "technical skills", "soft skills",
    "elaboration du reporting", "reporting commercial", "sens de organisation",
    "maintenance industrielle",
    "fsjes ain chock", "residence safi",
    "voyage sport internet",
    "qui est",
    "situation de famille",
    "etat civil",
    "date d obtention",
    "date obtention",
    "missions ou taches",
    "taches realisees",
    "propos de moi",
    "mon objectif",
    "autres infos",
    "coordinateurs chauffeurs camions",
    "declaration cnss",
    "identification du contribuable",
    "programmation automates",
    "content manager brand",
    "account sales manager",
    "de direction secretaire",
    "secretaire de direction",
    "manager de rayon",
    "art culinaire",
    "qualites relationnelles",
    "qualites sociales",
    "principaux points forts",
    "comprehension approfondie",
    "assistance juridique",
    "organise par etrangere",
    "office package word",
    "ms word excel",
    "questionnaire quali quanti",
    "maitrise de la bureautique",
    "marketing direct",
    "marketing option",
    "digital agency",
    "land rover jaguar",
    "freight services universal",
    "des arts graphiques",
    "serie physique chimie",
    "ain sbaa faculte",
    "jnane deroua",
    "hay lalla meriem",
    "khalil la villette",
    "rue hm koudia",
    "kourbo tanga balia lot",
    "casa bnou noussair moussa",
    "chaine d approvisionnement",
    "nouvelles defis",
    "en strategie expert",
    "de reussir motivation",
    "etudes academiques",
    "en prospection confirme",
    "ma concerne son travail",
    "permet de reussir",
    "fi cati ons quali",
    "abd el aziz ouahmane",
    "confirme comptable",
    "ail com",
    "-developpement web",
]


COMMON_FIRST_NAMES: set[str] = {
    # Moroccan / Arabic / French common first names
    "marwa", "wijdane", "oumaima", "fatima", "imane", "ikram", "sara", "sarah",
    "aya", "hajar", "nada", "yasmine", "salma", "zineb", "zainab", "soukaina",
    "chaima", "khadija", "raihana", "wahiba", "assia", "sihame", "sanaa", "asmae",
    "asmaa", "amina", "hanane", "nawal", "maryem", "meriem", "leila", "laila",
    "jihane", "khaoula", "nouhaila", "latifa", "hasna", "radia", "nabila",
    "ghizlane", "sanae", "fatima", "houda", "rajaa", "mounia", "zahra",
    "naoual", "ihssan", "bousso", "naima", "aicha", "chaimae", "chaimae",
    "imahh", "hanane", "stitou",
    "mohamed", "mohammed", "ahmed", "amine", "anas", "ayoub", "youssef",
    "mehdi", "omar", "ali", "khalid", "hamza", "tariq", "hassan", "hicham",
    "zakaria", "zakariae", "mounir", "karim", "badr", "walid", "driss",
    "imad", "othmane", "younes", "mourad", "abdelhakim", "abdelkrim",
    "abdelillah", "abdelhay", "adil", "anas", "ousine", "oussama", "lahcen",
    "rachid", "hamid", "khalil", "amadu", "rabii", "haddar", "rabie",
    "hamza", "moubarik", "issam", "reda", "mohcine", "nadif", "naoui",
    "hassane", "zakaryae", "hafir", "mouhib", "mustapha", "moumenc",
    "fouad", "jaouad", "miloud", "farssi", "ittaana", "hilal", "charba",
    "yassine", "sanhoury", "rochdi", "louajni", "akorbal", "tigraten",
    "farid", "labrahmia", "elhoubba", "belkacem", "abdelhkim", "bayahya",
    "facu", "haddar",
    # French
    "jean", "pierre", "paul", "marie", "michel", "philippe", "alain",
    "nicolas", "thomas", "julien", "maxime", "laurent", "stephane", "eric",
    "camille", "lea", "manon", "lisa", "chloe",
}


# ---------------------------------------------------------------------------
# Core validation
# ---------------------------------------------------------------------------

def is_invalid_candidate_name(first_name: str | None, last_name: str | None) -> bool:
    """Return True if first_name + last_name look like a corrupted / non-person name."""
    first_clean = (first_name or "").strip()
    last_clean = (last_name or "").strip()
    full = f"{first_clean} {last_clean}".strip()

    if not full or len(full) < 3:
        return True

    # Contains digits → not a name
    if re.search(r"\d", full):
        return True

    # Too long → not a real name
    if len(full) > 65:
        return True

    normalized_full = strip_accents(full)

    # Check blocked phrases
    for phrase in BLOCKED_NAME_PHRASES:
        if phrase in normalized_full:
            return True

    # Tokenize and check each word against blocklist
    words_first = [w for w in re.split(r"\W+", strip_accents(first_clean)) if w and len(w) >= 2]
    words_last = [w for w in re.split(r"\W+", strip_accents(last_clean)) if w and len(w) >= 2]
    all_words = words_first + words_last

    if not all_words:
        return True

    # If any word in name matches blocklist → invalid
    for w in all_words:
        if w in SECTION_HEADER_BLOCKLIST:
            return True

    # If more than half the words are single letters or look like abbreviations → invalid
    all_raw_words = full.split()
    short_or_caps = sum(1 for w in all_raw_words if len(w) <= 2 or (w.isupper() and len(w) <= 4))
    if short_or_caps > len(all_raw_words) / 2:
        return True

    # Name has more than 5 words → suspicious
    if len(all_raw_words) > 5:
        return True

    return False


# ---------------------------------------------------------------------------
# Name extraction helpers
# ---------------------------------------------------------------------------

def extract_name_from_filename(filename: str | None) -> tuple[str, str] | None:
    """Try to extract a real person name from the CV filename."""
    if not filename:
        return None
    stem = Path(filename).stem

    # Remove dates like 9-2024, 8-2024, 2024, 2025
    stem = re.sub(r"\b\d{1,2}[-._]\d{2,4}\b", " ", stem)
    stem = re.sub(r"\b20\d{2}\b", " ", stem)
    # Remove leading numbers and codes like "1.", "13 ", "0_0_"
    stem = re.sub(r"^[\d._\s-]+", "", stem)

    noise_tokens = {
        "cv", "mv", "vc", "pl", "qm", "adv", "daf", "drh", "rrh",
        "resume", "curriculum", "vitae", "final", "draft", "copy",
        "pdf", "docx", "uploaded", "mon", "nouveau", "nouvelle",
        "pfe", "stage", "stagiaire", "job", "recrutement",
        "fc", "ba", "co", "sd", "vf", "sign", "signe",
        "new", "fr", "fr",
    }

    raw_tokens = [t.strip(".,;:()[]{}'\"-") for t in re.split(r"[._\s-]+", stem) if t]
    tokens = []
    for t in raw_tokens:
        clean_t = strip_accents(t.lower())
        if clean_t.isdigit() or len(clean_t) < 2:
            continue
        if clean_t in noise_tokens:
            continue
        if clean_t in SECTION_HEADER_BLOCKLIST:
            continue
        tokens.append(t)

    if len(tokens) >= 2:
        # Heuristic: Moroccan filenames often have LASTNAME FIRSTNAME order
        first_w = tokens[0].title()
        last_w = " ".join(t.title() for t in tokens[1:])
        # If last token looks like a known first name → swap
        if strip_accents(tokens[-1].lower()) in COMMON_FIRST_NAMES and len(tokens) == 2:
            first_w, last_w = tokens[-1].title(), tokens[0].title()

        if not is_invalid_candidate_name(first_w, last_w):
            return first_w, last_w

    elif len(tokens) == 1:
        fn = tokens[0].title()
        if not is_invalid_candidate_name(fn, "Candidat"):
            return fn, "Candidat"

    return None


def extract_name_from_raw_text(raw_text: str | None, email: str | None = None) -> tuple[str, str] | None:
    """Try to extract the person's name from the first lines of raw CV text."""
    if not raw_text or not raw_text.strip():
        return _extract_name_from_email(email)

    lines = [line.strip() for line in raw_text.replace("\r", "\n").splitlines() if line.strip()]

    # 1. Look for explicit labels: "Nom : ...", "Prénom : ...", "Nom & Prénom :"
    for line in lines[:25]:
        match = re.search(
            r"(?:nom\s*(?:complet|&\s*pr[eé]nom)?|pr[eé]nom)\s*[:|-]\s*([A-Za-zÀ-ÖØ-öø-ÿ'\s-]{3,50})",
            line,
            re.IGNORECASE,
        )
        if match:
            candidate_str = match.group(1).strip()
            words = [w for w in re.split(r"\s+", candidate_str) if len(w) >= 2]
            if 2 <= len(words) <= 4:
                fn, ln = words[0].title(), " ".join(w.title() for w in words[1:])
                if not is_invalid_candidate_name(fn, ln):
                    return fn, ln

    # 2. Inspect first 15 non-empty lines for 2-4 word short lines
    for line in lines[:15]:
        # Skip lines with contact info, special symbols, or numbers
        if re.search(r"[@+\d#|/\\<>]|http|www|github|linkedin", line, re.IGNORECASE):
            continue
        # Skip lines that look like addresses, cities, countries
        if re.search(r"\b(?:rue|avenue|boulevard|quartier|lot|bloc|hay|cite|imm)\b", line, re.IGNORECASE):
            continue

        words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ'-]{2,}", line)
        if not (2 <= len(words) <= 4):
            continue

        # Skip if any word is in blocklist
        if any(strip_accents(w) in SECTION_HEADER_BLOCKLIST for w in words):
            continue

        # Skip if line is too long
        if len(" ".join(words)) > 50:
            continue

        # Skip if line looks like a job title (contains common title patterns)
        if re.search(
            r"\b(?:manager|directeur|responsable|chef|ingenieur|consultant|analyst|technicien|assistant|charge|stage|coordinateur|secretaire)\b",
            strip_accents(line.lower()),
        ):
            continue

        first_w = words[0].title()
        last_w = " ".join(w.title() for w in words[1:])
        # Swap if last looks like a known first name
        if strip_accents(words[-1]).lower() in COMMON_FIRST_NAMES and len(words) == 2:
            first_w, last_w = words[-1].title(), words[0].title()

        if not is_invalid_candidate_name(first_w, last_w):
            return first_w, last_w

    # 3. Fall back to email
    return _extract_name_from_email(email)


def _extract_name_from_email(email: str | None) -> tuple[str, str] | None:
    if not email or "@" not in email:
        return None
    local_part = email.split("@", 1)[0]
    tokens = [t for t in re.split(r"[._-]+", local_part) if t and not t.isdigit() and len(t) >= 2]
    if len(tokens) >= 2:
        fn = tokens[0].title()
        ln = " ".join(t.title() for t in tokens[1:])
        if not is_invalid_candidate_name(fn, ln):
            return fn, ln
    elif len(tokens) == 1 and len(tokens[0]) >= 3:
        fn = tokens[0].title()
        if not is_invalid_candidate_name(fn, "Candidat"):
            return fn, "Candidat"
    return None


def sanitize_or_fallback_name(
    first_name: str | None,
    last_name: str | None,
    raw_text: str | None = None,
    email: str | None = None,
    filename: str | None = None,
) -> tuple[str, str]:
    """
    Return a valid (first_name, last_name) tuple.

    Priority:
    1. Use original if valid.
    2. Try filename extraction.
    3. Try raw text extraction.
    4. Try email extraction.
    5. Return placeholder ("Prénom", "Candidat").
    """
    if not is_invalid_candidate_name(first_name, last_name):
        return (first_name or "").strip(), (last_name or "").strip()

    # Priority 1: filename
    fn_res = extract_name_from_filename(filename)
    if fn_res and not is_invalid_candidate_name(fn_res[0], fn_res[1]):
        return fn_res

    # Priority 2: raw text
    raw_res = extract_name_from_raw_text(raw_text, email=email)
    if raw_res and not is_invalid_candidate_name(raw_res[0], raw_res[1]):
        return raw_res

    # Priority 3: email
    email_res = _extract_name_from_email(email)
    if email_res and not is_invalid_candidate_name(email_res[0], email_res[1]):
        return email_res

    # Priority 4: keep first_name if it alone is valid
    if first_name and not is_invalid_candidate_name(first_name, "Candidat"):
        return first_name.strip(), "Candidat"

    return "Prénom", "Candidat"
