from pydantic import BaseModel,Field
from typing import Optional,List

class Chunk(BaseModel):
    id: str
    type: str   #one of three
    name: str
    qualified_name:str
    file_path: str
    start_line: int
    end_line: int
    docstring: Optional[str]
    source: str
    calls: List[str] = Field(default_factory=list)