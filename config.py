import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "Autonomous Financial Advisor Agent"
APP_VERSION = "2.0.0"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_PRIMARY = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_MODEL_FAST = "llama-3.1-8b-instant"

# Observability
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

# API Settings
API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", "30"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL", "300"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))

# CORS
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
