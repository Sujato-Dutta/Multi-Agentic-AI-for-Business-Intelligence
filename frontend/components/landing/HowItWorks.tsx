"use client";

import { Upload, MessageSquare, Cpu, Download } from "lucide-react";

const steps = [
  { icon: Upload, step: "01", title: "Connect Data", desc: "Upload CSV, connect REST API, or pick a demo dataset." },
  { icon: MessageSquare, step: "02", title: "Ask a Question", desc: "Type any business question in plain English." },
  { icon: Cpu, step: "03", title: "Agents Analyze", desc: "Orchestrator routes to the best specialist agent automatically." },
  { icon: Download, step: "04", title: "Get Results", desc: "Receive text insights, interactive charts, or a full PDF report." },
];

export default function HowItWorks() {
  return (
    <section className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-[var(--text-primary)] mb-4">
            How It <span className="gradient-text">Works</span>
          </h2>
          <p className="text-[var(--text-muted)]">Four steps from raw data to actionable intelligence.</p>
        </div>
        <div className="grid md:grid-cols-4 gap-6">
          {steps.map((s, i) => (
            <div key={s.step} className="relative text-center animate-fade-in-up" style={{ animationDelay: `${i * 0.12}s` }}>
              {i < steps.length - 1 && (
                <div className="hidden md:block absolute top-10 left-[60%] w-[80%] h-px bg-gradient-to-r from-[var(--accent)] to-transparent" />
              )}
              <div className="w-20 h-20 mx-auto rounded-2xl flex items-center justify-center mb-5 glass-card glow-border">
                <s.icon className="w-8 h-8 text-[var(--accent-light)]" />
              </div>
              <div className="text-xs font-mono text-[var(--accent)] mb-2">{s.step}</div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">{s.title}</h3>
              <p className="text-sm text-[var(--text-muted)]">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
