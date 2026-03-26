const AGENTS_TABLE = [
  { agent: "Orchestrator", model: "kimi-k2-instruct", trigger: "Every query", purpose: "Route to specialist via intent detection" },
  { agent: "Data Ingestion", model: "— (no LLM)", trigger: "Every query", purpose: "Load CSV/Excel, REST API (JSON/XML/CSV), or demo datasets + auto-clean" },
  { agent: "Column Mapper", model: "— (no LLM)", trigger: "Non-general queries", purpose: "Fuzzy-match user columns to specialist schemas; fallback if unmatched" },
  { agent: "General Analysis", model: "llama-3.1-8b", trigger: "Default / unmatched queries", purpose: "Stats, correlations, anomalies" },
  { agent: "Dynamic Pricing", model: "qwen3-32b", trigger: "price, margin, discount, elasticity", purpose: "Elasticity, margins, discount simulation" },
  { agent: "Employee Churn", model: "gpt-oss-120b", trigger: "churn, attrition, retention, HR", purpose: "Churn rates, risk flags, retention cost" },
  { agent: "Demand Forecasting", model: "qwen3-32b", trigger: "forecast, demand, predict, trend", purpose: "Trend decomposition, polyfit forecasts, stockout risk" },
  { agent: "Hallucination Guard", model: "— (no LLM)", trigger: "Every specialist output", purpose: "Cross-reference LLM numbers vs computed data" },
  { agent: "Output", model: "— (no LLM)", trigger: "Every query (final step)", purpose: "Text / Charts / PDF report generation" },
];

const EXAMPLE_QUERIES = [
  { query: "Summarize sales trends by region", agent: "General Analysis", output: "Text" },
  { query: "What is the optimal pricing for maximum revenue?", agent: "Dynamic Pricing", output: "Report" },
  { query: "Show churn risk by department", agent: "Employee Churn", output: "Charts" },
  { query: "Forecast demand for the next 90 days", agent: "Demand Forecasting", output: "Report" },
  { query: "Visualize marketing spend vs conversions", agent: "General Analysis", output: "Charts" },
  { query: "Generate a full report on employee satisfaction", agent: "Employee Churn", output: "Report" },
];

export default function DocsPage() {
  return (
    <div className="min-h-screen py-12 px-4 md:px-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-[var(--text-primary)] mb-2">
          <span className="gradient-text">Documentation</span>
        </h1>
        <p className="text-[var(--text-muted)] mb-12">Everything you need to understand and use the platform.</p>

        {/* Overview */}
        <Section title="Overview">
          <p>
            Multi-Agentic AI for Business Intelligence is a free, open-source platform that uses multiple specialized AI agents
            to analyze your data. Connect a data source, ask a question in natural language, and the system automatically
            routes your query to the best specialist agent — delivering insights, charts, or a full PDF report.
          </p>
          <p className="mt-2">
            <strong>Key design principle:</strong> All calculations are done deterministically by pandas/numpy/scipy.
            The LLM never does math — it only narrates pre-computed results. A hallucination guard then cross-references
            every number in the LLM output against the actual computed data, flagging any ungrounded claims.
          </p>
        </Section>

        {/* Data Sources */}
        <Section title="Data Sources">
          <p className="mb-3">The platform accepts data from three sources, with automatic format detection and cleaning:</p>
          <ul className="list-disc list-inside space-y-2">
            <li><strong>CSV/Excel Upload</strong> — .csv, .xlsx, .xls, or .tsv files</li>
            <li><strong>REST API</strong> — Connects to any HTTP endpoint. Supports:
              <ul className="list-disc list-inside ml-6 mt-1 space-y-1 text-[var(--text-muted)]">
                <li>JSON arrays &amp; nested objects (unwraps <code className="text-[var(--accent-light)]">data</code>, <code className="text-[var(--accent-light)]">results</code>, <code className="text-[var(--accent-light)]">items</code>, etc.)</li>
                <li>XML responses (auto-detects repeating row elements)</li>
                <li>CSV/TSV text responses</li>
                <li>Nested JSON flattening (e.g. <code className="text-[var(--accent-light)]">user.name</code> → <code className="text-[var(--accent-light)]">user_name</code>)</li>
              </ul>
            </li>
            <li><strong>Demo Datasets</strong> — 6 built-in: Sales, HR, Marketing, Pricing, Demand, Employee Satisfaction</li>
          </ul>
          <div className="glass-card p-4 mt-4">
            <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-2">Auto-Cleaning</h4>
            <p className="text-xs text-[var(--text-muted)]">
              All ingested data is automatically cleaned: whitespace stripped from headers, empty rows/columns dropped,
              string columns coerced to numeric when &gt;70% parseable, and a data quality report is generated
              (warns about high null ratios, duplicates, zero-variance columns).
            </p>
          </div>
        </Section>

        {/* Column Mapping */}
        <Section title="Smart Column Mapping">
          <p className="mb-3">
            When you upload custom data, column names may not match what specialist agents expect.
            The Column Mapper uses fuzzy synonym matching to bridge this gap:
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  <th className="text-left py-2 px-3 text-[var(--text-muted)] font-medium">Your Column</th>
                  <th className="text-left py-2 px-3 text-[var(--text-muted)] font-medium">→ Mapped To</th>
                  <th className="text-left py-2 px-3 text-[var(--text-muted)] font-medium">Agent</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { from: "unit_price, selling_price, mrp, rate", to: "price", agent: "Pricing" },
                  { from: "qty_sold, volume, quantity", to: "units_sold", agent: "Pricing" },
                  { from: "dept, division, team", to: "department", agent: "Churn" },
                  { from: "satisfaction, happiness, engagement", to: "satisfaction_score", agent: "Churn" },
                  { from: "timestamp, day, order_date", to: "date", agent: "Forecasting" },
                  { from: "orders, consumption, qty", to: "demand", agent: "Forecasting" },
                ].map((r) => (
                  <tr key={r.to} className="border-b border-[var(--border)]">
                    <td className="py-2 px-3 text-[var(--text-muted)]"><code className="text-xs">{r.from}</code></td>
                    <td className="py-2 px-3 text-[var(--accent-light)] font-medium">{r.to}</td>
                    <td className="py-2 px-3 text-[var(--text-muted)]">{r.agent}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-[var(--text-muted)] mt-3">
            If required columns can&apos;t be matched, the system automatically falls back to General Analysis — which works with any numeric data.
          </p>
        </Section>

        {/* Agents */}
        <Section title="Agent Architecture">
          <p className="mb-4">Each agent is purpose-built for a domain. Agents marked &quot;no LLM&quot; are pure computation — zero API calls:</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  <th className="text-left py-3 px-3 text-[var(--text-muted)] font-medium">Agent</th>
                  <th className="text-left py-3 px-3 text-[var(--text-muted)] font-medium">Model</th>
                  <th className="text-left py-3 px-3 text-[var(--text-muted)] font-medium">Trigger</th>
                  <th className="text-left py-3 px-3 text-[var(--text-muted)] font-medium">Purpose</th>
                </tr>
              </thead>
              <tbody>
                {AGENTS_TABLE.map((a) => (
                  <tr key={a.agent} className="border-b border-[var(--border)] hover:bg-[rgba(124,58,237,0.05)]">
                    <td className="py-3 px-3 text-[var(--text-primary)] font-medium">{a.agent}</td>
                    <td className="py-3 px-3"><code className="text-xs px-2 py-0.5 rounded bg-[var(--surface)] text-[var(--accent-light)]">{a.model}</code></td>
                    <td className="py-3 px-3 text-[var(--text-muted)]">{a.trigger}</td>
                    <td className="py-3 px-3 text-[var(--text-muted)]">{a.purpose}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        {/* Hallucination Prevention */}
        <Section title="Hallucination Prevention">
          <p className="mb-3">The system uses a multi-layered approach to ensure output accuracy:</p>
          <div className="space-y-3">
            <div className="glass-card p-4">
              <h4 className="text-sm font-semibold text-[var(--accent-light)] mb-1">Layer 1: Deterministic Calculations</h4>
              <p className="text-xs text-[var(--text-muted)]">
                All statistics (means, correlations, elasticity, churn rates, forecasts) are computed by pandas/numpy/scipy.
                The LLM never does math — it only receives pre-computed numbers in its prompt and generates natural language summaries.
              </p>
            </div>
            <div className="glass-card p-4">
              <h4 className="text-sm font-semibold text-[var(--accent-light)] mb-1">Layer 2: Grounded Prompts</h4>
              <p className="text-xs text-[var(--text-muted)]">
                Every prompt includes the actual computed data. The LLM is instructed to generate bullet points only — no reasoning,
                no chain-of-thought. Models that output thinking blocks (Qwen3, DeepSeek) have them auto-stripped.
              </p>
            </div>
            <div className="glass-card p-4">
              <h4 className="text-sm font-semibold text-[var(--accent-light)] mb-1">Layer 3: Hallucination Guard</h4>
              <p className="text-xs text-[var(--text-muted)]">
                After insights are generated, every number in the LLM output is extracted and cross-referenced against
                the computed analysis data (with 10% tolerance). If more than half the numbers in an insight are ungrounded,
                it gets flagged with a disclaimer: &quot;[Note: Some figures are approximations]&quot;.
                A grounding score (0.0–1.0) is logged for monitoring.
              </p>
            </div>
            <div className="glass-card p-4">
              <h4 className="text-sm font-semibold text-[var(--accent-light)] mb-1">Layer 4: Output Validation</h4>
              <p className="text-xs text-[var(--text-muted)]">
                Agent outputs are structurally validated (non-empty insights + analysis dict).
                If validation fails, the specialist is retried once, then falls back to General Analysis.
              </p>
            </div>
          </div>
        </Section>

        {/* Example Queries */}
        <Section title="Example Queries">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  <th className="text-left py-3 px-3 text-[var(--text-muted)] font-medium">Query</th>
                  <th className="text-left py-3 px-3 text-[var(--text-muted)] font-medium">Agent</th>
                  <th className="text-left py-3 px-3 text-[var(--text-muted)] font-medium">Output</th>
                </tr>
              </thead>
              <tbody>
                {EXAMPLE_QUERIES.map((q) => (
                  <tr key={q.query} className="border-b border-[var(--border)] hover:bg-[rgba(124,58,237,0.05)]">
                    <td className="py-3 px-3 text-[var(--text-primary)]">{q.query}</td>
                    <td className="py-3 px-3 text-[var(--accent-light)]">{q.agent}</td>
                    <td className="py-3 px-3 text-[var(--text-muted)]">{q.output}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        {/* Logging */}
        <Section title="Logging & Monitoring">
          <p className="mb-3">
            Every agent event is logged to a Supabase PostgreSQL database with structured metadata:
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  <th className="text-left py-2 px-3 text-[var(--text-muted)] font-medium">Field</th>
                  <th className="text-left py-2 px-3 text-[var(--text-muted)] font-medium">Description</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { field: "session_id", desc: "Unique ID per request for full pipeline traceability" },
                  { field: "agent", desc: "Which agent generated the log (Orchestrator, Pricing, etc.)" },
                  { field: "event", desc: "Event type (request, agent_start, agent_done, error, complete)" },
                  { field: "grounding_score", desc: "0.0–1.0 how well LLM insights matched computed data" },
                  { field: "duration_ms", desc: "Total pipeline execution time" },
                  { field: "detail", desc: "JSONB metadata (column mappings, data quality warnings, etc.)" },
                ].map((r) => (
                  <tr key={r.field} className="border-b border-[var(--border)]">
                    <td className="py-2 px-3"><code className="text-xs text-[var(--accent-light)]">{r.field}</code></td>
                    <td className="py-2 px-3 text-[var(--text-muted)]">{r.desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-[var(--text-muted)] mt-3">
            Logging is optional — if SUPABASE_URL/SUPABASE_KEY are not set, logs go to console only.
          </p>
        </Section>

        {/* API Reference */}
        <Section title="API Reference">
          <div className="space-y-4">
            <ApiEndpoint method="GET" path="/health" desc="Returns server status and timestamp." />
            <ApiEndpoint method="GET" path="/demo-datasets" desc="Returns list of available demo dataset names." />
            <ApiEndpoint method="POST" path="/analyze" desc="Main analysis endpoint. Accepts multipart/form-data with query, data_source, file, rest_url, rest_headers, demo_dataset, agent_mode, output_override. Returns SSE stream with agent events." />
            <ApiEndpoint method="GET" path="/download/{filename}" desc="Download a generated PDF report." />
          </div>
        </Section>

        {/* Self-hosting */}
        <Section title="Self-Hosting Guide">
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-3">Backend</h3>
          <Pre>{`cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env      # Add GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY
uvicorn main:app --reload --port 8000`}</Pre>

          <h3 className="text-lg font-semibold text-[var(--text-primary)] mt-6 mb-3">Frontend</h3>
          <Pre>{`cd frontend
npm install
cp .env.example .env.local  # Set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev`}</Pre>

          <h3 className="text-lg font-semibold text-[var(--text-primary)] mt-6 mb-3">Supabase Logging (Optional)</h3>
          <Pre>{`-- Run in Supabase SQL Editor:
CREATE TABLE agent_logs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    session_id TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'INFO',
    agent TEXT, event TEXT, message TEXT,
    detail JSONB, query TEXT, data_source TEXT,
    grounding_score REAL, duration_ms INTEGER, error TEXT
);
CREATE INDEX idx_agent_logs_session ON agent_logs(session_id);
CREATE INDEX idx_agent_logs_created ON agent_logs(created_at DESC);
ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow insert" ON agent_logs FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow read" ON agent_logs FOR SELECT USING (true);`}</Pre>

          <h3 className="text-lg font-semibold text-[var(--text-primary)] mt-6 mb-3">Deployment</h3>
          <ul className="list-disc list-inside space-y-1">
            <li><strong>Backend → Render</strong>: Root = <code className="text-[var(--accent-light)]">backend/</code>, add GROQ_API_KEY + SUPABASE_URL + SUPABASE_KEY env vars</li>
            <li><strong>Frontend → Vercel</strong>: Root = <code className="text-[var(--accent-light)]">frontend/</code>, add NEXT_PUBLIC_API_URL env var</li>
          </ul>
        </Section>

        {/* Watermark */}
        <div className="text-center mt-16 pb-8">
          <p className="text-sm font-medium text-white" style={{ textShadow: "0 0 15px rgba(255,255,255,0.4)" }}>
            Made by Sujato Dutta
          </p>
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-12">
      <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-4">{title}</h2>
      <div className="text-sm text-[var(--text-secondary)] leading-relaxed space-y-3">{children}</div>
    </section>
  );
}

function ApiEndpoint({ method, path, desc }: { method: string; path: string; desc: string }) {
  return (
    <div className="glass-card p-4 flex items-start gap-3">
      <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${method === "GET" ? "bg-emerald-900/40 text-emerald-400" : "bg-blue-900/40 text-blue-400"}`}>
        {method}
      </span>
      <div>
        <code className="text-sm text-[var(--accent-light)]">{path}</code>
        <p className="text-xs text-[var(--text-muted)] mt-1">{desc}</p>
      </div>
    </div>
  );
}

function Pre({ children }: { children: string }) {
  return (
    <pre className="p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)] text-sm text-[var(--text-secondary)] overflow-x-auto font-mono">
      {children}
    </pre>
  );
}
