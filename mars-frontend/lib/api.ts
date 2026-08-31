import { QueryResult,IngestState,IngestStatusResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchRepos(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/repos`);
  if (!res.ok) throw new Error("Failed to fetch repos");
  const data = await res.json();
  return data.repos;
}

export async function runQuery(repo: string, question: string): Promise<QueryResult> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo, question }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Query failed");
  }
  return res.json();
}

export async function startIngest(repoUrl: string): Promise<{ slug: string; state: IngestState }> {
  const res = await fetch(`${API_BASE}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: repoUrl }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Ingest failed to start");
  }
  return res.json();
}

export async function getIngestStatus(slug: string): Promise<IngestStatusResponse> {
  const res = await fetch(`${API_BASE}/ingest/status/${slug}`);
  if (!res.ok) throw new Error("Could not fetch ingest status");
  return res.json();
}