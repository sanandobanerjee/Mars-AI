from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from typing import List, Dict
from tenacity import retry,stop_after_attempt,wait_exponential,retry_if_exception_type
from groq import RateLimitError

from src.config import GROQ_API_KEY, GROQ_MODEL, MAX_HOP_COUNT,MAX_ACCUMULATED_CHUNKS,MAX_CONTEXT_CHARS
from src.agent.state import AgentState
from src.vectorstore.store import VectorStore
from src.ingestion.embedder import Embedder
from src.graph.call_graph import CallGraph
from src.ingestion.models import Chunk

class CodeAgent:
    @retry(
        retry=retry_if_exception_type(RateLimitError),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(4),
    )
    def _call_llm(self, prompt: str) -> str:
        response = self.llm.invoke(prompt)
        return response.content.strip()

    def __init__(self, chunks: List[Chunk], vector_store: VectorStore, embedder: Embedder):
        self.chunks_by_id: Dict[str, Chunk] = {c.id: c for c in chunks}
        self.vector_store = vector_store
        self.embedder = embedder
        self.call_graph = CallGraph(chunks)
        self.llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0)
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(AgentState)
        builder.add_node("retrieve", self._retrieve_node)
        builder.add_node("decide", self._decide_node)
        builder.add_node("hop", self._hop_node)
        builder.add_node("generate", self._generate_node)
        builder.add_node("cite", self._cite_node)

        builder.set_entry_point("retrieve")
        builder.add_edge("retrieve", "decide")
        builder.add_conditional_edges(
            "decide",
            self._route_after_decide,
            {"hop": "hop", "generate": "generate"},
        )
        builder.add_edge("hop", "decide")
        builder.add_edge("generate", "cite")
        builder.add_edge("cite", END)

        return builder.compile()

    # embeds raw query text, hits chroma for similar semantic chunks and merges IDs into "visited"
    def _retrieve_node(self, state: AgentState) -> AgentState:
        query_embedding = self.embedder.model.encode(state["query"]).tolist()
        results = self.vector_store.query(query_embedding, n_results=5)
        retrieved_ids = results["ids"][0]

        accumulated = list(state.get("accumulated_chunk_ids", []))
        visited = list(state.get("visited_chunk_ids", []))
        for cid in retrieved_ids:
            if cid not in visited:
                accumulated.append(cid)
                visited.append(cid)

        return {
            **state,
            "accumulated_chunk_ids": accumulated,
            "visited_chunk_ids": visited,
            "hop_count": state.get("hop_count", 0),
        }

    # checks max hop count before llm call as a safeguard    
    def _decide_node(self, state: AgentState) -> AgentState:
        if state.get("hop_count", 0) >= MAX_HOP_COUNT:
            return {**state, "needs_hop": False}

        context = self._format_context_light(state["accumulated_chunk_ids"])
        prompt = (
            "You are deciding whether more context is needed to answer a question about a codebase.\n"
            f"Question: {state['query']}\n\n"
            f"Currently retrieved context:\n{context}\n\n"
            "If the retrieved context fully answers the question, respond with exactly: NO_HOP\n"
            "If tracing callers or callees of the retrieved functions would help answer more completely, "
            "respond with exactly: HOP\n"
            "Respond with only one word."
        )
        decision = self._call_llm(prompt).upper()
        needs_hop = "HOP" in decision and "NO_HOP" not in decision

        return {**state, "needs_hop": needs_hop}

    # decide_node now decides if it needs more context
    def _format_context_light(self,chunk_ids:List[str])->str:
        parts=[]
        for cid in chunk_ids:
            chunk=self.chunks_by_id.get(cid)
            if chunk:
                doc=f" - {chunk.docstring}" if chunk.docstring else ""
                parts.append(f" - {chunk.qualified_name} ({chunk.file_path}:{chunk.start_line}){doc}")
        return "\n".join(parts)

    # actual langgraph conditional edge function
    def _route_after_decide(self, state: AgentState) -> str:
        return "hop" if state.get("needs_hop") else "generate"

    # merges old and new callees and increments hop_count
    def _hop_node(self, state: AgentState) -> AgentState:
        accumulated = list(state["accumulated_chunk_ids"])
        visited = set(state["visited_chunk_ids"])
        new_ids = set()

        for cid in state["accumulated_chunk_ids"]:
            new_ids.update(self.call_graph.get_callees(cid, max_hops=1))
            new_ids.update(self.call_graph.get_callers(cid, max_hops=1))

        for nid in new_ids:
            if nid not in visited and len(accumulated) < MAX_ACCUMULATED_CHUNKS:
                accumulated.append(nid)
                visited.add(nid)

        return {
            **state,
            "accumulated_chunk_ids": accumulated,
            "visited_chunk_ids": list(visited),
            "hop_count": state.get("hop_count", 0) + 1,
        }

    # formats chunks as labeled source blocks
    def _format_context(self, chunk_ids: List[str]) -> str:
        parts = []
        total_chars = 0
        for cid in chunk_ids:
            chunk = self.chunks_by_id.get(cid)
            if not chunk:
                continue
            block = f"### {chunk.qualified_name} ({chunk.file_path}:{chunk.start_line})\n{chunk.source}"
            if total_chars + len(block) > MAX_CONTEXT_CHARS:
                break
            parts.append(block)
            total_chars += len(block)
        return "\n\n".join(parts)

    # accumulated context+ question to LLM which spits out answer 
    def _generate_node(self,state:AgentState) -> AgentState:
        context = self._format_context(state["accumulated_chunk_ids"])
        prompt = (
            "You are a codebase assistant. Answer the question using only the provided code context. "
            "Reference specific functions by name where relevant.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {state['query']}\n\n"
            "Answer:"
        )
        answer = self._call_llm(prompt)
        return {**state, "final_answer": answer}

    # makes llm not hallucinate the line numbers
    def _cite_node(self, state: AgentState) -> AgentState:
        citations = []
        for cid in state["accumulated_chunk_ids"]:
            chunk = self.chunks_by_id.get(cid)
            if chunk:
                citations.append({
                    "qualified_name": chunk.qualified_name,
                    "file_path": chunk.file_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                })
        return {**state, "citations": citations}

    # receives the query
    def query(self, question: str) -> dict:
        initial_state: AgentState = {
            "query": question,
            "accumulated_chunk_ids": [],
            "visited_chunk_ids": [],
            "hop_count": 0,
            "needs_hop": False,
            "final_answer": None,
            "citations": [],
        }
        result = self.graph.invoke(initial_state)
        return {
            "answer": result["final_answer"],
            "citations": result["citations"],
            "hops_used": result["hop_count"],
        }