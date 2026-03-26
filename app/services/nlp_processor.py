"""
nlp_processor.py – NLP pipeline powered by spaCy.

Provides:
  • Tokenisation, lemmatisation, stop-word removal
  • Skill / tool / technology extraction (entity + keyword-list)
  • Experience & education section detection
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

import spacy
from spacy.tokens import Doc

from app.utils.helpers import setup_logging

logger = setup_logging("drcode.nlp")

# ──────────────────────────────────────────────
#  Load spaCy model (lazy singleton)
# ──────────────────────────────────────────────
_nlp: spacy.Language | None = None


def _get_nlp() -> spacy.Language:
    """Load the spaCy English model (downloads if missing)."""
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("Downloading spaCy model en_core_web_sm …")
            from spacy.cli import download
            download("en_core_web_sm")
            _nlp = spacy.load("en_core_web_sm")
        logger.info("spaCy model loaded.")
    return _nlp


# ──────────────────────────────────────────────
#  Curated keyword lists
# ──────────────────────────────────────────────
TECH_SKILLS: set[str] = {
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl",
    # Web Frameworks
    "react", "reactjs", "react.js", "angular", "vue", "vuejs", "vue.js",
    "next.js", "nextjs", "nuxt", "django", "flask", "fastapi", "express",
    "spring", "spring boot", "rails", "laravel", "asp.net",
    # Data / ML
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "spark", "hadoop", "airflow", "mlflow", "machine learning",
    "deep learning", "nlp", "natural language processing", "computer vision",
    "data science", "data analysis", "data engineering",
    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
    "terraform", "ansible", "jenkins", "ci/cd", "github actions",
    "gitlab ci", "circleci", "linux", "nginx", "apache",
    # Databases
    "sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "elasticsearch",
    "dynamodb", "cassandra", "neo4j", "sqlite", "oracle", "firebase",
    # Tools & Misc
    "git", "github", "gitlab", "bitbucket", "jira", "confluence",
    "figma", "postman", "swagger", "graphql", "rest", "restful",
    "api", "microservices", "agile", "scrum", "kanban",
    "html", "css", "sass", "tailwind", "bootstrap", "webpack",
    "node.js", "nodejs", "npm", "yarn", "deno",
    # Soft skills (subset – kept short)
    "leadership", "communication", "teamwork", "problem solving",
    "project management", "time management",
}

# ──────────────────────────────────────────────
#  Data class for extracted information
# ──────────────────────────────────────────────

@dataclass
class ExtractedInfo:
    """Container for all information extracted from a document."""
    skills: List[str]           = field(default_factory=list)
    experience: List[str]       = field(default_factory=list)
    education: List[str]        = field(default_factory=list)
    tools_and_tech: List[str]   = field(default_factory=list)
    clean_tokens: List[str]     = field(default_factory=list)
    lemmatized_text: str        = ""
    raw_text: str               = ""


# ──────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────

def process_text(text: str) -> ExtractedInfo:
    """
    Run the full NLP pipeline on *text* and return structured data.

    Steps:
      1. Tokenise & lemmatise (spaCy)
      2. Remove stop-words and punctuation
      3. Extract skills via curated list + NER
      4. Detect experience & education sections
    """
    nlp = _get_nlp()
    doc: Doc = nlp(text)

    info = ExtractedInfo(raw_text=text)

    # ── Tokenisation / lemmatisation / stopword removal ──
    tokens: list[str] = []
    lemmas: list[str] = []
    for token in doc:
        if token.is_stop or token.is_punct or token.is_space:
            continue
        tokens.append(token.text.lower())
        lemmas.append(token.lemma_.lower())

    info.clean_tokens = tokens
    info.lemmatized_text = " ".join(lemmas)

    # ── Skill / tool extraction ──
    text_lower = text.lower()
    found_skills: set[str] = set()
    for skill in TECH_SKILLS:
        # Whole-word match
        if re.search(rf"\b{re.escape(skill)}\b", text_lower):
            found_skills.add(skill)

    # Also check spaCy NER for ORG / PRODUCT entities (may uncover tools)
    for ent in doc.ents:
        ent_lower = ent.text.lower()
        if ent.label_ in ("ORG", "PRODUCT"):
            if ent_lower in TECH_SKILLS:
                found_skills.add(ent_lower)

    info.skills = sorted(found_skills)
    info.tools_and_tech = sorted(
        s for s in found_skills
        if s not in {
            "leadership", "communication", "teamwork",
            "problem solving", "project management", "time management",
        }
    )

    # ── Experience section extraction ──
    info.experience = _extract_section(text, [
        "experience", "work experience", "professional experience",
        "employment history", "work history",
    ])

    # ── Education section extraction ──
    info.education = _extract_section(text, [
        "education", "academic background", "qualifications",
        "academic qualifications", "degrees",
    ])

    return info


# ──────────────────────────────────────────────
#  Section helpers
# ──────────────────────────────────────────────

_SECTION_HEADERS = re.compile(
    r"^(?:[\d.]*\s*)?([A-Z][A-Za-z &/]+)", re.MULTILINE
)


def _extract_section(text: str, headers: list[str]) -> list[str]:
    """
    Heuristically extract bullet-point content under any of the
    given *headers* inside *text*.
    """
    lines = text.split("\n")
    capturing = False
    captured: list[str] = []

    for line in lines:
        stripped = line.strip()
        # Check if this line IS one of the target headers
        if any(h in stripped.lower() for h in headers):
            capturing = True
            continue

        # A blank line or a new all-caps header ends the section
        if capturing:
            if stripped == "":
                if captured:
                    # Allow one blank line; two in a row → stop
                    if captured[-1] == "":
                        break
                    captured.append("")
                continue
            # New section header → stop capturing
            if _SECTION_HEADERS.match(stripped) and stripped.isupper():
                break
            captured.append(stripped)

    # Clean trailing blanks
    while captured and captured[-1] == "":
        captured.pop()

    return captured
