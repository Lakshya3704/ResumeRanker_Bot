"""
handlers.py – Telegram bot conversation handlers.

Flow:
  1. /start → welcome message
  2. User uploads JD  (PDF / DOCX / TXT)
  3. User uploads Resume (PDF / DOCX)
  4. Bot processes → returns score, skills, suggestions
  5. User can tap "Download Improved Resume" → receives PDF + DOCX
"""

from __future__ import annotations


from pathlib import Path

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Document,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.services.file_parser import extract_text, UnsupportedFileTypeError
from app.services.nlp_processor import process_text
from app.services.matcher import match
from app.services.scorer import compute_score
from app.services.recommender import generate_recommendations
from app.services.improver import improve_resume, answer_question
from app.services.resume_gen import generate_pdf, generate_docx
from app.utils.helpers import save_temp_file, cleanup_temp_file, setup_logging

logger = setup_logging("drcode.bot")

# ── Conversation states ──
WAITING_JD, WAITING_RESUME, PROCESSING = range(3)


# ══════════════════════════════════════════════
#  /start command
# ══════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send welcome message and ask for JD."""
    welcome = (
        "👋 *Welcome to DRCode – AI Resume Analyzer!*\n\n"
        "I'll help you compare your resume against a job description "
        "and give you a detailed score with actionable tips.\n\n"
        "📌 *How it works:*\n"
        "1️⃣ Send me the *Job Description* (PDF, DOCX, or TXT)\n"
        "2️⃣ Then send me your *Resume* (PDF or DOCX)\n"
        "3️⃣ I'll analyze and return your score + suggestions\n"
        "4️⃣ Optionally download an improved resume!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📄 *Step 1:* Please upload your *Job Description* file now."
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")
    return WAITING_JD


# ══════════════════════════════════════════════
#  Receive JD
# ══════════════════════════════════════════════

async def receive_jd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the JD file upload."""
    document: Document | None = update.message.document

    if not document:
        await update.message.reply_text(
            "⚠️ Please send a *file* (PDF, DOCX, or TXT), not a text message.",
            parse_mode="Markdown",
        )
        return WAITING_JD

    filename = document.file_name or "jd_upload"
    ext = Path(filename).suffix.lower()

    if ext not in (".pdf", ".docx", ".txt"):
        await update.message.reply_text(
            "❌ Unsupported format. Please upload a *PDF*, *DOCX*, or *TXT* file.",
            parse_mode="Markdown",
        )
        return WAITING_JD

    # Download file
    tg_file = await document.get_file()
    file_bytes = await tg_file.download_as_bytearray()
    jd_path = save_temp_file(bytes(file_bytes), f"jd_{filename}")

    context.user_data["jd_path"] = str(jd_path)
    context.user_data["jd_filename"] = filename

    await update.message.reply_text(
        f"✅ JD received: *{filename}*\n\n"
        "📄 *Step 2:* Now please upload your *Resume* (PDF or DOCX).",
        parse_mode="Markdown",
    )
    return WAITING_RESUME


# ══════════════════════════════════════════════
#  Receive Resume & Process
# ══════════════════════════════════════════════

async def receive_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle resume upload, run full analysis, and send results."""
    document: Document | None = update.message.document

    if not document:
        await update.message.reply_text(
            "⚠️ Please send a *file* (PDF or DOCX), not a text message.",
            parse_mode="Markdown",
        )
        return WAITING_RESUME

    filename = document.file_name or "resume_upload"
    ext = Path(filename).suffix.lower()

    if ext not in (".pdf", ".docx"):
        await update.message.reply_text(
            "❌ Unsupported format. Please upload a *PDF* or *DOCX* resume.",
            parse_mode="Markdown",
        )
        return WAITING_RESUME

    # Download file
    tg_file = await document.get_file()
    file_bytes = await tg_file.download_as_bytearray()
    resume_path = save_temp_file(bytes(file_bytes), f"resume_{filename}")

    context.user_data["resume_path"] = str(resume_path)
    context.user_data["resume_filename"] = filename

    await update.message.reply_text("⏳ *Analyzing your resume…* Please wait.", parse_mode="Markdown")

    try:
        # ── Extract text ──
        jd_path = context.user_data.get("jd_path", "")
        jd_text = extract_text(jd_path)
        resume_text = extract_text(resume_path)

        if not jd_text.strip() or not resume_text.strip():
            await update.message.reply_text(
                "❌ Could not extract text from one of the files. "
                "Please make sure the files are not image-only PDFs."
            )
            return ConversationHandler.END

        # ── NLP ──
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

        # ── Store for later use ──
        context.user_data["jd_text"] = jd_text
        context.user_data["resume_text"] = resume_text
        context.user_data["missing_skills"] = recs.missing_skills
        context.user_data["suggestions"] = recs.suggestions

        # ── Build response ──
        response = _build_analysis_message(score, match_result, recs)

        # Add download button
        keyboard = [[
            InlineKeyboardButton(
                "📥 Download Improved Resume",
                callback_data="download_improved",
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            response,
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )

    except UnsupportedFileTypeError as e:
        await update.message.reply_text(f"❌ {e}")
    except Exception as exc:
        logger.exception("Analysis error")
        await update.message.reply_text(
            f"❌ An error occurred during analysis:\n`{exc}`",
            parse_mode="Markdown",
        )
    finally:
        # Cleanup temp files
        cleanup_temp_file(Path(context.user_data.get("jd_path", "")))
        cleanup_temp_file(Path(context.user_data.get("resume_path", "")))

    return ConversationHandler.END


# ══════════════════════════════════════════════
#  Download improved resume callback
# ══════════════════════════════════════════════

async def download_improved(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send improved resume as PDF + DOCX."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text("⏳ *Generating your improved resume…*", parse_mode="Markdown")

    try:
        resume_text = context.user_data.get("resume_text", "")
        jd_text = context.user_data.get("jd_text", "")
        missing_skills = context.user_data.get("missing_skills", [])
        suggestions = context.user_data.get("suggestions", [])

        if not resume_text:
            await query.message.reply_text("❌ No resume data found. Please start over with /start.")
            return

        # ── Improve ──
        improved_text = await improve_resume(
            resume_text=resume_text,
            jd_text=jd_text,
            missing_skills=missing_skills,
            suggestions=suggestions,
        )

        # ── Generate files ──
        pdf_path = generate_pdf(improved_text)
        docx_path = generate_docx(improved_text)

        # ── Send files ──
        await query.message.reply_document(
            document=open(pdf_path, "rb"),
            filename="improved_resume.pdf",
            caption="📄 Your improved resume (PDF)",
        )
        await query.message.reply_document(
            document=open(docx_path, "rb"),
            filename="improved_resume.docx",
            caption="📝 Your improved resume (DOCX)",
        )

        await query.message.reply_text(
            "✅ *Done!* Your improved resume has been sent in both PDF and DOCX formats.\n\n"
            "Use /start to analyze another resume.",
            parse_mode="Markdown",
        )

    except Exception as exc:
        logger.exception("Resume generation error")
        await query.message.reply_text(
            f"❌ Failed to generate resume:\n`{exc}`",
            parse_mode="Markdown",
        )


# ══════════════════════════════════════════════
#  /cancel command
# ══════════════════════════════════════════════

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current conversation."""
    await update.message.reply_text(
        "🚫 Operation cancelled. Use /start to begin again.",
        parse_mode="Markdown",
    )
    context.user_data.clear()
    return ConversationHandler.END


# ══════════════════════════════════════════════
#  Q&A Handler for free text
# ══════════════════════════════════════════════

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle general questions from the user based on their resume and JD."""
    question = update.message.text
    resume_text = context.user_data.get("resume_text", "")
    jd_text = context.user_data.get("jd_text", "")

    if not resume_text or not jd_text:
        await update.message.reply_text(
            "⚠️ Please upload your *Job Description* and *Resume* first using /start before asking questions.",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text("🤔 *Thinking…*", parse_mode="Markdown")

    try:
        answer = await answer_question(question, resume_text, jd_text)
        await update.message.reply_text(answer)
    except Exception as exc:
        logger.exception("Failed to answer question in bot")
        await update.message.reply_text("❌ An error occurred while generating the answer.")


# ══════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════

def _build_analysis_message(score, match_result, recs) -> str:
    """Format the analysis result into a Telegram-friendly message."""
    # Score header
    msg = (
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *RESUME ANALYSIS REPORT*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏆 *Score: {score.total_score}/10* ({score.grade})\n\n"
    )

    # Score breakdown
    msg += (
        "📈 *Score Breakdown:*\n"
        f"  • Skills Match: `{score.skills_score}/4.0`\n"
        f"  • Experience:   `{score.experience_score}/2.0`\n"
        f"  • Keywords:     `{score.keyword_score}/2.0`\n"
        f"  • Similarity:   `{score.semantic_score}/2.0`\n\n"
    )

    # Matched skills
    if match_result.matched_skills:
        skills_str = ", ".join(match_result.matched_skills[:10])
        msg += f"✅ *Matched Skills:*\n{skills_str}\n\n"

    # Missing skills
    if recs.missing_skills:
        missing_str = "\n".join(f"  • {s}" for s in recs.missing_skills[:10])
        msg += f"❌ *Missing Skills:*\n{missing_str}\n\n"

    # Weak areas
    if recs.weak_areas:
        weak_str = "\n".join(f"  ⚠️ {w}" for w in recs.weak_areas)
        msg += f"🔍 *Weak Areas:*\n{weak_str}\n\n"

    # Suggestions
    if recs.suggestions:
        sugg_str = "\n".join(f"  💡 {s}" for s in recs.suggestions[:6])
        msg += f"💡 *Suggestions:*\n{sugg_str}\n\n"

    # Format tips (first 3)
    if recs.format_tips:
        tips_str = "\n".join(f"  📌 {t}" for t in recs.format_tips[:3])
        msg += f"📋 *ATS Format Tips:*\n{tips_str}\n\n"

    msg += "━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "👇 Tap below to get your improved resume!"

    return msg


def build_conversation_handler() -> ConversationHandler:
    """Create and return the main ConversationHandler."""
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_JD: [
                MessageHandler(filters.Document.ALL, receive_jd),
                CommandHandler("cancel", cancel),
            ],
            WAITING_RESUME: [
                MessageHandler(filters.Document.ALL, receive_resume),
                CommandHandler("cancel", cancel),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
