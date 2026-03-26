"""
analyze.py – FastAPI routes for resume analysis, improvement, and generation.

Endpoints:
  POST /analyze          → upload JD + Resume, get score & feedback
  POST /improve-resume   → get improved resume text
  POST /generate-resume  → get downloadable PDF or DOCX
"""

from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from app.models.schemas import (
    AnalysisResponse,
    ScoreBreakdownResponse,
    RecommendationsResponse,
    ImproveResumeRequest,
    ImproveResumeResponse,
    GenerateResumeRequest,
    AskRequest,
    AskResponse,
)
from app.services.file_parser import extract_text, UnsupportedFileTypeError
from app.services.nlp_processor import process_text
from app.services.matcher import match
from app.services.scorer import compute_score
from app.services.recommender import generate_recommendations
from app.services.improver import improve_resume, answer_question
from app.services.resume_gen import generate_pdf, generate_docx
from app.utils.helpers import save_temp_file, cleanup_temp_file, setup_logging

logger = setup_logging("drcode.routes")

router = APIRouter()


# ──────────────────────────────────────────────
#  POST /analyze
# ──────────────────────────────────────────────

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_resume(
    jd_file: UploadFile = File(..., description="Job Description (PDF/DOCX/TXT)"),
    resume_file: UploadFile = File(..., description="Resume (PDF/DOCX)"),
):
    """
    Upload a JD and a Resume → receive a detailed analysis with score,
    matched/missing skills, and actionable recommendations.
    """
    jd_path = None
    resume_path = None

    try:
        # ── Save uploaded files ──
        jd_bytes = await jd_file.read()
        resume_bytes = await resume_file.read()

        if not jd_file.filename or not resume_file.filename:
            raise HTTPException(400, "Both files must have a filename.")

        jd_path = save_temp_file(jd_bytes, f"jd_{jd_file.filename}")
        resume_path = save_temp_file(resume_bytes, f"resume_{resume_file.filename}")

        # ── Extract text ──
        try:
            jd_text = extract_text(jd_path)
            resume_text = extract_text(resume_path)
        except UnsupportedFileTypeError as e:
            raise HTTPException(400, str(e))

        if not jd_text.strip():
            raise HTTPException(400, "Could not extract text from the JD file.")
        if not resume_text.strip():
            raise HTTPException(400, "Could not extract text from the Resume file.")

        # ── NLP processing ──
        jd_info = process_text(jd_text)
        resume_info = process_text(resume_text)

        # ── Match ──
        match_result = match(
            jd_skills=jd_info.skills,
            resume_skills=resume_info.skills,
            jd_text=jd_info.lemmatized_text,
            resume_text=resume_info.lemmatized_text,
            jd_experience=jd_info.experience,
            resume_experience=resume_info.experience,
        )

        # ── Score ──
        score = compute_score(match_result)

        # ── Recommendations ──
        recs = generate_recommendations(match_result, score)

        return AnalysisResponse(
            score=ScoreBreakdownResponse(
                skills_score=score.skills_score,
                experience_score=score.experience_score,
                keyword_score=score.keyword_score,
                semantic_score=score.semantic_score,
                total_score=score.total_score,
                grade=score.grade,
            ),
            recommendations=RecommendationsResponse(
                missing_skills=recs.missing_skills,
                weak_areas=recs.weak_areas,
                suggestions=recs.suggestions,
                format_tips=recs.format_tips,
            ),
            matched_skills=match_result.matched_skills,
            missing_skills=match_result.missing_skills,
            jd_skills=list(jd_info.skills),
            resume_skills=list(resume_info.skills),
            jd_text=jd_text,
            resume_text=resume_text,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Analysis failed")
        raise HTTPException(500, f"Internal error during analysis: {exc}")
    finally:
        if jd_path:
            cleanup_temp_file(jd_path)
        if resume_path:
            cleanup_temp_file(resume_path)


# ──────────────────────────────────────────────
#  POST /improve-resume
# ──────────────────────────────────────────────

@router.post("/improve-resume", response_model=ImproveResumeResponse)
async def improve_resume_endpoint(body: ImproveResumeRequest):
    """
    Given resume text, JD text, and missing skills,
    return an AI-improved version of the resume.
    """
    try:
        improved = await improve_resume(
            resume_text=body.resume_text,
            jd_text=body.jd_text,
            missing_skills=body.missing_skills,
            suggestions=body.suggestions,
        )
        return ImproveResumeResponse(improved_text=improved)
    except Exception as exc:
        logger.exception("Resume improvement failed")
        raise HTTPException(500, f"Improvement failed: {exc}")


# ──────────────────────────────────────────────
#  POST /generate-resume
# ──────────────────────────────────────────────

@router.post("/generate-resume")
async def generate_resume_endpoint(body: GenerateResumeRequest):
    """
    Generate a downloadable PDF or DOCX from improved resume text.
    """
    fmt = (body.format or "pdf").lower()

    try:
        if fmt == "pdf":
            path = generate_pdf(body.improved_text)
            return FileResponse(
                path=str(path),
                media_type="application/pdf",
                filename="improved_resume.pdf",
            )
        elif fmt == "docx":
            path = generate_docx(body.improved_text)
            return FileResponse(
                path=str(path),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                filename="improved_resume.docx",
            )
        else:
            raise HTTPException(400, f"Unsupported format: '{fmt}'. Use 'pdf' or 'docx'.")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Resume generation failed")
        raise HTTPException(500, f"Generation failed: {exc}")


# ──────────────────────────────────────────────
#  POST /ask
# ──────────────────────────────────────────────

@router.post("/ask", response_model=AskResponse)
async def ask_question_endpoint(body: AskRequest):
    """
    Endpoint for asking conversational questions about the JD and resume.
    """
    try:
        answer = await answer_question(
            question=body.question,
            resume_text=body.resume_text,
            jd_text=body.jd_text,
        )
        return AskResponse(answer=answer)
    except Exception as exc:
        logger.exception("Q&A failed")
        raise HTTPException(500, f"Failed to get answer: {exc}")
