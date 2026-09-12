"use client";

import { useState, useEffect, useRef } from "react";
import { fetchRepos, runQuery, startIngest, getIngestStatus } from "@/lib/api";
import { QueryResult, TraceStep, IngestState } from "@/lib/types";
import Header from "@/components/Header";
import StatusBadge from "@/components/StatusBadge";
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

    const cleaned = repoUrl
      .trim()
      .replace(/^https?:\/\/(www\.)?github\.com\//i, "")
      .replace(/\/$/, "");
    const fullUrl = `https://github.com/${cleaned}`;

    try {
      const { slug } = await startIngest(fullUrl);

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
      setActiveStep("cite");
      setResult(res);
    } catch (e) {
      clearInterval(interval);
      setError(e instanceof Error ? e.message : "Query failed");
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <main className="min-h-screen px-6 md:px-16 py-12 max-w-6xl mx-auto">
      <Header readyCount={repos.length} />

      <div className="grid md:grid-cols-[1fr_1.4fr] gap-6">
        <div>
          <div className="font-display text-xl font-semibold mb-6 text-mars">Query</div>

          <div className="mb-8">
            <div className="font-body text-xs text-text/40 tracking-[0.2em] uppercase mb-2">
              Add target
            </div>
            <div className="flex items-stretch border border-text/10 rounded overflow-hidden focus-within:border-mars transition-colors">
              <span className="bg-panel px-3 py-2 text-text/40 text-sm font-body flex items-center border-r border-text/10">
                github.com/
              </span>
              <input
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="owner/repo"
                className="flex-1 bg-void px-3 py-2 text-text placeholder:text-text/30 focus:outline-none text-sm"
              />
            </div>
            <div className="flex items-center justify-between mt-2">
              <button
                onClick={handleAddRepo}
                disabled={ingestState === "ingesting" || !repoUrl.trim()}
                className="font-body text-sm text-mars disabled:text-text/30 hover:text-mars-bright transition-colors"
              >
                Ingest →
              </button>
              {ingestState && <StatusBadge status={ingestState} />}
            </div>
            {ingestError && (
              <div className="text-mars-bright text-xs mt-2 font-body">{ingestError}</div>
            )}
          </div>

          <div className="mb-6">
            <div className="font-body text-xs text-text/40 tracking-[0.2em] uppercase mb-2">
              Repository
            </div>
            <select
              value={repo}
              onChange={(e) => setRepo(e.target.value)}
              className="w-full bg-void border border-text/10 rounded px-3 py-2 text-text focus:outline-none focus:border-mars transition-colors text-sm"
            >
              {repos.map((r) => (
                <option key={r} value={r} className="bg-panel">
                  {r}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-6">
            <div className="font-body text-xs text-text/40 tracking-[0.2em] uppercase mb-2">
              Question
            </div>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={4}
              placeholder="How does this function work?"
              className="w-full bg-void border border-text/10 rounded px-3 py-2 text-text placeholder:text-text/30 resize-none focus:outline-none focus:border-mars transition-colors text-sm"
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={isRunning || !repo || !question.trim()}
            className="w-full bg-mars hover:bg-mars-bright text-text font-display font-semibold rounded px-4 py-2.5 disabled:opacity-30 transition-colors"
          >
            {isRunning ? "Running…" : "Run →"}
          </button>
        </div>

        <div>
          <TracePanel activeStep={activeStep} hopsUsed={result?.hops_used ?? 0} isRunning={isRunning} />
          {error && (
            <div className="border border-mars-bright/40 bg-mars-bright/10 text-mars-bright rounded-lg p-4 text-sm font-body">
              {error}
            </div>
          )}
          {result && <AnswerPanel result={result} />}
        </div>
      </div>
    </main>
  );
}