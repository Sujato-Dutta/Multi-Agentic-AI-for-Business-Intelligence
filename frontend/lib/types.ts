export interface AnalysisRequest {
  query: string;
  data_source: "csv" | "rest" | "demo";
  file?: File;
  rest_url?: string;
  rest_headers?: string;
  rest_params?: string;
  demo_dataset?: string;
  agent_mode: "auto" | "general" | "pricing" | "churn" | "forecasting";
  output_override?: "text" | "charts" | "report" | null;
}

export interface ChartData {
  title: string;
  image: string;
  caption?: string;
}

export interface SSEEvent {
  event: "agent_start" | "agent_done" | "output_text" | "output_charts" | "output_report" | "error" | "done";
  agent?: string;
  detail?: string;
  content?: string;
  charts?: ChartData[];
  filename?: string;
  download_url?: string;
  message?: string;
}

export interface AgentTraceStep {
  agent: string;
  status: "running" | "done" | "error";
  detail?: string;
  message?: string;
}

export interface AnalysisResult {
  type: "text" | "charts" | "report" | null;
  textContent?: string;
  charts?: ChartData[];
  reportFilename?: string;
  reportDownloadUrl?: string;
}
