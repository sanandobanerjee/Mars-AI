"use client";

import { TraceStep } from "@/lib/types";

const STEPS: TraceStep[] = ["retrieve", "decide", "hop", "generate", "cite"];

interface TracePanelProps {
  activeStep: TraceStep | null;
  hopsUsed: number;
  isRunning: boolean;
}

export default function TracePanel({ activeStep, hopsUsed, isRunning }: TracePanelProps) {
  return (
    <div className="border border-text-dim/20 bg-surface rounded-lg p-4 font-mono text-sm">
      <div className="text-text-dim mb-3 tracking-wide text-xs uppercase">
        Agent Trace
      </div>
      <div className="flex flex-wrap gap-2">
        {STEPS.map((step) => {
          const isActive = activeStep === step;
          const isPast =
            activeStep !== null && STEPS.indexOf(step) < STEPS.indexOf(activeStep);
          return (
            <div
              key={step}
              className={`px-3 py-1.5 rounded border transition-colors duration-300 ${
                isActive
                  ? "border-signal text-signal bg-signal/10"
                  : isPast
                  ? "border-text-dim/40 text-text-dim"
                  : "border-text-dim/15 text-text-dim/50"
              }`}
            >
              {step}
              {step === "hop" && hopsUsed > 0 ? ` ×${hopsUsed}` : ""}
            </div>
          );
        })}
      </div>
      {isRunning && (
        <div className="mt-3 text-signal text-xs animate-pulse">
          processing...
        </div>
      )}
    </div>
  );
}