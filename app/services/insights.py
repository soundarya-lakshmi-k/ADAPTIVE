import json
from typing import Any
import httpx
from app.core.config import settings
from app.models.schemas import StudyPlan

def _build_prompt(performance: dict, final_ability: float) -> str:
    topic_lines = "\n".join(
        f"  - {topic}: {stats['accuracy']*100:.0f}% accuracy "
        f"(avg difficulty {stats['avg_difficulty']:.2f}, {stats['total']} Qs)"
        for topic, stats in performance.get("topic_accuracy", {}).items()
    )
    return f"""You are an expert GRE tutor analysing a student's adaptive test results.

## Student Performance Data
- Final Ability Estimate: {final_ability:.3f} / 1.0
- Overall Accuracy: {performance.get('overall_accuracy', 0)*100:.0f}%
- Questions Answered: {performance.get('total_questions', 0)}
- Strongest Topic: {performance.get('strongest_topic', 'N/A')}
- Weakest Topic: {performance.get('weakest_topic', 'N/A')}

## Topic Breakdown
{topic_lines}

Respond ONLY with valid JSON, no markdown, no extra text:
{{
  "summary": "One sentence summarising performance",
  "steps": [
    {{"step": 1, "title": "Short title", "detail": "2-3 sentence actionable advice"}},
    {{"step": 2, "title": "Short title", "detail": "2-3 sentence actionable advice"}},
    {{"step": 3, "title": "Short title", "detail": "2-3 sentence actionable advice"}}
  ]
}}"""

async def generate_study_plan(
    performance: dict,
    final_ability: float,
    weakest_topic: str | None,
    strongest_topic: str | None,
) -> StudyPlan:
    prompt = _build_prompt(performance, final_ability)
    
    if settings.GEMINI_API_KEY:
        try:
            raw_json = await _call_gemini(prompt)
        except Exception:
            raw_json = _fallback_plan(performance, final_ability)
    else:
        raw_json = _fallback_plan(performance, final_ability)

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        # Cleanup potential markdown backticks if Gemini ignores the system prompt
        cleaned = raw_json.strip().removeprefix("```json").removesuffix("```").strip()
        data = json.loads(cleaned)

    return StudyPlan(
        summary=data["summary"],
        steps=data["steps"],
        estimated_ability=final_ability,
        strongest_topic=strongest_topic,
        weakest_topic=weakest_topic,
    )

async def _call_gemini(prompt: str) -> str:
    # Constructing the URL for Gemini 2.0 Flash
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models"
        f"/gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}"
    )
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 800,
            "temperature": 0.3,
            "responseMimeType": "application/json",
        },
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
    return data["candidates"][0]["content"]["parts"][0]["text"]

def _fallback_plan(performance: dict, ability: float) -> str:
    weakest = performance.get("weakest_topic", "general reasoning")
    accuracy = performance.get("overall_accuracy", 0)
    level = "beginner" if ability < 0.4 else "intermediate" if ability < 0.7 else "advanced"
    
    plan = {
        "summary": f"You scored {accuracy*100:.0f}% with ability {ability:.2f}/1.0, placing you at {level} level.",
        "steps": [
            {"step": 1, "title": f"Master {weakest} Fundamentals", "detail": f"Spend 3-4 sessions on core {weakest} concepts. Work through 20 practice problems at difficulty 0.3-0.5."},
            {"step": 2, "title": "Timed Mixed Drills", "detail": "Complete 2 timed 15-question drills mixing all topics. Aim for 90 seconds per question."},
            {"step": 3, "title": "Full Mock Test", "detail": "Take a full adaptive mock test under exam conditions. Aim to reach 0.65+ ability before your GRE date."},
        ],
    }
    return json.dumps(plan)