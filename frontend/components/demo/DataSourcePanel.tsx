"use client";

import { useState, useRef } from "react";
import { Upload, Globe, Database, ChevronDown } from "lucide-react";

interface DataSourcePanelProps {
  dataSource: "csv" | "rest" | "demo";
  onDataSourceChange: (ds: "csv" | "rest" | "demo") => void;
  file: File | null;
  onFileChange: (f: File | null) => void;
  restUrl: string;
  onRestUrlChange: (url: string) => void;
  restHeaders: string;
  onRestHeadersChange: (h: string) => void;
  demoDataset: string;
  onDemoDatasetChange: (d: string) => void;
  agentMode: string;
  onAgentModeChange: (m: string) => void;
  outputOverride: string | null;
  onOutputOverrideChange: (o: string | null) => void;
}

const DEMO_DATASETS = ["Sales", "HR", "Marketing", "Pricing", "Demand", "Employee Satisfaction"];
const AGENT_MODES = [
  { value: "auto", label: "Auto Detect" },
  { value: "general", label: "General Analysis" },
  { value: "pricing", label: "Pricing" },
  { value: "churn", label: "Churn / HR" },
  { value: "forecasting", label: "Forecasting" },
];
const OUTPUT_MODES = [
  { value: null, label: "Auto" },
  { value: "text", label: "Text" },
  { value: "charts", label: "Charts" },
  { value: "report", label: "PDF Report" },
];

export default function DataSourcePanel(props: DataSourcePanelProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const sources = [
    { key: "demo" as const, icon: Database, label: "Demo Dataset" },
    { key: "csv" as const, icon: Upload, label: "Upload CSV" },
    { key: "rest" as const, icon: Globe, label: "REST API" },
  ];

  return (
    <div className="space-y-6">
      {/* Data source tabs */}
      <div>
        <label className="block text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-3">Data Source</label>
        <div className="grid grid-cols-3 gap-2">
          {sources.map((s) => (
            <button key={s.key} onClick={() => props.onDataSourceChange(s.key)}
              className={`flex flex-col items-center gap-2 p-3 rounded-xl border text-sm transition-all duration-200 ${
                props.dataSource === s.key
                  ? "border-[var(--accent)] bg-[rgba(124,58,237,0.1)] text-[var(--accent-light)]"
                  : "border-[var(--border)] bg-[var(--surface)] text-[var(--text-muted)] hover:border-[var(--accent-light)]"
              }`}>
              <s.icon className="w-5 h-5" />
              <span className="text-xs">{s.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Conditional inputs */}
      {props.dataSource === "demo" && (
        <div>
          <label className="block text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-2">Dataset</label>
          <div className="relative">
            <select value={props.demoDataset} onChange={(e) => props.onDemoDatasetChange(e.target.value)}
              className="w-full appearance-none px-4 py-3 rounded-xl bg-[var(--surface)] border border-[var(--border)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[var(--accent)]">
              {DEMO_DATASETS.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)] pointer-events-none" />
          </div>
        </div>
      )}

      {props.dataSource === "csv" && (
        <div>
          <label className="block text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-2">Upload File</label>
          <input ref={fileRef} type="file" accept=".csv,.xlsx,.xls" className="hidden"
            onChange={(e) => props.onFileChange(e.target.files?.[0] || null)} />
          <button onClick={() => fileRef.current?.click()}
            className="w-full p-6 rounded-xl border-2 border-dashed border-[var(--border)] bg-[var(--surface)] hover:border-[var(--accent)] transition-colors text-center">
            <Upload className="w-8 h-8 mx-auto mb-2 text-[var(--text-muted)]" />
            <p className="text-sm text-[var(--text-muted)]">
              {props.file ? props.file.name : "Click to upload CSV or Excel"}
            </p>
          </button>
        </div>
      )}

      {props.dataSource === "rest" && (
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-2">API URL</label>
            <input value={props.restUrl} onChange={(e) => props.onRestUrlChange(e.target.value)}
              placeholder="https://api.example.com/data"
              className="w-full px-4 py-3 rounded-xl bg-[var(--surface)] border border-[var(--border)] text-[var(--text-primary)] text-sm placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)]" />
          </div>
          <div>
            <label className="block text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-2">Headers (JSON)</label>
            <input value={props.restHeaders} onChange={(e) => props.onRestHeadersChange(e.target.value)}
              placeholder='{"Authorization": "Bearer ..."}'
              className="w-full px-4 py-3 rounded-xl bg-[var(--surface)] border border-[var(--border)] text-[var(--text-primary)] text-sm placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)]" />
          </div>
        </div>
      )}

      {/* Agent mode */}
      <div>
        <label className="block text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-2">Agent Mode</label>
        <div className="flex flex-wrap gap-2">
          {AGENT_MODES.map((m) => (
            <button key={m.value} onClick={() => props.onAgentModeChange(m.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                props.agentMode === m.value
                  ? "bg-[var(--accent)] text-white"
                  : "bg-[var(--surface)] border border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--accent-light)]"
              }`}>
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* Output override */}
      <div>
        <label className="block text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-2">Output Format</label>
        <div className="flex flex-wrap gap-2">
          {OUTPUT_MODES.map((m) => (
            <button key={m.label} onClick={() => props.onOutputOverrideChange(m.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                props.outputOverride === m.value
                  ? "bg-[var(--accent)] text-white"
                  : "bg-[var(--surface)] border border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--accent-light)]"
              }`}>
              {m.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
