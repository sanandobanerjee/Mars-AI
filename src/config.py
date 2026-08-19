import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "openai/gpt-oss-20b"

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "data" / "chroma"))
REPOS_DIR = BASE_DIR / "data" / "repos"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

MAX_HOP_COUNT = 3
CHUNK_TYPES = ("function", "method", "class_summary")

TARGET_REPOS = {
    "tqdm": "https://github.com/tqdm/tqdm.git",
    "requests": "https://github.com/psf/requests.git",
    "flask": "https://github.com/pallets/flask.git",
    "httpx": "https://github.com/encode/httpx.git",
}

CORE_PATHS = {
    "tqdm": ["tqdm"],
    "requests": ["src/requests"],
    "flask": ["src/flask"],
    "httpx": ["httpx"],
}