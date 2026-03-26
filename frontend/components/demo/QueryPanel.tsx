"use client";

import { Send } from "lucide-react";

interface QueryPanelProps {
  query: string;
  onQueryChange: (q: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

const EXAMPLE_QUERIES = [
  "Show me revenue trends by region",
  "Analyze employee churn risk by department",
  "What is the optimal pricing for our products?",
  "Forecast demand for the next 90 days",
  "Generate a full report on marketing spend efficiency",
  "Explain key satisfaction drivers",
];

export default function QueryPanel({ query, onQueryChange, onSubmit, isLoading }: QueryPanelProps) {
  return (
    <div className="space-y-4">
      <label className="block text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">Your Question</label>
      <div className="relative">
        <textarea value={query} onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Ask any business question in plain English..."
          rows={3}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); onSubmit(); } }}
          className="w-full px-4 py-3 pr-14 rounded-xl bg-[var(--surface)] border border-[var(--border)] text-[var(--text-primary)] text-sm placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] resize-none" />
        <button onClick={onSubmit} disabled={isLoading || !query.trim()}
          className="absolute right-3 bottom-3 p-2 rounded-lg text-white transition-all duration-200 disabled:opacity-40 hover:scale-105"
          style={{ background: "linear-gradient(135deg, #7c3aed, #6d28d9)" }}>
          {isLoading ? (
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>

      {/* Example chips */}
      <div className="flex flex-wrap gap-2">
        {EXAMPLE_QUERIES.map((eq) => (
          <button key={eq} onClick={() => onQueryChange(eq)}
            className="px-3 py-1.5 rounded-full text-xs bg-[var(--surface)] border border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--accent-light)] hover:text-[var(--accent-light)] transition-all">
            {eq}
          </button>
        ))}
      </div>
    </div>
  );
}
