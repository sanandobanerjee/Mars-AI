from typing import List, Optional
from pydantic import BaseModel


class ExpectedCitation(BaseModel):
    qualified_name: str
    file_path: str


class EvalQuestion(BaseModel):
    id: str
    repo: str
    question: str
    ground_truth: str
    expected_citations: List[ExpectedCitation]
    difficulty: str


class JudgeScore(BaseModel):
    faithfulness: float
    correctness: float
    avoided_fabrication: Optional[bool] = None
    reasoning: str = ""


class EvalResult(BaseModel):
    id: str
    repo: str
    difficulty: str
    question: str
    answer: str
    hops_used: int
    citation_precision: Optional[float] = None
    actual_citations: List[dict] = []
    judge: JudgeScore