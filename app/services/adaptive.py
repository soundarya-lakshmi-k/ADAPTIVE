import math
import random
from app.core.config import settings
from app.models.schemas import QuestionDocument

def irt_probability(ability: float, difficulty: float) -> float:
    a = settings.IRT_DISCRIMINATION
    logit = a * (ability - difficulty)
    return 1.0 / (1.0 + math.exp(-logit))

def update_ability(ability: float, correct: bool, difficulty: float) -> float:
    p = irt_probability(ability, difficulty)
    response = 1.0 if correct else 0.0
    delta = settings.IRT_LEARNING_RATE * (response - p)
    new_ability = ability + delta
    return round(max(settings.MIN_DIFFICULTY, min(settings.MAX_DIFFICULTY, new_ability)), 4)

def select_next_question(ability: float, available_questions: list) -> QuestionDocument | None:
    if not available_questions:
        return None
    band = settings.DIFFICULTY_BAND
    in_band = [q for q in available_questions if abs(q.difficulty - ability) <= band]
    pool = in_band if in_band else available_questions
    pool.sort(key=lambda q: (round(abs(q.difficulty - ability), 2), random.random()))
    return pool[0]

def compute_performance_summary(responses: list) -> dict:
    if not responses:
        return {}
    topic_stats = {}
    for r in responses:
        t = r["topic"]
        if t not in topic_stats:
            topic_stats[t] = {"correct": 0, "total": 0, "difficulties": []}
        topic_stats[t]["total"] += 1
        topic_stats[t]["correct"] += int(r["correct"])
        topic_stats[t]["difficulties"].append(r["difficulty"])
    topic_accuracy = {
        t: {
            "accuracy": round(v["correct"] / v["total"], 2),
            "avg_difficulty": round(sum(v["difficulties"]) / len(v["difficulties"]), 2),
            "total": v["total"],
        }
        for t, v in topic_stats.items()
    }
    sorted_topics = sorted(topic_accuracy.items(), key=lambda x: x[1]["accuracy"])
    weakest = sorted_topics[0][0] if sorted_topics else None
    strongest = sorted_topics[-1][0] if sorted_topics else None
    overall_accuracy = round(sum(int(r["correct"]) for r in responses) / len(responses), 2)
    return {
        "topic_accuracy": topic_accuracy,
        "weakest_topic": weakest,
        "strongest_topic": strongest,
        "overall_accuracy": overall_accuracy,
        "total_questions": len(responses),
    }