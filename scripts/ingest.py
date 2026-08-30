import sys
from pathlib import Path
from typing import List
from git import Repo

from src.config import REPOS_DIR, TARGET_REPOS, CORE_PATHS
from src.ingestion.ast_parser import parse_repo
from src.ingestion.embedder import Embedder
from src.vectorstore.store import VectorStore
from src.ingestion.repo_utils import parse_github_url, make_repo_slug, detect_core_paths


def clone_if_missing(dest: Path, url: str) -> Path:
    if not dest.exists():
        print(f"Cloning into {dest}...")
        Repo.clone_from(url, dest)
    return dest


def _run_ingestion(slug: str, repo_path: Path, core_paths: List[str], force: bool = False) -> int:
    chunks = parse_repo(repo_path, core_paths=core_paths)
    print(f"Parsed {len(chunks)} chunks from {slug}")

    store = VectorStore(collection_name=slug)
    existing_count = store.count()

    if existing_count == len(chunks) and not force:
        print(f"'{slug}' already ingested ({existing_count} chunks). Skipping.")
        return existing_count

    if existing_count > 0:
        store.client.delete_collection(name=slug)
        store = VectorStore(collection_name=slug)

    embedder = Embedder()
    embeddings = embedder.embed_chunks(chunks)
    store.add_chunks(chunks, embeddings)
    print(f"Ingested {store.count()} chunks into '{slug}' collection.")
    return store.count()


def ingest(repo_name: str, force: bool = False) -> int:
    if repo_name not in TARGET_REPOS:
        print(f"Unknown repo '{repo_name}'. Options: {list(TARGET_REPOS.keys())}")
        sys.exit(1)
    repo_path = clone_if_missing(REPOS_DIR / repo_name, TARGET_REPOS[repo_name])
    return _run_ingestion(repo_name, repo_path, CORE_PATHS[repo_name], force=force)


def ingest_from_url(repo_url: str, force: bool = False) -> str:
    owner, repo = parse_github_url(repo_url)
    slug = make_repo_slug(owner, repo)
    repo_path = clone_if_missing(REPOS_DIR / slug, repo_url)
    core_paths = detect_core_paths(repo_path)
    _run_ingestion(slug, repo_path, core_paths, force=force)
    return slug


if __name__ == "__main__":
    repo_name = sys.argv[1] if len(sys.argv) > 1 else "tqdm"
    force = "--force" in sys.argv
    ingest(repo_name, force=force)