from typing import TypedDict,List,Optional,Dict,Any

class AgentState(TypedDict):
    query:str
    accumulated_chunk_ids:List[str]
    visited_chunk_ids:List[str]
    hop_count:int
    needs_hop:bool
    final_answer:Optional[str]
    citations:List[Dict[str,Any]]
    