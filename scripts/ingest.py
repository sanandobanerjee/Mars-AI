import sys
from git import Repo
from pathlib import Path

from src.config import REPOS_DIR, TARGET_REPOS, CORE_PATHS
from src.ingestion.ast_parser import parse_repo
from src.ingestion.embedder import Embedder
from src.vectorstore.store import VectorStore


def clone_if_missing(name: str, url: str) -> Path:
    dest = REPOS_DIR / name
    if not dest.exists():
        print(f"Cloning {name}...")
        Repo.clone_from(url, dest)
    return dest


def ingest(repo_name: str, force: bool = False) -> None:
    if repo_name not in TARGET_REPOS:
        print(f"Unknown repo '{repo_name}'. Options: {list(TARGET_REPOS.keys())}")
        sys.exit(1)

    repo_path = clone_if_missing(repo_name, TARGET_REPOS[repo_name])
    chunks = parse_repo(repo_path, core_paths=CORE_PATHS[repo_name])
    print(f"Parsed {len(chunks)} chunks from {repo_name}")

    store = VectorStore(collection_name=repo_name)
    existing_count = store.count()

    if existing_count == len(chunks) and not force:
        print(f"'{repo_name}' already ingested ({existing_count} chunks). Skipping. Use --force to re-ingest.")
        return

    if existing_count > 0:
        print(f"Existing collection has {existing_count} chunks, expected {len(chunks)}. Recreating collection.")
        store.client.delete_collection(name=repo_name)
        store = VectorStore(collection_name=repo_name)

    embedder = Embedder()
    embeddings = embedder.embed_chunks(chunks)
    store.add_chunks(chunks, embeddings)
    print(f"Ingested {store.count()} chunks into '{repo_name}' collection.")


if __name__ == "__main__":
    repo_name = sys.argv[1] if len(sys.argv) > 1 else "tqdm"
    force = "--force" in sys.argv
    ingest(repo_name, force=force)