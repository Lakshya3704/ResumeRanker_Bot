"""
matcher.py – Keyword + Semantic matching engine.

Provides:
  • Jaccard keyword overlap between two skill sets
  • Semantic (cosine) similarity via Sentence-BERT
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Set

from app.utils.helpers import setup_logging

logger = setup_logging("drcode.matcher")

# ──────────────────────────────────────────────
#  Sentence-BERT lazy loader
# ──────────────────────────────────────────────
_sbert_model = None


def _get_sbert():
    """Load Sentence-BERT model on first use."""
    global _sbert_model
    if _sbert_model is None:
        logger.info("Loading Sentence-BERT model (all-MiniLM-L6-v2) …")
        from sentence_transformers import SentenceTransformer
        _sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Sentence-BERT model loaded.")
    return _sbert_model


# ──────────────────────────────────────────────
#  Data classes
# ──────────────────────────────────────────────

@dataclass
class MatchResult:
    """Holds all matching metrics between JD and Resume."""
    keyword_score: float             # 0-1 Jaccard-like overlap
    semantic_score: float            # 0-1 cosine similarity
    matched_skills: List[str]        # Skills present in both
    missing_skills: List[str]        # In JD but not in Resume
    extra_skills: List[str]          # In Resume but not in JD
    experience_overlap: float        # 0-1 section similarity
    total_jd_skills: int
    total_resume_skills: int


# ──────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────

def match(
    jd_skills: List[str],
    resume_skills: List[str],
    jd_text: str,
    resume_text: str,
    jd_experience: List[str] | None = None,
    resume_experience: List[str] | None = None,
) -> MatchResult:
    """
    Compare a JD to a Resume on multiple axes.

    Args:
        jd_skills:          Extracted skill list from JD.
        resume_skills:      Extracted skill list from Resume.
        jd_text:            Full cleaned text of JD.
        resume_text:        Full cleaned text of Resume.
        jd_experience:      Experience section lines from JD.
        resume_experience:  Experience section lines from Resume.

    Returns:
        :class:`MatchResult` with all metrics.
    """
    jd_set: Set[str]     = {s.lower() for s in jd_skills}
    resume_set: Set[str] = {s.lower() for s in resume_skills}

    # ── Keyword (Jaccard-ish) overlap ──
    matched  = sorted(jd_set & resume_set)
    missing  = sorted(jd_set - resume_set)
    extra    = sorted(resume_set - jd_set)

    if jd_set:
        keyword_score = len(matched) / len(jd_set)
    else:
        keyword_score = 0.0

    # ── Semantic similarity ──
    semantic_score = _compute_semantic_similarity(jd_text, resume_text)

    # ── Experience overlap (semantic on section text) ──
    jd_exp_text     = "\n".join(jd_experience or [])
    resume_exp_text = "\n".join(resume_experience or [])
    if jd_exp_text and resume_exp_text:
        experience_overlap = _compute_semantic_similarity(jd_exp_text, resume_exp_text)
    else:
        # If either section is missing, give a neutral mid-score
        experience_overlap = 0.5

    return MatchResult(
        keyword_score=round(keyword_score, 4),
        semantic_score=round(semantic_score, 4),
        matched_skills=matched,
        missing_skills=missing,
        extra_skills=extra,
        experience_overlap=round(experience_overlap, 4),
        total_jd_skills=len(jd_set),
        total_resume_skills=len(resume_set),
    )


# ──────────────────────────────────────────────
#  Internal helpers
# ──────────────────────────────────────────────

def _compute_semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Compute cosine similarity between two texts using Sentence-BERT.

    Returns a float in [0, 1].
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0

    try:
        model = _get_sbert()
        embeddings = model.encode([text_a, text_b], convert_to_tensor=True)

        from sentence_transformers.util import cos_sim
        similarity = cos_sim(embeddings[0], embeddings[1]).item()

        # Clamp to [0, 1]
        return max(0.0, min(1.0, similarity))
    except Exception as exc:
        logger.error("Semantic similarity failed: %s", exc)
        return 0.0
