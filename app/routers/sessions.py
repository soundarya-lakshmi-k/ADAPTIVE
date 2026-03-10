import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.core.database import get_db
from app.core.config import settings
from app.models.schemas import SessionCreate, SessionDocument, SessionOut, QuestionOut, QuestionDocument
from app.services.adaptive import select_next_question

router = APIRouter()

@router.post("/", status_code=201)
async def create_session(payload: SessionCreate):
    db = get_db()
    session_id = str(uuid.uuid4())
    session = SessionDocument(
        session_id=session_id,
        student_name=payload.student_name,
        ability=settings.BASELINE_ABILITY,
    )
    await db.sessions.insert_one(session.model_dump())
    questions_cursor = db.questions.find({}, {"_id": 0})
    all_questions = [QuestionDocument(**q) async for q in questions_cursor]
    first_q = select_next_question(settings.BASELINE_ABILITY, all_questions)
    if not first_q:
        raise HTTPException(status_code=500, detail="No questions found. Run seed script.")
    await db.sessions.update_one(
        {"session_id": session_id},
        {"$push": {"questions_asked": first_q.question_id}},
    )
    return {
        "session_id": session_id,
        "student_name": payload.student_name,
        "ability": settings.BASELINE_ABILITY,
        "max_questions": settings.MAX_QUESTIONS,
        "first_question": QuestionOut(**first_q.model_dump()).model_dump(),
    }

@router.get("/{session_id}")
async def get_session(session_id: str):
    db = get_db()
    doc = await db.sessions.find_one({"session_id": session_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionOut(
        session_id=doc["session_id"],
        student_name=doc["student_name"],
        ability=doc["ability"],
        questions_answered=len(doc["responses"]),
        is_complete=doc["is_complete"],
        created_at=doc["created_at"],
    )

@router.get("/{session_id}/results")
async def get_session_results(session_id: str):
    db = get_db()
    doc = await db.sessions.find_one({"session_id": session_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found")
    if not doc["is_complete"]:
        raise HTTPException(status_code=400, detail="Session is not yet complete")
    responses = doc.get("responses", [])
    correct_count = sum(1 for r in responses if r["correct"])
    return {
        "session_id": session_id,
        "student_name": doc["student_name"],
        "final_ability": doc["ability"],
        "total_questions": len(responses),
        "correct_answers": correct_count,
        "accuracy": round(correct_count / len(responses), 2) if responses else 0,
        "responses": responses,
        "completed_at": doc.get("completed_at"),
    }