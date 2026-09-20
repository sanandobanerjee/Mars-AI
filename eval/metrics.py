from typing import List,Optional
from eval.schemas import EvalQuestion

def citation_precision(question:EvalQuestion,actual_citations:List[dict])->Optional[float]:
    if question.difficulty == "adversarial" or not question.expected_citations:
        return None

    expected_names={c.qualified_name for c in question.expected_citations}
    actual_names={c["qualified_name"] for c in actual_citations}

    matched=expected_names & actual_names
    return len(matched)/len(expected_names)