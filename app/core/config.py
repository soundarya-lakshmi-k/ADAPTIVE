import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB: str = os.getenv("MONGODB_DB", "adaptive_engine")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    BASELINE_ABILITY: float = 0.5
    MAX_QUESTIONS: int = 10
    DIFFICULTY_BAND: float = 0.15
    MIN_DIFFICULTY: float = 0.1
    MAX_DIFFICULTY: float = 1.0
    IRT_LEARNING_RATE: float = 0.3
    IRT_DISCRIMINATION: float = 1.7

settings = Settings()