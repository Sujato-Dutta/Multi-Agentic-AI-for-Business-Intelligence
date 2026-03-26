"use client";

import { useState, useCallback } from "react";
import DataSourcePanel from "@/components/demo/DataSourcePanel";
import QueryPanel from "@/components/demo/QueryPanel";
import AgentTrace from "@/components/demo/AgentTrace";
import OutputPanel from "@/components/demo/OutputPanel";
import { runAnalysis } from "@/lib/api";
import type { AgentTraceStep, AnalysisResult } from "@/lib/types";

export default function DemoPage() {
  const [dataSource, setDataSource] = useState<"csv" | "rest" | "demo">("demo");
  const [file, setFile] = useState<File | null>(null);
  const [restUrl, setRestUrl] = useState("");
  const [restHeaders, setRestHeaders] = useState("");
  const [demoDataset, setDemoDataset] = useState("Sales");
  const [agentMode, setAgentMode] = useState("auto");
  const [outputOverride, setOutputOverride] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [traceSteps, setTraceSteps] = useState<AgentTraceStep[]>([]);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = useCallback(async () => {
    if (!query.trim() || isLoading) return;

    setIsLoading(true);
    setTraceSteps([]);
    setResult(null);
    setError(null);

    const currentResult: AnalysisResult = { type: null };

    try {
      const stream = runAnalysis({
        query,
        data_source: dataSource,
        file: dataSource === "csv" ? file || undefined : undefined,
        rest_url: dataSource === "rest" ? restUrl : undefined,
        rest_headers: dataSource === "rest" ? restHeaders || undefined : undefined,
        demo_dataset: dataSource === "demo" ? demoDataset : undefined,
        agent_mode: agentMode as "auto" | "general" | "pricing" | "churn" | "forecasting",
        output_override: outputOverride as "text" | "charts" | "report" | null,
      });

      for await (const event of stream) {
        switch (event.event) {
          case "agent_start":
            setTraceSteps((prev) => [...prev, { agent: event.agent || "Unknown", status: "running" }]);
            break;
          case "agent_done":
            setTraceSteps((prev) =>
              prev.map((s) =>
                s.agent === event.agent && s.status === "running"
                  ? { ...s, status: "done", detail: event.detail }
                  : s
              )
            );
            break;
          case "error":
            setTraceSteps((prev) =>
              prev.map((s) =>
                s.agent === event.agent && s.status === "running"
                  ? { ...s, status: "error", message: event.message }
                  : s
              )
            );
            if (event.agent === "DataIngestion" || event.agent === "AnalysisAgent") {
              setError(event.message || "Analysis failed");
            }
            break;
          case "output_text":
            currentResult.type = "text";
            currentResult.textContent = event.content;
            setResult({ ...currentResult });
            break;
          case "output_charts":
            if (!currentResult.type) currentResult.type = "charts";
            currentResult.charts = event.charts;
            setResult({ ...currentResult });
            break;
          case "output_report":
            currentResult.type = "report";
            currentResult.reportFilename = event.filename;
            currentResult.reportDownloadUrl = event.download_url;
            setResult({ ...currentResult });
            break;
          case "done":
            break;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
    } finally {
      setIsLoading(false);
    }
  }, [query, dataSource, file, restUrl, restHeaders, demoDataset, agentMode, outputOverride, isLoading]);

  return (
    <div className="min-h-screen py-8 px-4 md:px-6">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-[var(--text-primary)] mb-2">
            Interactive <span className="gradient-text">Demo</span>
          </h1>
          <p className="text-[var(--text-muted)]">Connect data, ask a question, watch the agents work.</p>
        </div>

        <div className="grid lg:grid-cols-[380px_1fr] gap-6">
          {/* Left column */}
          <div className="space-y-6">
            <div className="glass-card p-6">
              <DataSourcePanel
                dataSource={dataSource} onDataSourceChange={setDataSource}
                file={file} onFileChange={setFile}
                restUrl={restUrl} onRestUrlChange={setRestUrl}
                restHeaders={restHeaders} onRestHeadersChange={setRestHeaders}
                demoDataset={demoDataset} onDemoDatasetChange={setDemoDataset}
                agentMode={agentMode} onAgentModeChange={setAgentMode}
                outputOverride={outputOverride} onOutputOverrideChange={setOutputOverride}
              />
            </div>
            {traceSteps.length > 0 && (
              <div className="glass-card p-6">
                <AgentTrace steps={traceSteps} />
              </div>
            )}
          </div>

          {/* Right column */}
          <div className="space-y-6">
            <div className="glass-card p-6">
              <QueryPanel query={query} onQueryChange={setQuery} onSubmit={handleSubmit} isLoading={isLoading} />
            </div>
            <div className="glass-card p-6">
              <OutputPanel result={result} isLoading={isLoading} error={error} onRetry={handleSubmit} />
            </div>
          </div>
        </div>

        {/* Watermark */}
        <div className="text-center mt-12">
          <p className="text-sm font-medium text-white" style={{ textShadow: "0 0 15px rgba(255,255,255,0.4)" }}>
            Made by Sujato Dutta
          </p>
        </div>
      </div>
    </div>
  );
}
