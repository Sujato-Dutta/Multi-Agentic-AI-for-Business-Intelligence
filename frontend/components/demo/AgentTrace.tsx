"use client";

import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import type { AgentTraceStep } from "@/lib/types";

interface AgentTraceProps {
  steps: AgentTraceStep[];
}

export default function AgentTrace({ steps }: AgentTraceProps) {
  if (steps.length === 0) return null;

  return (
    <div className="space-y-1">
      <label className="block text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-3">Agent Pipeline</label>
      <div className="relative pl-6">
        {/* Vertical line */}
        <div className="absolute left-[11px] top-2 bottom-2 w-px bg-[var(--border)]" />

        {steps.map((step, i) => (
          <div key={`${step.agent}-${i}`} className="relative flex items-start gap-3 pb-4 last:pb-0 animate-fade-in-up">
            {/* Status icon */}
            <div className="relative z-10 flex-shrink-0 -ml-6">
              {step.status === "running" && (
                <div className="w-6 h-6 rounded-full bg-[var(--surface)] border border-[var(--accent)] flex items-center justify-center animate-pulse-glow">
                  <Loader2 className="w-3.5 h-3.5 text-[var(--accent-light)] animate-spin" />
                </div>
              )}
              {step.status === "done" && (
                <div className="w-6 h-6 rounded-full bg-[rgba(34,197,94,0.15)] flex items-center justify-center">
                  <CheckCircle2 className="w-4 h-4 text-[var(--success)]" />
                </div>
              )}
              {step.status === "error" && (
                <div className="w-6 h-6 rounded-full bg-[rgba(239,68,68,0.15)] flex items-center justify-center">
                  <XCircle className="w-4 h-4 text-[var(--error)]" />
                </div>
              )}
            </div>

            {/* Content */}
            <div className="min-w-0 flex-1">
              <div className="text-sm font-medium text-[var(--text-primary)]">{step.agent}</div>
              {step.detail && <div className="text-xs text-[var(--text-muted)] mt-0.5">{step.detail}</div>}
              {step.message && <div className="text-xs text-[var(--error)] mt-0.5">{step.message}</div>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
