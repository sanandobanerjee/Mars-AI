import chromadb
from typing import List,Optional

from src.config import CHROMA_PERSIST_DIR
from src.ingestion.models import Chunk

class VectorStore:
    def __init__(self,collection_name:str,persist_dir:str=CHROMA_PERSIST_DIR):
        self.client=chromadb.PersistentClient(
            path=persist_dir,
            settings=chromadb.Settings(anonymized_telemetry=False)
        )
        self.collection=self.client.get_or_create_collection(name=collection_name)

    def add_chunks(self,chunks:List[Chunk],embeddings:List[List[float]])->None:
        self.collection.add(
            ids=[c.id for c in chunks],
            embeddings=embeddings,
            documents=[c.source for c in chunks],
            metadatas=[
                {
                    "type": c.type,
                    "name": c.name,
                    "qualified_name": c.qualified_name,
                    "file_path": c.file_path,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "docstring": c.docstring or ""
                }
                for c in chunks
            ],
        )

    def query(self,query_embedding:List[float],n_results:int=5,chunk_type: Optional[str]=None)->dict:
        where_filter={"type":chunk_type} if chunk_type else None
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter
        )

    def count(self)->int:
        return self.collection.count()