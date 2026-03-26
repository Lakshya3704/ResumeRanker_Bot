"""
scorer.py – Weighted scoring engine (out of 10).

Breakdown:
  • Skills match      → 4 points
  • Experience match  → 2 points
  • Keyword match     → 2 points
  • Semantic sim.     → 2 points
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.matcher import MatchResult
from app.utils.helpers import setup_logging

logger = setup_logging("drcode.scorer")


# ──────────────────────────────────────────────
#  Weights (must sum to 10)
# ──────────────────────────────────────────────
WEIGHT_SKILLS     = 4.0
WEIGHT_EXPERIENCE = 2.0
WEIGHT_KEYWORD    = 2.0
WEIGHT_SEMANTIC   = 2.0


@dataclass
class ScoreBreakdown:
    """Detailed score breakdown for transparency."""
    skills_score: float       # 0 – WEIGHT_SKILLS
    experience_score: float   # 0 – WEIGHT_EXPERIENCE
    keyword_score: float      # 0 – WEIGHT_KEYWORD
    semantic_score: float     # 0 – WEIGHT_SEMANTIC
    total_score: float        # 0 – 10
    grade: str                # A+ / A / B … / F


def compute_score(match_result: MatchResult) -> ScoreBreakdown:
    """
    Compute a normalised score out of 10 from a :class:`MatchResult`.

    Each component ratio (0-1) is multiplied by its weight.
    """
    skills_score     = match_result.keyword_score    * WEIGHT_SKILLS
    experience_score = match_result.experience_overlap * WEIGHT_EXPERIENCE
    keyword_score    = match_result.keyword_score    * WEIGHT_KEYWORD
    semantic_score   = match_result.semantic_score   * WEIGHT_SEMANTIC

    total = skills_score + experience_score + keyword_score + semantic_score
    total = round(min(total, 10.0), 2)

    grade = _to_grade(total)

    breakdown = ScoreBreakdown(
        skills_score=round(skills_score, 2),
        experience_score=round(experience_score, 2),
        keyword_score=round(keyword_score, 2),
        semantic_score=round(semantic_score, 2),
        total_score=total,
        grade=grade,
    )
    logger.info("Score computed: %s/10 (%s)", total, grade)
    return breakdown


def _to_grade(score: float) -> str:
    """Map a numeric score to a letter grade."""
    if score >= 9.5:
        return "A+"
    elif score >= 8.5:
        return "A"
    elif score >= 7.5:
        return "B+"
    elif score >= 6.5:
        return "B"
    elif score >= 5.5:
        return "C+"
    elif score >= 4.5:
        return "C"
    elif score >= 3.5:
        return "D"
    else:
        return "F"
