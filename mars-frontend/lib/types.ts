export interface Citation {
  qualified_name: string;
  file_path: string;
  start_line: number;
  end_line: number;
}

export interface QueryResult {
  answer: string;
  citations: Citation[];
  hops_used: number;
}

export type TraceStep = "retrieve" | "decide" | "hop" | "generate" | "cite" | "done";

export type IngestState = "pending" | "ingesting" | "ready" | "error";

export interface IngestStatusResponse {
  slug: string;
  state: IngestState;
  message: string;
  chunk_count: number;
}