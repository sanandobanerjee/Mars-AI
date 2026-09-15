from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel


class IngestState(str, Enum):
    PENDING = "pending"
    INGESTING = "ingesting"
    READY = "ready"
    ERROR = "error"


class IngestStatus(BaseModel):
    slug: str
    state: IngestState
    message: str = ""
    chunk_count: int = 0
    owner: str = ""
    repo: str = ""
    default_branch: str = "main"


_status_store: Dict[str, IngestStatus] = {}


def set_status(
    slug: str,
    state: IngestState,
    message: str = "",
    chunk_count: int = 0,
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    default_branch: Optional[str] = None,
) -> None:
    existing = _status_store.get(slug)
    _status_store[slug] = IngestStatus(
        slug=slug,
        state=state,
        message=message,
        chunk_count=chunk_count,
        owner=owner if owner is not None else (existing.owner if existing else ""),
        repo=repo if repo is not None else (existing.repo if existing else ""),
        default_branch=default_branch if default_branch is not None else (existing.default_branch if existing else "main"),
    )


def get_status(slug: str) -> Optional[IngestStatus]:
    return _status_store.get(slug)


def all_ready_repos() -> List[str]:
    return [s.slug for s in _status_store.values() if s.state == IngestState.READY]