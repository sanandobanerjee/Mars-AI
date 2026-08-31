"use client";

import { useState, useEffect, useRef } from "react";
import { fetchRepos, runQuery, startIngest, getIngestStatus } from "@/lib/api";
import { QueryResult, TraceStep, IngestState } from "@/lib/types";
import TracePanel from "@/components/TracePanel";
import AnswerPanel from "@/components/AnswerPanel";

export default function Home() {
  const [repos, setRepos] = useState<string[]>([]);
  const [repo, setRepo] = useState("");
  const [question, setQuestion] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [activeStep, setActiveStep] = useState<TraceStep | null>(null);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [repoUrl, setRepoUrl] = useState("");
  const [ingestState, setIngestState] = useState<IngestState | null>(null);
  const [ingestError, setIngestError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadRepos = () => {
    fetchRepos()
      .then((r) => {
        setRepos(r);
        if (r.length > 0 && !repo) setRepo(r[0]);
      })
      .catch(() => setError("Could not reach Mars API"));
  };

  useEffect(() => {
    loadRepos();
  }, []);

  const handleAddRepo = async () => {
    if (!repoUrl.trim()) return;
    setIngestError(null);
    setIngestState("ingesting");

    try {
      const { slug } = await startIngest(repoUrl.trim());

      pollRef.current = setInterval(async () => {
        const status = await getIngestStatus(slug);
        setIngestState(status.state);

        if (status.state === "ready") {
          if (pollRef.current) clearInterval(pollRef.current);
          loadRepos();
          setRepo(slug);
          setRepoUrl("");
        } else if (status.state === "error") {
          if (pollRef.current) clearInterval(pollRef.current);
          setIngestError(status.message);
        }
      }, 3000);
    } catch (e) {
      setIngestState(null);
      setIngestError(e instanceof Error ? e.message : "Failed to start ingestion");
    }
  };

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const handleSubmit = async () => {
    if (!repo || !question.trim()) return;
    setIsRunning(true);
    setError(null);
    setResult(null);
    setActiveStep("retrieve");

    const fakeProgress: TraceStep[] = ["retrieve", "decide", "generate", "cite"];
    let stepIndex = 0;
    const interval = setInterval(() => {
      stepIndex = Math.min(stepIndex + 1, fakeProgress.length - 1);
      setActiveStep(fakeProgress[stepIndex]);
    }, 1200);

    try {
      const res = await runQuery(repo, question);
      clearInterval(interval);
      setActiveStep("done");
      setResult(res);
    } catch (e) {
      clearInterval(interval);
      setError(e instanceof Error ? e.message : "Query failed");
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <main className="min-h-screen p-6 md:p-10 max-w-5xl mx-auto">
      <header className="mb-8">
        <div className="font-mono text-xs text-signal tracking-widest uppercase mb-1">
          Mars
        </div>
        <h1 className="font-display text-2xl md:text-3xl text-text">
          Multi-hop Agent Retrieval and Scoring
        </h1>
      </header>

      <div className="grid md:grid-cols-[280px_1fr] gap-6">
        <div className="space-y-4">
          <div className="border border-text-dim/20 rounded-lg p-4 bg-surface">
            <label className="block text-xs font-mono text-text-dim uppercase mb-2">
              Add a GitHub repo
            </label>
            <input
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/owner/repo"
              className="w-full bg-bg border border-text-dim/20 rounded px-3 py-2 text-text text-sm mb-2"
            />
            <button
              onClick={handleAddRepo}
              disabled={ingestState === "ingesting" || !repoUrl.trim()}
              className="w-full border border-signal text-signal rounded px-3 py-2 text-sm disabled:opacity-40"
            >
              {ingestState === "ingesting" ? "Ingesting..." : "Ingest repo"}
            </button>
            {ingestError && (
              <div className="text-rust text-xs mt-2 font-mono">{ingestError}</div>
            )}
          </div>

          <div>
            <label className="block text-xs font-mono text-text-dim uppercase mb-2">
              Repository
            </label>
            <select
              value={repo}
              onChange={(e) => setRepo(e.target.value)}
              className="w-full bg-surface border border-text-dim/20 rounded px-3 py-2 text-text font-mono text-sm"
            >
              {repos.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-mono text-text-dim uppercase mb-2">
              Question
            </label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={4}
              placeholder="How does this function work?"
              className="w-full bg-surface border border-text-dim/20 rounded px-3 py-2 text-text text-sm resize-none"
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={isRunning || !repo || !question.trim()}
            className="w-full bg-rust text-bg font-medium rounded px-4 py-2.5 disabled:opacity-40 transition-opacity"
          >
            {isRunning ? "Running..." : "Run query"}
          </button>
        </div>

        <div className="space-y-4">
          <TracePanel activeStep={activeStep} hopsUsed={result?.hops_used ?? 0} isRunning={isRunning} />
          {error && (
            <div className="border border-rust/40 bg-rust/10 text-rust rounded-lg p-4 text-sm font-mono">
              {error}
            </div>
          )}
          {result && <AnswerPanel result={result} />}
        </div>
      </div>
    </main>
  );
}