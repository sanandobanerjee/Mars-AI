import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

from src.config import REPOS_DIR, TARGET_REPOS, CORE_PATHS
from src.ingestion.ast_parser import parse_repo
from src.ingestion.embedder import Embedder
from src.vectorstore.store import VectorStore
from src.agent.graph_agent import CodeAgent
from scripts.ingest import ingest

from eval.schemas import EvalQuestion, EvalResult
from eval.judge import judge_answer
from eval.metrics import citation_precision

EVAL_DATA_DIR = Path(__file__).resolve().parent / "data"
EVAL_RESULTS_DIR = Path(__file__).resolve().parent / "results"
BY_REPO_DIR = EVAL_RESULTS_DIR / "by_repo"


def load_questions(repo_name: str) -> List[EvalQuestion]:
    path = EVAL_DATA_DIR / f"{repo_name}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [EvalQuestion(**item) for item in raw]


def build_agent(repo_name: str, embedder: Embedder) -> CodeAgent:
    ingest(repo_name)
    repo_path = REPOS_DIR / repo_name
    chunks = parse_repo(repo_path, core_paths=CORE_PATHS[repo_name])
    store = VectorStore(collection_name=repo_name)
    return CodeAgent(chunks, store, embedder)


def repo_already_complete(repo_name: str, expected_count: int) -> bool:
    path = BY_REPO_DIR / f"{repo_name}.json"
    if not path.exists():
        return False
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
        return len(existing) >= expected_count
    except (json.JSONDecodeError, OSError):
        return False


def save_repo_results(repo_name: str, results: List[EvalResult]) -> None:
    BY_REPO_DIR.mkdir(parents=True, exist_ok=True)
    path = BY_REPO_DIR / f"{repo_name}.json"
    path.write_text(json.dumps([r.model_dump() for r in results], indent=2), encoding="utf-8")


def load_repo_results(repo_name: str) -> List[EvalResult]:
    path = BY_REPO_DIR / f"{repo_name}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [EvalResult(**item) for item in raw]


def run_eval_for_repo(repo_name: str, embedder: Embedder) -> Tuple[List[EvalResult], bool]:
    questions = load_questions(repo_name)
    agent = build_agent(repo_name, embedder)
    results: List[EvalResult] = []
    rate_limited = False

    for q in questions:
        print(f"  [{q.id}] {q.question}")
        try:
            response = agent.query(q.question)
            precision = citation_precision(q, response["citations"])
            score = judge_answer(q, response["answer"])

            results.append(EvalResult(
                id=q.id,
                repo=q.repo,
                difficulty=q.difficulty,
                question=q.question,
                answer=response["answer"],
                hops_used=response["hops_used"],
                citation_precision=precision,
                judge=score,
            ))
        except Exception as e:
            print(f"    Failed on {q.id}: {type(e).__name__}: {e}")
            print(f"    Stopping {repo_name} early. {len(results)}/{len(questions)} questions completed.")
            rate_limited = True
            break

        time.sleep(1)

    save_repo_results(repo_name, results)
    return results, rate_limited


def summarize(results: List[EvalResult]) -> dict:
    by_difficulty: dict = {}
    for r in results:
        by_difficulty.setdefault(r.difficulty, []).append(r)

    summary = {"total_questions": len(results), "by_difficulty": {}}

    for difficulty, group in by_difficulty.items():
        avg_faithfulness = sum(r.judge.faithfulness for r in group) / len(group)
        avg_correctness = sum(r.judge.correctness for r in group) / len(group)

        precisions = [r.citation_precision for r in group if r.citation_precision is not None]
        avg_precision = sum(precisions) / len(precisions) if precisions else None

        entry = {
            "count": len(group),
            "avg_faithfulness": round(avg_faithfulness, 3),
            "avg_correctness": round(avg_correctness, 3),
            "avg_citation_precision": round(avg_precision, 3) if avg_precision is not None else None,
        }

        if difficulty == "adversarial":
            avoided = [r.judge.avoided_fabrication for r in group if r.judge.avoided_fabrication is not None]
            entry["fabrication_avoidance_rate"] = round(sum(1 for a in avoided if a) / len(avoided), 3) if avoided else None

        if difficulty == "multi_hop":
            entry["hop_trigger_rate"] = round(sum(1 for r in group if r.hops_used > 0) / len(group), 3)

        summary["by_difficulty"][difficulty] = entry

    return summary


if __name__ == "__main__":
    EVAL_RESULTS_DIR.mkdir(exist_ok=True)
    embedder = Embedder()
    all_results: List[EvalResult] = []
    stopped_early = False

    for repo_name in TARGET_REPOS:
        questions = load_questions(repo_name)

        if repo_already_complete(repo_name, len(questions)):
            print(f"{repo_name} already fully evaluated ({len(questions)}/{len(questions)}). Skipping.")
            all_results.extend(load_repo_results(repo_name))
            continue

        print(f"Running eval for {repo_name}...")
        results, rate_limited = run_eval_for_repo(repo_name, embedder)
        all_results.extend(results)

        if rate_limited:
            stopped_early = True
            print(f"\nStopped early due to rate limit. Progress saved to eval/results/by_repo/{repo_name}.json")
            print("Rerun this script later to resume — completed repos will be skipped automatically.")
            break

    if not all_results:
        print("No results to summarize.")
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        output_path = EVAL_RESULTS_DIR / f"eval-{timestamp}.json"
        output_path.write_text(json.dumps([r.model_dump() for r in all_results], indent=2), encoding="utf-8")

        summary = summarize(all_results)
        summary_path = EVAL_RESULTS_DIR / f"summary-{timestamp}.json"
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        print(f"\nResults saved to {output_path}")
        print(f"Summary saved to {summary_path}")
        print(json.dumps(summary, indent=2))

    if stopped_early:
        print("\nNote: this run stopped early. The summary above reflects only completed questions.")