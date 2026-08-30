import re
from pathlib import Path
from typing import List,Tuple

GITHUB_URL_PATTERN = re.compile(
    r"^https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)

DENYLIST_DIRS = {
    "test", "tests", "__pycache__", ".venv", "venv", "env",
    "examples", "example", "docs", "doc", "benchmarks", "benchmark",
    ".github", "build", "dist", "node_modules", ".git",
}

def parse_github_url(url:str)-> Tuple[str,str]:
    match=GITHUB_URL_PATTERN.match(url.strip())
    if not match:
        raise ValueError(f"Not a valid GitHub repository URL: {url}")
    return match.group(1),match.group(2)

def make_repo_slug(owner: str, repo: str) -> str:
    raw = f"{owner}-{repo}".lower()
    slug = re.sub(r"[^a-z0-9_-]", "-", raw)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug[:63]

def detect_core_paths(repo_path: Path) -> List[str]:
    candidates = [
        item for item in repo_path.iterdir()
        if item.is_dir()
        and item.name not in DENYLIST_DIRS
        and not item.name.startswith(".")
        and (item / "__init__.py").exists()
    ]

    if not candidates:
        return ["."]

    best = max(candidates, key=lambda p: sum(1 for _ in p.rglob("*.py")))
    return [best.name]