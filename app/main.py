"""
Root entry point — run with: uvicorn main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import connect_db, disconnect_db
from app.routers import sessions, questions, insights


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()


app = FastAPI(
    title="Adaptive Diagnostic Engine",
    description="A 1D Adaptive Testing system using IRT to assess student proficiency",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(questions.router, prefix="/api/questions", tags=["Questions"])
app.include_router(insights.router, prefix="/api/insights", tags=["AI Insights"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "service": "Adaptive Diagnostic Engine",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}