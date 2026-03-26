"use client";

import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";

export default function Hero() {
  return (
    <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full opacity-20"
          style={{ background: "radial-gradient(circle, #7c3aed 0%, transparent 70%)", filter: "blur(80px)" }} />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full opacity-15"
          style={{ background: "radial-gradient(circle, #6366f1 0%, transparent 70%)", filter: "blur(80px)" }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full opacity-10"
          style={{ background: "radial-gradient(circle, #a78bfa 0%, transparent 70%)", filter: "blur(100px)" }} />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-6 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 mb-8 rounded-full border border-[var(--border)] bg-[var(--surface)] text-sm text-[var(--accent-light)] animate-fade-in-up">
          <Sparkles className="w-4 h-4" />
          <span>Powered by Multi-Agent AI Architecture</span>
        </div>

        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 animate-fade-in-up"
          style={{ animationDelay: "0.1s" }}>
          <span className="text-[var(--text-primary)]">Business Intelligence</span>
          <br />
          <span className="gradient-text glow-text">Reimagined with AI Agents</span>
        </h1>

        <p className="text-lg md:text-xl text-[var(--text-muted)] max-w-2xl mx-auto mb-10 leading-relaxed animate-fade-in-up"
          style={{ animationDelay: "0.2s" }}>
          Connect your data, ask any business question in plain English, and let specialized AI agents
          deliver insights, charts, and professional PDF reports — automatically.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-in-up"
          style={{ animationDelay: "0.3s" }}>
          <Link href="/demo"
            className="inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-semibold text-white rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-[0_0_30px_rgba(124,58,237,0.4)]"
            style={{ background: "linear-gradient(135deg, #7c3aed, #6d28d9)" }}>
            Launch Demo
            <ArrowRight className="w-5 h-5" />
          </Link>
          <Link href="/docs"
            className="inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-semibold text-[var(--text-primary)] rounded-xl border border-[var(--border)] bg-[var(--surface)] transition-all duration-300 hover:border-[var(--accent-light)] hover:bg-[rgba(124,58,237,0.1)]">
            Read Docs
          </Link>
        </div>

        {/* Stats bar */}
        <div className="mt-20 grid grid-cols-3 gap-8 max-w-lg mx-auto animate-fade-in-up" style={{ animationDelay: "0.5s" }}>
          {[
            { value: "5", label: "Specialist Agents" },
            { value: "6", label: "Demo Datasets" },
            { value: "3", label: "Output Formats" },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <div className="text-3xl font-bold gradient-text">{s.value}</div>
              <div className="text-xs text-[var(--text-muted)] mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
