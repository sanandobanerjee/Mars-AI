"use client";

import { motion, AnimatePresence } from "framer-motion";
import { TraceStep } from "@/lib/types";

const STEPS: TraceStep[] = ["retrieve", "decide", "hop", "generate", "cite"];

interface TracePanelProps {
  activeStep: TraceStep | null;
  hopsUsed: number;
  isRunning: boolean;
}

export default function TracePanel({ activeStep, hopsUsed, isRunning }: TracePanelProps) {
  if (!activeStep) return null;

  return (
    <div className="border border-text/10 bg-panel rounded-lg p-5 mb-6">
      <div className="font-body text-xs text-text/40 tracking-[0.2em] uppercase mb-3">
        Process
      </div>
      <div className="flex flex-wrap gap-x-6 gap-y-2">
        <AnimatePresence>
          {STEPS.map((step, i) => {
            const isActive = activeStep === step;
            const isPast = STEPS.indexOf(step) < STEPS.indexOf(activeStep);
            if (!isActive && !isPast) return null;

            return (
              <motion.div
                key={step}
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: i * 0.08 }}
                className={`font-display text-sm uppercase tracking-wide ${
                  isActive ? "text-mars" : "text-text/40"
                }`}
              >
                {step}
                {step === "hop" && hopsUsed > 0 ? ` ×${hopsUsed}` : ""}
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}