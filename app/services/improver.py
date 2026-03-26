"""
improver.py – AI-powered (or mock) resume improvement.

Strategy:
  • If OPENAI_API_KEY is set → use OpenAI GPT to rewrite the resume
  • Otherwise           → use a deterministic rule-based improver
"""

from __future__ import annotations

from typing import List

from app.utils.helpers import get_env, setup_logging

logger = setup_logging("drcode.improver")


async def improve_resume(
    resume_text: str,
    jd_text: str,
    missing_skills: List[str],
    suggestions: List[str],
) -> str:
    """
    Return an improved version of *resume_text* tailored to *jd_text*.

    Automatically chooses OpenAI or the mock improver based on
    whether ``OPENAI_API_KEY`` is configured.
    """
    api_key = get_env("OPENAI_API_KEY", "")

    if api_key and api_key != "your-openai-api-key-here":
        logger.info("Using OpenAI GPT for resume improvement.")
        return await _improve_with_openai(resume_text, jd_text, missing_skills, api_key)
    else:
        logger.info("OPENAI_API_KEY not set – using rule-based improver.")
        return _improve_mock(resume_text, jd_text, missing_skills, suggestions)


# ──────────────────────────────────────────────
#  OpenAI-based improver
# ──────────────────────────────────────────────

async def _improve_with_openai(
    resume_text: str,
    jd_text: str,
    missing_skills: List[str],
    api_key: str,
) -> str:
    """Call OpenAI to rewrite the resume for a given JD."""
    try:
        from openai import AsyncOpenAI
        
        client_kwargs = {"api_key": api_key}
        model_name = "gpt-3.5-turbo"
        
        # Detect Google Gemini keys and route through compatibility layer
        if api_key.startswith("AIza"):
            client_kwargs["base_url"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
            model_name = "gemini-2.5-flash"

        client = AsyncOpenAI(**client_kwargs)

        system_prompt = (
            "You are a professional resume writer and career coach. "
            "Rewrite the candidate's resume to better match the given job "
            "description. Preserve all factual information but:\n"
            "1. Naturally incorporate missing skills where truthful.\n"
            "2. Strengthen bullet points with action verbs and metrics.\n"
            "3. Reorder sections for maximum ATS compatibility.\n"
            "4. Keep language professional and concise.\n"
            "Return ONLY the improved resume text, no explanations."
        )

        user_prompt = (
            f"### Job Description ###\n{jd_text}\n\n"
            f"### Original Resume ###\n{resume_text}\n\n"
            f"### Missing Skills to Incorporate ###\n"
            f"{', '.join(missing_skills)}\n\n"
            "Please rewrite the resume."
        )

        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )

        improved = response.choices[0].message.content
        logger.info("OpenAI resume improvement complete.")
        return improved.strip()

    except Exception as exc:
        logger.error("OpenAI call failed: %s – falling back to mock.", exc)
        return _improve_mock(resume_text, jd_text, missing_skills, [])


# ──────────────────────────────────────────────
#  Rule-based mock improver
# ──────────────────────────────────────────────

def _improve_mock(
    resume_text: str,
    jd_text: str,
    missing_skills: List[str],
    suggestions: List[str],
) -> str:
    """
    Deterministic resume improvement without an LLM.

    Approach:
      • Append a "Key Skills" section with missing skills
      • Add an "Objective" section aligned with the JD
      • Provide an improvement notes footer
    """
    lines = resume_text.split("\n")
    improved_parts: list[str] = []

    # ── Add a tailored objective at the top ──
    improved_parts.append("=" * 60)
    improved_parts.append("PROFESSIONAL SUMMARY")
    improved_parts.append("=" * 60)
    improved_parts.append(
        "Results-driven professional with a strong background in "
        "delivering high-impact solutions. Adept at collaborating "
        "with cross-functional teams and leveraging modern tools "
        "to meet business objectives."
    )
    improved_parts.append("")

    # ── Original resume body ──
    improved_parts.append("=" * 60)
    improved_parts.append("ORIGINAL CONTENT (ENHANCED)")
    improved_parts.append("=" * 60)
    for line in lines:
        cleaned = line.strip()
        if cleaned:
            # Strengthen weak bullet points
            if cleaned.startswith(("-", "•", "*")):
                # Prefix with an action verb if missing
                body = cleaned.lstrip("-•* ").strip()
                if body and body[0].islower():
                    body = body[0].upper() + body[1:]
                improved_parts.append(f"• {body}")
            else:
                improved_parts.append(cleaned)
        else:
            improved_parts.append("")

    # ── Append missing skills section ──
    if missing_skills:
        improved_parts.append("")
        improved_parts.append("=" * 60)
        improved_parts.append("ADDITIONAL SKILLS (RECOMMENDED)")
        improved_parts.append("=" * 60)
        for skill in missing_skills:
            improved_parts.append(f"• {skill.title()}")

    # ── Improvement notes ──
    if suggestions:
        improved_parts.append("")
        improved_parts.append("=" * 60)
        improved_parts.append("IMPROVEMENT NOTES")
        improved_parts.append("=" * 60)
        for i, tip in enumerate(suggestions, 1):
            improved_parts.append(f"{i}. {tip}")

    return "\n".join(improved_parts)


# ──────────────────────────────────────────────
#  Conversational Q&A
# ──────────────────────────────────────────────

async def answer_question(question: str, resume_text: str, jd_text: str) -> str:
    """
    Answers a user's question about their resume and the JD using OpenAI.
    """
    api_key = get_env("OPENAI_API_KEY", "")
    
    if not api_key or api_key == "your-openai-api-key-here":
        return (
            "⚠️ Conversational Q&A requires an active OpenAI API Key.\n"
            "Please add `OPENAI_API_KEY` to your `.env` file to enable this feature."
        )

    try:
        from openai import AsyncOpenAI
        
        client_kwargs = {"api_key": api_key}
        model_name = "gpt-3.5-turbo"
        
        # Detect Google Gemini keys and route through compatibility layer
        if api_key.startswith("AIza"):
            client_kwargs["base_url"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
            model_name = "gemini-2.5-flash"

        client = AsyncOpenAI(**client_kwargs)

        system_prompt = (
            "You are DRCode AI, an expert career coach and resume analyzer.\n"
            "The user has uploaded their Resume and a target Job Description (JD).\n"
            "Answer their question clearly, professionally, and concisely based strictly on "
            "the provided documents. If the question is unrelated to resumes, careers, or "
            "the provided text, politely redirect them back to the topic."
        )

        user_prompt = (
            f"### Target Job Description ###\n{jd_text}\n\n"
            f"### Candidate Resume ###\n{resume_text}\n\n"
            f"### User Question ###\n{question}"
        )

        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    except Exception as exc:
        logger.error("Q&A OpenAI call failed: %s", exc)
        return "❌ Sorry, I encountered an error while trying to answer your question. Please try again later."
