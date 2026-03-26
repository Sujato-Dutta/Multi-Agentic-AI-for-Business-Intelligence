"use client";

export default function Footer() {
  return (
    <footer className="border-t border-[var(--border)] py-12 px-6">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <div className="text-lg font-bold gradient-text mb-1">Multi-Agentic AI for Business Intelligence</div>
          <p className="text-sm text-[var(--text-muted)]">Open-source AI-powered business intelligence platform.</p>
        </div>
        <div className="text-sm text-[var(--text-muted)] text-center md:text-right">
          <p>MIT License</p>
          <p className="mt-2" style={{ textShadow: "0 0 10px rgba(255,255,255,0.3)" }}>
            <span className="text-white font-medium">Made by Sujato Dutta</span>
          </p>
        </div>
      </div>
    </footer>
  );
}
