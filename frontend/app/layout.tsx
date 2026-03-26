import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Multi-Agentic AI for Business Intelligence",
  description: "AI-powered business intelligence with multi-agent analysis. Connect data, ask questions, get insights.",
  keywords: ["AI", "Business Intelligence", "Multi-Agent", "Analytics", "Data Analysis"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">
        <nav className="fixed top-0 left-0 right-0 z-50 border-b border-[var(--border)]"
          style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(16px)" }}>
          <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <Link href="/" className="text-lg font-bold gradient-text tracking-tight">
              Multi-Agentic AI for BI
            </Link>
            <div className="hidden md:flex items-center gap-8">
              <Link href="/" className="text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
                Home
              </Link>
              <Link href="/demo" className="text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
                Demo
              </Link>
              <Link href="/docs" className="text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
                Docs
              </Link>
            </div>
            <Link
              href="/demo"
              className="px-5 py-2 text-sm font-medium text-white rounded-lg transition-all duration-200 hover:opacity-90 hover:scale-105"
              style={{ background: "linear-gradient(135deg, #7c3aed, #6d28d9)" }}
            >
              Try Demo
            </Link>
          </div>
        </nav>
        <main className="pt-16">{children}</main>
      </body>
    </html>
  );
}
