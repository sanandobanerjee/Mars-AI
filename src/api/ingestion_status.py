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


_status_store: Dict[str, IngestStatus] = {}


def set_status(slug: str, state: IngestState, message: str = "", chunk_count: int = 0) -> None:
    _status_store[slug] = IngestStatus(slug=slug, state=state, message=message, chunk_count=chunk_count)


def get_status(slug: str) -> Optional[IngestStatus]:
    return _status_store.get(slug)


def all_ready_repos() -> List[str]:
    return [s.slug for s in _status_store.values() if s.state == IngestState.READY]