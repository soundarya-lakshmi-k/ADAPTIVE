from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.core.database import get_db
from app.core.config import settings
from app.models.schemas import AnswerIn, AnswerResult, QuestionDocument, QuestionOut, ResponseRecord
from app.services.adaptive import select_next_question, update_ability

router = APIRouter()

@router.post("/submit")
async def submit_answer(payload: AnswerIn):
    db = get_db()
    session = await db.sessions.find_one({"session_id": payload.session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["is_complete"]:
        raise HTTPException(status_code=400, detail="Session already complete")
    question = await db.questions.find_one({"question_id": payload.question_id}, {"_id": 0})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    q = QuestionDocument(**question)
    correct = payload.selected_answer.upper() == q.correct_answer.upper()
    ability_before = session["ability"]
    ability_after = update_ability(ability_before, correct, q.difficulty)
    record = ResponseRecord(
        question_id=q.question_id,
        topic=q.topic,
        difficulty=q.difficulty,
        selected_answer=payload.selected_answer.upper(),
        correct=correct,
        ability_before=ability_before,
        ability_after=ability_after,
    )
    questions_answered = len(session["responses"]) + 1
    is_complete = questions_answered >= settings.MAX_QUESTIONS
    update_doc = {
        "$set": {"ability": ability_after},
        "$push": {"responses": record.model_dump()},
    }
    if is_complete:
        update_doc["$set"]["is_complete"] = True
        update_doc["$set"]["completed_at"] = datetime.utcnow()
    await db.sessions.update_one({"session_id": payload.session_id}, update_doc)
    next_question = None
    if not is_complete:
        asked_ids = session["questions_asked"] + [q.question_id]
        remaining_cursor = db.questions.find({"question_id": {"$nin": asked_ids}}, {"_id": 0})
        remaining = [QuestionDocument(**doc) async for doc in remaining_cursor]
        chosen = select_next_question(ability_after, remaining)
        if chosen:
            await db.sessions.update_one(
                {"session_id": payload.session_id},
                {"$push": {"questions_asked": chosen.question_id}},
            )
            next_question = QuestionOut(**chosen.model_dump())
    return AnswerResult(
        correct=correct,
        correct_answer=q.correct_answer,
        explanation=q.explanation,
        updated_ability=ability_after,
        questions_remaining=max(0, settings.MAX_QUESTIONS - questions_answered),
        next_question=next_question,
        test_complete=is_complete,
    )

@router.get("/")
async def list_questions(topic: str = None, limit: int = 20):
    db = get_db()
    query = {"topic": topic} if topic else {}
    cursor = db.questions.find(query, {"_id": 0}).limit(limit)
    return [QuestionOut(**doc) async for doc in cursor]