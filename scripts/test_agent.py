import sys
from git import Repo
from pathlib import Path

from src.config import REPOS_DIR, TARGET_REPOS, CORE_PATHS
from src.ingestion.ast_parser import parse_repo
from src.ingestion.embedder import Embedder
from src.vectorstore.store import VectorStore
from src.agent.graph_agent import CodeAgent


def clone_if_missing(name: str, url: str) -> Path:
    dest = REPOS_DIR / name
    if not dest.exists():
        Repo.clone_from(url, dest)
    return dest


if __name__ == "__main__":
    repo_name = sys.argv[1] if len(sys.argv) > 1 else "tqdm"

    repo_path = clone_if_missing(repo_name, TARGET_REPOS[repo_name])
    chunks = parse_repo(repo_path, core_paths=CORE_PATHS[repo_name])

    store = VectorStore(collection_name=repo_name)
    if store.count() != len(chunks):
        print(
            f"Collection '{repo_name}' has {store.count()} chunks, expected {len(chunks)}.\n"
            f"Run: python -m scripts.ingest {repo_name}"
        )
        sys.exit(1)

    embedder = Embedder()
    agent = CodeAgent(chunks, store, embedder)

    questions = [
        "How does tqdm calculate the estimated time remaining?",
        "What calls the update method?",
    ]

    for q in questions:
        print(f"\n{'='*60}\nQuestion: {q}\n{'='*60}")
        result = agent.query(q)
        print(f"Hops used: {result['hops_used']}")
        print(f"Answer: {result['answer']}")
        print(f"Citations ({len(result['citations'])}):")
        for c in result["citations"][:5]:
            print(f"  - {c['qualified_name']} ({c['file_path']}:{c['start_line']})")