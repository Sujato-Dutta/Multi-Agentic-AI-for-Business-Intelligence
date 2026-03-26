"use client";

import { Copy, Check, Download, FileText, AlertTriangle } from "lucide-react";
import { useState } from "react";
import type { AnalysisResult, ChartData } from "@/lib/types";
import { getDownloadUrl } from "@/lib/api";

interface OutputPanelProps {
  result: AnalysisResult | null;
  isLoading: boolean;
  error: string | null;
  onRetry: () => void;
}

export default function OutputPanel({ result, isLoading, error, onRetry }: OutputPanelProps) {
  const [copied, setCopied] = useState(false);

  if (error) {
    return (
      <div className="glass-card p-6 border-[var(--error)] border">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-[var(--error)] flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-[var(--error)] mb-1">Analysis Error</h3>
            <p className="text-sm text-[var(--text-muted)] mb-4">{error}</p>
            <button onClick={onRetry}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-[var(--error)] text-white hover:opacity-90 transition-opacity">
              Retry Analysis
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-6 w-48" />
        <div className="skeleton h-4 w-full" />
        <div className="skeleton h-4 w-3/4" />
        <div className="skeleton h-40 w-full" />
        <div className="skeleton h-4 w-1/2" />
      </div>
    );
  }

  if (!result || !result.type) {
    return (
      <div className="text-center py-16">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[var(--surface)] border border-[var(--border)] flex items-center justify-center">
          <FileText className="w-8 h-8 text-[var(--text-muted)]" />
        </div>
        <p className="text-sm text-[var(--text-muted)]">Results will appear here after analysis</p>
      </div>
    );
  }

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Text output */}
      {result.textContent && (
        <div className="glass-card p-6 relative">
          <button onClick={() => handleCopy(result.textContent || "")}
            className="absolute top-4 right-4 p-2 rounded-lg bg-[var(--surface)] border border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--accent-light)] transition-colors">
            {copied ? <Check className="w-4 h-4 text-[var(--success)]" /> : <Copy className="w-4 h-4" />}
          </button>
          <div className="prose prose-invert prose-sm max-w-none text-[var(--text-secondary)]"
            dangerouslySetInnerHTML={{ __html: markdownToHtml(result.textContent) }} />
        </div>
      )}

      {/* Charts */}
      {result.charts && result.charts.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-[var(--text-muted)] uppercase tracking-wider mb-3">Visualizations</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {result.charts.map((chart: ChartData, i: number) => (
              <div key={i} className="glass-card p-4 glow-border-hover transition-all duration-300">
                <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-3">{chart.title}</h4>
                <img src={`data:image/png;base64,${chart.image}`} alt={chart.title}
                  className="w-full rounded-lg" />
                {chart.caption && <p className="text-xs text-[var(--text-muted)] mt-2">{chart.caption}</p>}
                <button onClick={() => downloadChart(chart)}
                  className="mt-2 flex items-center gap-1.5 text-xs text-[var(--accent-light)] hover:underline">
                  <Download className="w-3 h-3" /> Download
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Report download */}
      {result.reportFilename && (
        <div className="glass-card p-6 glow-border">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl flex items-center justify-center"
              style={{ background: "linear-gradient(135deg, rgba(124,58,237,0.2), rgba(99,102,241,0.2))" }}>
              <FileText className="w-7 h-7 text-[var(--accent-light)]" />
            </div>
            <div className="flex-1">
              <h3 className="text-base font-semibold text-[var(--text-primary)]">PDF Report Generated</h3>
              <p className="text-sm text-[var(--text-muted)]">{result.reportFilename}</p>
            </div>
            <a href={getDownloadUrl(result.reportFilename)} download
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium text-white transition-all hover:scale-105"
              style={{ background: "linear-gradient(135deg, #7c3aed, #6d28d9)" }}>
              <Download className="w-4 h-4" /> Download PDF
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

function downloadChart(chart: ChartData) {
  const link = document.createElement("a");
  link.href = `data:image/png;base64,${chart.image}`;
  link.download = `${chart.title.replace(/\s+/g, "_")}.png`;
  link.click();
}

function markdownToHtml(md: string): string {
  return md
    .replace(/^### (.*$)/gm, '<h3 class="text-lg font-semibold text-[var(--text-primary)] mt-4 mb-2">$1</h3>')
    .replace(/^## (.*$)/gm, '<h2 class="text-xl font-bold text-[var(--text-primary)] mt-4 mb-2">$1</h2>')
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/^- (.*$)/gm, '<li class="ml-4 list-disc">$1</li>')
    .replace(/\n/g, "<br />");
}
