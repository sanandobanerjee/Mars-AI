import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List
from git import Repo

from src.config import REPOS_DIR, TARGET_REPOS, CORE_PATHS
from src.ingestion.ast_parser import parse_repo
from src.ingestion.embedder import Embedder
from src.vectorstore.store import VectorStore
from src.ingestion.repo_utils import parse_github_url, make_repo_slug, detect_core_paths, get_default_branch


@dataclass
class IngestResult:
    slug: str
    chunk_count: int
    owner: str
    repo: str
    default_branch: str


def clone_if_missing(dest: Path, url: str) -> Path:
    if not dest.exists():
        print(f"Cloning into {dest}...")
        Repo.clone_from(url, dest)
    return dest


def _run_ingestion(slug: str, repo_path: Path, core_paths: List[str], force: bool = False) -> int:
    chunks = parse_repo(repo_path, core_paths=core_paths)
    print(f"Parsed {len(chunks)} chunks from {slug}")

    if len(chunks) == 0:
        raise ValueError(
            f"No Python source files found in '{slug}'. Mars currently only supports "
            f"Python codebases (AST-based parsing) — JavaScript/TypeScript and other "
            f"languages aren't ingested yet."
        )

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


def ingest(repo_name: str, force: bool = False) -> IngestResult:
    if repo_name not in TARGET_REPOS:
        print(f"Unknown repo '{repo_name}'. Options: {list(TARGET_REPOS.keys())}")
        sys.exit(1)

    owner, repo = parse_github_url(TARGET_REPOS[repo_name])
    repo_path = clone_if_missing(REPOS_DIR / repo_name, TARGET_REPOS[repo_name])
    default_branch = get_default_branch(repo_path)
    chunk_count = _run_ingestion(repo_name, repo_path, CORE_PATHS[repo_name], force=force)
    return IngestResult(slug=repo_name, chunk_count=chunk_count, owner=owner, repo=repo, default_branch=default_branch)


def ingest_from_url(repo_url: str, force: bool = False) -> IngestResult:
    owner, repo = parse_github_url(repo_url)
    slug = make_repo_slug(owner, repo)
    repo_path = clone_if_missing(REPOS_DIR / slug, repo_url)
    core_paths = detect_core_paths(repo_path)
    default_branch = get_default_branch(repo_path)
    chunk_count = _run_ingestion(slug, repo_path, core_paths, force=force)
    return IngestResult(slug=slug, chunk_count=chunk_count, owner=owner, repo=repo, default_branch=default_branch)


if __name__ == "__main__":
    repo_name = sys.argv[1] if len(sys.argv) > 1 else "tqdm"
    force = "--force" in sys.argv
    result = ingest(repo_name, force=force)
    print(f"Slug: {result.slug}, chunks: {result.chunk_count}, owner: {result.owner}, repo: {result.repo}, branch: {result.default_branch}")