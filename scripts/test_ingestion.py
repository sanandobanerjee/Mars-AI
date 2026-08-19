from git import Repo
from pathlib import Path

from src.config import REPOS_DIR, TARGET_REPOS, CORE_PATHS
from src.ingestion.ast_parser import parse_repo
from src.graph.call_graph import CallGraph


def clone_if_missing(name: str, url: str) -> Path:
    dest = REPOS_DIR / name
    if not dest.exists():
        Repo.clone_from(url, dest)
    return dest


if __name__ == "__main__":
    repo_name = "tqdm"
    repo_path = clone_if_missing(repo_name, TARGET_REPOS[repo_name])
    chunks = parse_repo(repo_path, core_paths=CORE_PATHS[repo_name])

    graph = CallGraph(chunks)
    print(f"Graph stats: {graph.stats()}")

    sample = next(c for c in chunks if c.qualified_name == "tqdm.update")
    callees = graph.get_callees(sample.id, max_hops=1)
    callers = graph.get_callers(sample.id, max_hops=1)

    print(f"\nSample: {sample.qualified_name}")
    print(f"  Calls: {sample.calls}")
    print(f"  Resolved callees ({len(callees)}):")
    for cid in callees:
        print(f"    - {graph.chunks_by_id[cid].qualified_name}")
    print(f"  Resolved callers ({len(callers)}):")
    for cid in callers:
        print(f"    - {graph.chunks_by_id[cid].qualified_name}")