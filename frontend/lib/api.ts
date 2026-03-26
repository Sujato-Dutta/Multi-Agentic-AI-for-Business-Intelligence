import type { AnalysisRequest, SSEEvent } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getDemoDatasets(): Promise<string[]> {
  const res = await fetch(`${API_URL}/demo-datasets`);
  if (!res.ok) throw new Error("Failed to fetch demo datasets");
  const data = await res.json();
  return data.datasets;
}

export async function* runAnalysis(params: AnalysisRequest): AsyncGenerator<SSEEvent> {
  const formData = new FormData();
  formData.append("query", params.query);
  formData.append("data_source", params.data_source);
  formData.append("agent_mode", params.agent_mode);

  if (params.output_override) formData.append("output_override", params.output_override);
  if (params.file) formData.append("file", params.file);
  if (params.rest_url) formData.append("rest_url", params.rest_url);
  if (params.rest_headers) formData.append("rest_headers", params.rest_headers);
  if (params.rest_params) formData.append("rest_params", params.rest_params);
  if (params.demo_dataset) formData.append("demo_dataset", params.demo_dataset);

  const res = await fetch(`${API_URL}/analyze`, { method: "POST", body: formData });
  if (!res.ok) throw new Error(`Analysis failed: ${res.statusText}`);

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith("data: ")) {
        try {
          yield JSON.parse(trimmed.slice(6)) as SSEEvent;
        } catch { /* skip malformed */ }
      }
    }
  }
}

export function getDownloadUrl(filename: string): string {
  return `${API_URL}/download/${filename}`;
}

export async function downloadReport(filename: string): Promise<Blob> {
  const res = await fetch(getDownloadUrl(filename));
  if (!res.ok) throw new Error("Download failed");
  return res.blob();
}
