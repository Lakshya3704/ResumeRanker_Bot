"""
recommender.py – Generate actionable improvement suggestions.

Produces:
  • Missing skills list
  • Weak-area analysis
  • Concrete improvement tips
  • ATS format suggestions
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from app.services.matcher import MatchResult
from app.services.scorer import ScoreBreakdown
from app.utils.helpers import setup_logging

logger = setup_logging("drcode.recommender")


@dataclass
class Recommendations:
    """Container for all recommendation outputs."""
    missing_skills: List[str]       = field(default_factory=list)
    weak_areas: List[str]           = field(default_factory=list)
    suggestions: List[str]          = field(default_factory=list)
    format_tips: List[str]          = field(default_factory=list)


def generate_recommendations(
    match_result: MatchResult,
    score: ScoreBreakdown,
) -> Recommendations:
    """
    Build personalised recommendations based on match metrics and score.

    Args:
        match_result: Skill / semantic matching data.
        score:        Weighted score breakdown.

    Returns:
        :class:`Recommendations` with actionable items.
    """
    rec = Recommendations()

    # ── Missing skills ──
    rec.missing_skills = list(match_result.missing_skills)

    # ── Weak areas ──
    if score.skills_score < 2.0:
        rec.weak_areas.append(
            "Skills coverage is low – your resume matches less than half "
            "the skills listed in the job description."
        )
    if score.experience_score < 1.0:
        rec.weak_areas.append(
            "Experience relevance is weak – consider tailoring your work "
            "experience bullet points to mirror the JD language."
        )
    if score.semantic_score < 1.0:
        rec.weak_areas.append(
            "Overall content similarity is low – the resume may be too "
            "generic for this role."
        )

    # ── Suggestions ──
    if match_result.missing_skills:
        top_missing = match_result.missing_skills[:5]
        rec.suggestions.append(
            f"Add the following high-priority skills: {', '.join(top_missing)}."
        )
    if score.experience_score < 1.5:
        rec.suggestions.append(
            "Include measurable achievements (e.g., 'Increased sales by 30%')."
        )
    if score.skills_score < 3.0:
        rec.suggestions.append(
            "Add relevant projects or certifications that demonstrate the "
            "required skills."
        )
    if score.semantic_score < 1.0:
        rec.suggestions.append(
            "Use keywords and phrases from the job description throughout "
            "your resume."
        )

    # Always suggest:
    rec.suggestions.append(
        "Start bullet points with strong action verbs "
        "(e.g., Developed, Designed, Optimised)."
    )
    rec.suggestions.append(
        "Keep your resume to 1–2 pages for maximum impact."
    )

    # ── ATS / format tips ──
    rec.format_tips = _ats_format_tips()

    logger.info("Generated %d suggestions, %d format tips.",
                len(rec.suggestions), len(rec.format_tips))
    return rec


def _ats_format_tips() -> list[str]:
    """Return best-practice ATS formatting advice."""
    return [
        "Use a clean, single-column layout with standard section headers.",
        "Recommended section order: Contact → Summary → Skills → "
        "Experience → Education → Certifications → Projects.",
        "Avoid tables, images, and complex formatting — ATS parsers "
        "often misread them.",
        "Use standard fonts (Arial, Calibri, or Times New Roman) at "
        "10–12 pt.",
        "Save as PDF to preserve formatting, but also keep a DOCX "
        "version for systems that prefer it.",
        "Include exact keywords from the job description, not synonyms.",
        "Use bullet points instead of long paragraphs for readability.",
        "Put your full name and contact info at the very top.",
    ]
