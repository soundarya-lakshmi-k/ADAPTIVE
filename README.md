# Adaptive Diagnostic Engine

A production-grade **1-Dimension Computerised Adaptive Testing (CAT)** system for GRE preparation. The engine uses **Item Response Theory (IRT)** to dynamically select questions and estimate student proficiency, then leverages an LLM to generate a personalised study plan.

---

## Architecture Overview

```
adaptive-engine/
├── app/
│   ├── main.py               # FastAPI app, lifespan hooks, middleware
│   ├── core/
│   │   ├── config.py         # Centralised settings (env-var driven)
│   │   └── database.py       # Motor async MongoDB client + index setup
│   ├── models/
│   │   └── schemas.py        # Pydantic v2 models for all documents/DTOs
│   ├── routers/
│   │   ├── sessions.py       # Session creation & retrieval
│   │   ├── questions.py      # Answer submission & next-question logic
│   │   └── insights.py       # AI study plan generation
│   └── services/
│       ├── adaptive.py       # IRT core: P(correct), ability update, question selection
│       └── insights.py       # LLM dispatch (Anthropic / OpenAI / fallback)
├── scripts/
│   └── seed_questions.py     # Inserts 25 GRE-style questions into MongoDB
├── tests/
│   └── test_adaptive.py      # Pytest unit tests for the IRT algorithm
├── .env.example
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- MongoDB (local on port 27017 or a MongoDB Atlas URI)

### 2. Clone & install

```bash
git clone https://github.com/your-username/adaptive-engine.git
cd adaptive-engine
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env — set MONGODB_URI and at least one LLM key
```

| Variable | Default | Description |
|---|---|---|
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DB` | `adaptive_engine` | Database name |
| `GEMINI_API_KEY` | _(empty)_ | API key (preferred) |


### 4. Seed the database

```bash
python scripts/seed_questions.py
# → Inserted 25 questions into 'adaptive_engine.questions'
```

### 5. Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

Visit **http://localhost:8000/docs** for the interactive Swagger UI.

### 6. Run unit tests

```bash
pytest tests/ -v
```

---

## API Documentation

### Sessions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/sessions/` | Start a new test session. Returns `session_id` and the first question. |
| `GET` | `/api/sessions/{session_id}` | Get current session state (ability, progress). |
| `GET` | `/api/sessions/{session_id}/results` | Full result breakdown after test completion. |

#### POST /api/sessions/
```json
// Request body
{ "student_name": "Alice" }

// Response
{
  "session_id": "uuid-...",
  "student_name": "Alice",
  "ability": 0.5,
  "max_questions": 10,
  "first_question": {
    "question_id": "alg-003",
    "text": "If f(x) = 2x² − 3x + 1, what is f(−1)?",
    "options": { "A": "0", "B": "4", "C": "6", "D": "−4" },
    "difficulty": 0.45,
    "topic": "Algebra",
    "tags": ["functions", "substitution"]
  }
}
```

---

### Questions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/questions/submit` | Submit an answer. Returns correctness, updated ability, and next question. |
| `GET` | `/api/questions/` | List all questions (admin view, no correct answers). |

#### POST /api/questions/submit
```json
// Request body
{
  "session_id": "uuid-...",
  "question_id": "alg-003",
  "selected_answer": "C"
}

// Response
{
  "correct": true,
  "correct_answer": "C",
  "explanation": "f(−1) = 2(1) − 3(−1) + 1 = 6.",
  "updated_ability": 0.617,
  "questions_remaining": 9,
  "next_question": { ... },
  "test_complete": false
}
```

---

### AI Insights

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/insights/{session_id}` | Generate a 3-step LLM study plan (session must be complete). |

#### GET /api/insights/{session_id}
```json
{
  "summary": "You scored 70% with an ability estimate of 0.64, placing you at an intermediate level.",
  "steps": [
    { "step": 1, "title": "Strengthen Vocabulary Analogies", "detail": "..." },
    { "step": 2, "title": "Timed Algebra Drills", "detail": "..." },
    { "step": 3, "title": "Full Adaptive Mock Test", "detail": "..." }
  ],
  "estimated_ability": 0.64,
  "strongest_topic": "Geometry",
  "weakest_topic": "Vocabulary"
}
```

---

## Adaptive Algorithm Logic

### IRT Model — Rasch (1-PL)

The engine uses the **1-Parameter Logistic (Rasch) model**:

```
P(correct | θ, b) = 1 / (1 + exp(−a(θ − b)))
```

Where:
- **θ** = student ability estimate (0.1 – 1.0)
- **b** = item difficulty (0.1 – 1.0)  
- **a** = discrimination parameter, fixed at **1.7** (standard normal-ogive approximation)

### Ability Update — Gradient Ascent

After each response, ability is updated using one step of gradient ascent on the Rasch log-likelihood:

```
θ_new = θ_old + η × (r − P(correct | θ, b))
```

- **r** = 1 (correct) or 0 (incorrect)
- **η** = 0.3 (learning rate / step size)
- **P(...)** = IRT probability of a correct response

This is mathematically equivalent to one Newton–Raphson step and is standard in operational CAT systems.

### Question Selection — Maximum Information

At each step, the engine selects the question with **difficulty closest to current θ** from questions not yet seen. In the Rasch model, Fisher information is maximised when `b ≈ θ`, making this the statistically optimal strategy.

```
argmin_{q ∈ unseen} |q.difficulty − θ|
```

A small random tie-break within a ±0.15 band prevents item-exposure bias.

---

## MongoDB Schema

### `questions` collection
```json
{
  "question_id": "alg-005",
  "text": "The roots of ax² + bx + c = 0 are real and equal...",
  "options": { "A": "...", "B": "...", "C": "...", "D": "..." },
  "correct_answer": "C",
  "difficulty": 0.80,
  "topic": "Algebra",
  "tags": ["discriminant", "quadratic theory"],
  "explanation": "Equal roots ↔ discriminant = 0."
}
```

**Indexes:** `(difficulty, topic)` compound index + `tags` index for fast question retrieval.

### `sessions` collection
```json
{
  "session_id": "uuid-...",
  "student_name": "Alice",
  "ability": 0.64,
  "questions_asked": ["alg-003", "geo-002", ...],
  "responses": [
    {
      "question_id": "alg-003",
      "topic": "Algebra",
      "difficulty": 0.45,
      "selected_answer": "C",
      "correct": true,
      "ability_before": 0.5,
      "ability_after": 0.617,
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "is_complete": false,
  "created_at": "2024-01-15T10:29:00Z"
}
```

**Indexes:** `session_id` (unique) + `created_at` descending for pagination.

---

## AI Log — How AI Tools Were Used

### What worked extremely well

**Claude (Anthropic) — Architecture & IRT implementation**  
Claude was used to draft the IRT probability function and ability update rule. The prompt was:
> *"Implement a 1-PL Rasch model ability update using gradient ascent on the log-likelihood. Student ability and item difficulty are both on a 0-1 scale. Show the math and then the Python."*  
Claude produced the exact formula with a clear derivation, which was then validated against published CAT literature.

**Code scaffolding**  
Claude generated the initial FastAPI router structure, Pydantic v2 models, and Motor async patterns in a single pass, saving ~2 hours of boilerplate work.

**LLM prompt engineering**  
The system prompt for the study plan generator was iteratively refined with Claude to produce structured JSON reliably. Key discovery: explicitly saying "Respond ONLY with valid JSON — no markdown, no preamble" eliminated all formatting issues.

### Challenges AI couldn't fully solve

1. **MongoDB index strategy** — AI suggested indexes but couldn't know our exact query access patterns upfront. The compound `(difficulty, topic)` index was determined after profiling real query plans.

2. **IRT learning rate tuning** — The η=0.3 step size was chosen empirically. AI correctly noted that the optimal value depends on test length and question bank size, but couldn't compute it without simulation data.

3. **Edge-case question exhaustion** — Handling the case where all questions in the target difficulty band have been exhausted required custom fallback logic that AI drafts missed on the first pass.

---

## Evaluation Criteria Addressed

| Criteria | Implementation |
|----------|---------------|
| **System Design** | Compound MongoDB indexes; clean separation of concerns (router → service → DB); async throughout |
| **Algorithmic Logic** | Rasch 1-PL IRT with gradient-ascent ability update; maximum-information question selection |
| **AI Proficiency** | Structured JSON prompting;graceful fallback |
| **Code Hygiene** | Full type hints; Pydantic v2 validation; env-var config; try/catch throughout; pytest suite |# ADAPTIVE
