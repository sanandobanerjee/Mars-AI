"use client";

export default function Header({ readyCount }: { readyCount: number }) {
  return (
    <header className="mb-12">
      <div className="font-body text-xs text-text/50 tracking-[0.3em] uppercase mb-3">
        Codebase Exploration
      </div>
      <h1 className="font-display font-semibold text-5xl md:text-7xl leading-none mb-4 text-mars">
        MARS
      </h1>
      <div className="flex items-baseline gap-3 font-body text-sm text-text/60">
        <span>Multi-hop Agent Retrieval and Scoring</span>
        <span className="text-mars">·</span>
        <span>{readyCount} target{readyCount !== 1 ? "s" : ""} indexed</span>
      </div>
    </header>
  );
}