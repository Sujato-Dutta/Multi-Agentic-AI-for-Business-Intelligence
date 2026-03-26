"use client";

const agents = [
  { name: "Orchestrator Agent", model: "kimi-k2-instruct", role: "Routes queries to the best specialist via LLM intent detection", color: "#a78bfa" },
  { name: "Analysis Agent", model: "llama-3.1-8b", role: "Summary stats, correlations, trends, anomaly flagging", color: "#6366f1" },
  { name: "Dynamic Pricing Agent", model: "qwen3-32b", role: "Price elasticity, margins, competitor gaps, discount simulation", color: "#8b5cf6" },
  { name: "Employee Churn Agent", model: "gpt-oss-120b", role: "Churn rates, satisfaction segments, risk flags, retention cost", color: "#7c3aed" },
  { name: "Demand Forecasting Agent", model: "qwen3-32b", role: "Trend decomposition, polyfit forecasts, seasonality, stockout risk", color: "#6d28d9" },
];

export default function AgentShowcase() {
  return (
    <section className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-[var(--text-primary)] mb-4">
            Meet the <span className="gradient-text">AI Agents</span>
          </h2>
          <p className="text-[var(--text-muted)]">Each agent is a domain expert powered by a purpose-selected LLM.</p>
        </div>
        <div className="space-y-4">
          {agents.map((a, i) => (
            <div key={a.name}
              className="glass-card p-6 flex flex-col md:flex-row items-start md:items-center gap-4 glow-border-hover transition-all duration-300 animate-fade-in-up"
              style={{ animationDelay: `${i * 0.1}s` }}>
              <div className="w-3 h-3 rounded-full flex-shrink-0 mt-1 md:mt-0" style={{ backgroundColor: a.color, boxShadow: `0 0 12px ${a.color}60` }} />
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-3 mb-1">
                  <h3 className="text-base font-semibold text-[var(--text-primary)]">{a.name}</h3>
                  <span className="px-2.5 py-0.5 text-xs font-mono rounded-full border border-[var(--border)] text-[var(--accent-light)] bg-[rgba(124,58,237,0.1)]">
                    {a.model}
                  </span>
                </div>
                <p className="text-sm text-[var(--text-muted)]">{a.role}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
