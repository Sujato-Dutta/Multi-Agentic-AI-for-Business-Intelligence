"use client";

import { BarChart3, Brain, FileText } from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "Multi-Agent Intelligence",
    description: "Specialized AI agents for pricing, churn, forecasting, and general analysis — automatically routed by an orchestrator.",
  },
  {
    icon: BarChart3,
    title: "Instant Visualizations",
    description: "Agent-specific charts generated automatically — scatter plots, heatmaps, trend lines, and risk matrices.",
  },
  {
    icon: FileText,
    title: "Professional PDF Reports",
    description: "Multi-page branded reports with executive summaries, charts, data tables, and actionable recommendations.",
  },
];

export default function Features() {
  return (
    <section className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-[var(--text-primary)] mb-4">
            Three Pillars of <span className="gradient-text">Intelligent Analysis</span>
          </h2>
          <p className="text-[var(--text-muted)] max-w-2xl mx-auto">
            Every query is processed through a pipeline of specialized agents that collaborate to deliver the best output.
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <div key={f.title}
              className="glass-card p-8 glow-border-hover transition-all duration-300 hover:-translate-y-1 animate-fade-in-up"
              style={{ animationDelay: `${i * 0.15}s` }}>
              <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-6"
                style={{ background: "linear-gradient(135deg, rgba(124,58,237,0.2), rgba(99,102,241,0.2))" }}>
                <f.icon className="w-6 h-6 text-[var(--accent-light)]" />
              </div>
              <h3 className="text-xl font-semibold text-[var(--text-primary)] mb-3">{f.title}</h3>
              <p className="text-sm text-[var(--text-muted)] leading-relaxed">{f.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
