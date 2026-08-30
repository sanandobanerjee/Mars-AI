from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import REPOS_DIR, TARGET_REPOS, CORE_PATHS
from src.ingestion.ast_parser import parse_repo
from src.ingestion.embedder import Embedder
from src.vectorstore.store import VectorStore
from src.ingestion.repo_utils import parse_github_url, make_repo_slug, detect_core_paths
from src.agent.graph_agent import CodeAgent
from src.api.ingestion_status import set_status, get_status, all_ready_repos, IngestState
from scripts.ingest import ingest, ingest_from_url


@asynccontextmanager
async def lifespan(app: FastAPI):
    for repo_name in TARGET_REPOS:
        set_status(repo_name, IngestState.INGESTING, "Pre-ingesting demo repo")
        chunk_count = ingest(repo_name)
        set_status(repo_name, IngestState.READY, chunk_count=chunk_count)
    yield


app = FastAPI(title="Mars API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_embedder = Embedder()
_agents: dict[str, CodeAgent] = {}


class QueryRequest(BaseModel):
    repo: str
    question: str


class IngestRequest(BaseModel):
    repo_url: str


def _load_agent(slug: str) -> CodeAgent:
    if slug in _agents:
        return _agents[slug]

    status = get_status(slug)
    if status is None or status.state != IngestState.READY:
        raise HTTPException(status_code=400, detail=f"Repo '{slug}' is not ready. Check /ingest/status/{slug}")

    repo_path = REPOS_DIR / slug
    core_paths = CORE_PATHS.get(slug) or detect_core_paths(repo_path)
    chunks = parse_repo(repo_path, core_paths=core_paths)
    store = VectorStore(collection_name=slug)

    if store.count() != len(chunks):
        raise HTTPException(status_code=400, detail=f"Repo '{slug}' ingestion mismatch. Try re-ingesting.")

    agent = CodeAgent(chunks, store, _embedder)
    _agents[slug] = agent
    return agent


def _background_ingest(repo_url: str, slug: str) -> None:
    try:
        ingest_from_url(repo_url, force=False)
        store = VectorStore(collection_name=slug)
        set_status(slug, IngestState.READY, chunk_count=store.count())
    except Exception as e:
        set_status(slug, IngestState.ERROR, message=str(e))


@app.get("/repos")
def list_repos():
    return {"repos": all_ready_repos()}


@app.post("/ingest")
def start_ingest(req: IngestRequest, background_tasks: BackgroundTasks):
    try:
        owner, repo = parse_github_url(req.repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    slug = make_repo_slug(owner, repo)
    existing = get_status(slug)
    if existing and existing.state in (IngestState.READY, IngestState.INGESTING):
        return {"slug": slug, "state": existing.state}

    set_status(slug, IngestState.INGESTING, message="Cloning and ingesting")
    background_tasks.add_task(_background_ingest, req.repo_url, slug)
    return {"slug": slug, "state": IngestState.INGESTING}


@app.get("/ingest/status/{slug}")
def ingest_status(slug: str):
    status = get_status(slug)
    if status is None:
        raise HTTPException(status_code=404, detail="Unknown repo slug")
    return status


@app.post("/query")
def query(req: QueryRequest):
    agent = _load_agent(req.repo)
    result = agent.query(req.question)
    return result