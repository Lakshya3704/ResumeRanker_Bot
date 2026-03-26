"""
schemas.py – Pydantic models for request / response validation.

Used by FastAPI routes and internally by the analysis pipeline.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
#  Analysis
# ──────────────────────────────────────────────

class ScoreBreakdownResponse(BaseModel):
    """Score detail sent to the client."""
    skills_score: float      = Field(..., description="Points from skill matching (max 4)")
    experience_score: float  = Field(..., description="Points from experience relevance (max 2)")
    keyword_score: float     = Field(..., description="Points from keyword overlap (max 2)")
    semantic_score: float    = Field(..., description="Points from semantic similarity (max 2)")
    total_score: float       = Field(..., description="Final score out of 10")
    grade: str               = Field(..., description="Letter grade (A+ to F)")


class RecommendationsResponse(BaseModel):
    """Actionable recommendations."""
    missing_skills: List[str]  = Field(default_factory=list)
    weak_areas: List[str]      = Field(default_factory=list)
    suggestions: List[str]     = Field(default_factory=list)
    format_tips: List[str]     = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    """Full analysis result returned by POST /analyze."""
    score: ScoreBreakdownResponse
    recommendations: RecommendationsResponse
    matched_skills: List[str]   = Field(default_factory=list)
    missing_skills: List[str]   = Field(default_factory=list)
    jd_skills: List[str]        = Field(default_factory=list)
    resume_skills: List[str]    = Field(default_factory=list)
    jd_text: str                = Field("", description="Raw extracted JD text for Q&A context")
    resume_text: str            = Field("", description="Raw extracted Resume text for Q&A context")


# ──────────────────────────────────────────────
#  Resume improvement
# ──────────────────────────────────────────────

class ImproveResumeRequest(BaseModel):
    """Body for POST /improve-resume (when sending text directly)."""
    resume_text: str
    jd_text: str
    missing_skills: List[str]  = Field(default_factory=list)
    suggestions: List[str]     = Field(default_factory=list)


class ImproveResumeResponse(BaseModel):
    """Improved resume text."""
    improved_text: str


# ──────────────────────────────────────────────
#  Resume generation
# ──────────────────────────────────────────────

class GenerateResumeRequest(BaseModel):
    """Body for POST /generate-resume."""
    improved_text: str
    format: Optional[str] = Field("pdf", description="'pdf' or 'docx'")


# ──────────────────────────────────────────────
#  Authentication
# ──────────────────────────────────────────────

class UserSignupRequest(BaseModel):
    """Body for POST /auth/signup."""
    name: str = Field(..., min_length=1, description="Full name")
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=6, description="Password (min 6 chars)")


class UserLoginRequest(BaseModel):
    """Body for POST /auth/login."""
    email: str
    password: str


class UserResponse(BaseModel):
    """User profile info (no password)."""
    name: str
    email: str
    created_at: str


class TokenResponse(BaseModel):
    """JWT token + user info returned on signup/login."""
    token: str
    user: UserResponse


# ──────────────────────────────────────────────
#  Conversational Q&A
# ──────────────────────────────────────────────

class AskRequest(BaseModel):
    """Body for POST /ask."""
    question: str = Field(..., description="User's question")
    resume_text: str = Field(..., description="Candidate's original resume text")
    jd_text: str = Field(..., description="Target Job Description text")


class AskResponse(BaseModel):
    """AI answer to the question."""
    answer: str


# ──────────────────────────────────────────────
#  Health
# ──────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
