from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field

class QuestionDocument(BaseModel):
    question_id: str
    text: str
    options: dict
    correct_answer: str
    difficulty: float
    topic: str
    tags: list
    explanation: str = ""

class QuestionOut(BaseModel):
    question_id: str
    text: str
    options: dict
    difficulty: float
    topic: str
    tags: list

class AnswerIn(BaseModel):
    session_id: str
    question_id: str
    selected_answer: str

class AnswerResult(BaseModel):
    correct: bool
    correct_answer: str
    explanation: str
    updated_ability: float
    questions_remaining: int
    next_question: QuestionOut | None = None
    test_complete: bool = False

class ResponseRecord(BaseModel):
    question_id: str
    topic: str
    difficulty: float
    selected_answer: str
    correct: bool
    ability_before: float
    ability_after: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SessionDocument(BaseModel):
    session_id: str
    student_name: str = "Anonymous"
    ability: float = 0.5
    questions_asked: list = Field(default_factory=list)
    responses: list = Field(default_factory=list)
    is_complete: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

class SessionCreate(BaseModel):
    student_name: str = "Anonymous"

class SessionOut(BaseModel):
    session_id: str
    student_name: str
    ability: float
    questions_answered: int
    is_complete: bool
    created_at: datetime

class StudyPlan(BaseModel):
    summary: str
    steps: list
    estimated_ability: float
    strongest_topic: str | None
    weakest_topic: str | None