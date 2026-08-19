from sentence_transformers import SentenceTransformer
from typing import List

from src.config import EMBEDDING_MODEL
from src.ingestion.models import Chunk

class Embedder:
    def __init__(self, model_name: str=EMBEDDING_MODEL):
        self.model=SentenceTransformer(model_name)

    def _build_embedding_text(self,chunk:Chunk)->str:
        parts=[f"{chunk.type}:{chunk.qualified_name}"]
        if chunk.docstring:
            parts.append(chunk.docstring)
        parts.append(chunk.source)
        return "\n".join(parts)

    def embed_chunks(self,chunks:List[Chunk])->List[List[float]]:
        texts=[self._build_embedding_text(c) for c in chunks]
        embeddings=self.model.encode(texts, show_progress_bar=True,convert_to_numpy=True)
        return embeddings.tolist()