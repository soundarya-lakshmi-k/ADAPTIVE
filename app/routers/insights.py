from fastapi import APIRouter, HTTPException
from app.core.database import get_db
from app.models.schemas import StudyPlan
from app.services.adaptive import compute_performance_summary
from app.services.insights import generate_study_plan

router = APIRouter()

@router.get("/{session_id}")
async def get_study_plan(session_id: str):
    db = get_db()
    session = await db.sessions.find_one({"session_id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session["is_complete"]:
        raise HTTPException(status_code=400, detail="Study plan only available after test is complete")
    responses = session.get("responses", [])
    performance = compute_performance_summary(responses)
    plan = await generate_study_plan(
        performance=performance,
        final_ability=session["ability"],
        weakest_topic=performance.get("weakest_topic"),
        strongest_topic=performance.get("strongest_topic"),
    )
    return plan