"""Output agent — renders text, charts, or PDF reports. No LLM calls."""

import base64
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    Table, TableStyle, PageBreak,
)

from config import (
    OUTPUTS_DIR, PDF_BRAND_NAME, PDF_FOOTER,
    PDF_ACCENT_COLOR, PDF_HEADER_COLOR, DISCOUNT_SCENARIOS,
)

logger = logging.getLogger(__name__)
sns.set_theme(style="darkgrid", palette="viridis")
OUTPUTS_DIR.mkdir(exist_ok=True)


class OutputAgent:
    """Renders final output as text, charts, or PDF report. No LLM calls."""

    def run(self, *, insights: list[str], analysis_dict: dict, df: pd.DataFrame,
            output_format: str, agent_type: str, query: str) -> dict[str, Any]:
        logger.info("OutputAgent: format=%s, agent=%s", output_format, agent_type)

        if output_format == "text":
            return self._render_text(insights, agent_type, query)
        elif output_format == "charts":
            charts = self._generate_charts(analysis_dict, df, agent_type)
            return {"type": "charts", "charts": charts}
        else:
            charts = self._generate_charts(analysis_dict, df, agent_type)
            filename = self._build_pdf(insights, charts, analysis_dict, df, agent_type, query)
            return {"type": "report", "filename": filename, "charts": charts}

    def _render_text(self, insights: list[str], agent_type: str, query: str) -> dict[str, Any]:
        header = f"## Analysis Results — {agent_type.title()} Agent\n\n**Query:** {query}\n\n"
        body = "### Key Insights\n\n" + "\n".join(f"- {i}" for i in insights)
        return {"type": "text", "content": header + body}

    def _generate_charts(self, analysis: dict, df: pd.DataFrame, agent_type: str) -> list[dict]:
        generators = {
            "general": self._charts_general,
            "pricing": self._charts_pricing,
            "churn": self._charts_churn,
            "forecasting": self._charts_forecasting,
        }
        fn = generators.get(agent_type, self._charts_general)
        return fn(analysis, df)

    def _fig_to_b64(self, fig: plt.Figure) -> str:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="#0d1424")
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode()

    # ── General charts ──────────────────────────────────────────────
    def _charts_general(self, analysis: dict, df: pd.DataFrame) -> list[dict]:
        charts = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        # Chart 1: distribution / bar
        if numeric_cols:
            fig, ax = plt.subplots(figsize=(8, 5))
            col = numeric_cols[0]
            if df[col].nunique() > 10:
                ax.hist(df[col].dropna(), bins=25, color="#6366f1", edgecolor="#1e1b4b")
                ax.set_title(f"Distribution of {col}", color="white", fontsize=14)
            else:
                df[col].value_counts().head(10).plot.bar(ax=ax, color="#6366f1")
                ax.set_title(f"Top Values — {col}", color="white", fontsize=14)
            self._style_ax(ax)
            charts.append({"title": f"Distribution of {col}", "image": self._fig_to_b64(fig),
                           "caption": f"Shows the distribution of {col} across {len(df)} records."})

        # Chart 2: correlation heatmap or trend
        if len(numeric_cols) > 2:
            fig, ax = plt.subplots(figsize=(8, 6))
            corr = df[numeric_cols[:8]].corr()
            sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdYlBu_r", ax=ax,
                        cbar_kws={"shrink": 0.8})
            ax.set_title("Correlation Matrix", color="white", fontsize=14)
            fig.patch.set_facecolor("#0d1424")
            charts.append({"title": "Correlation Matrix", "image": self._fig_to_b64(fig),
                           "caption": f"Correlation heatmap of {len(numeric_cols)} numeric features."})
        elif numeric_cols:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.plot(df[numeric_cols[0]].values[:50], color="#a78bfa", linewidth=2)
            ax.set_title(f"Trend — {numeric_cols[0]}", color="white", fontsize=14)
            self._style_ax(ax)
            charts.append({"title": f"Trend — {numeric_cols[0]}", "image": self._fig_to_b64(fig),
                           "caption": f"Trend line for {numeric_cols[0]}."})

        # Chart 3: top-N bar
        if numeric_cols:
            fig, ax = plt.subplots(figsize=(8, 5))
            col = numeric_cols[0]
            top = df.nlargest(5, col)
            labels = top.iloc[:, 0].astype(str) if df.columns[0] != col else top.index.astype(str)
            ax.barh(labels, top[col].values, color="#8b5cf6")
            ax.set_title(f"Top 5 by {col}", color="white", fontsize=14)
            self._style_ax(ax)
            charts.append({"title": f"Top 5 by {col}", "image": self._fig_to_b64(fig),
                           "caption": f"Top 5 records ranked by {col}."})

        return charts[:3]

    # ── Pricing charts ──────────────────────────────────────────────
    def _charts_pricing(self, analysis: dict, df: pd.DataFrame) -> list[dict]:
        charts = []
        pricing = analysis.get("pricing_analysis", analysis)

        # Chart 1: price vs revenue scatter
        if "price" in df.columns and "revenue" in df.columns:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.scatter(df["price"], df["revenue"], alpha=0.7, c="#6366f1", s=50)
            z = np.polyfit(df["price"], df["revenue"], 1)
            p = np.poly1d(z)
            x_line = np.linspace(df["price"].min(), df["price"].max(), 50)
            ax.plot(x_line, p(x_line), "--", color="#f59e0b", linewidth=2)
            ax.set_title("Price vs Revenue with Trend", color="white", fontsize=14)
            ax.set_xlabel("Price", color="#cbd5e1")
            ax.set_ylabel("Revenue", color="#cbd5e1")
            self._style_ax(ax)
            charts.append({"title": "Price vs Revenue", "image": self._fig_to_b64(fig),
                           "caption": "Scatter plot showing price-revenue relationship with linear trend."})

        # Chart 2: discount simulation
        sim = pricing.get("discount_simulation", [])
        if sim:
            fig, ax = plt.subplots(figsize=(8, 5))
            labels = [s["discount_pct"] for s in sim]
            changes = [s["revenue_change_pct"] for s in sim]
            bar_colors = ["#22c55e" if c > 0 else "#ef4444" for c in changes]
            ax.bar(labels, changes, color=bar_colors)
            ax.set_title("Discount Scenario Impact", color="white", fontsize=14)
            ax.set_ylabel("Revenue Change %", color="#cbd5e1")
            ax.axhline(y=0, color="#94a3b8", linewidth=0.8)
            self._style_ax(ax)
            charts.append({"title": "Discount Scenarios", "image": self._fig_to_b64(fig),
                           "caption": f"Revenue impact across {len(DISCOUNT_SCENARIOS)} discount scenarios."})

        # Chart 3: margin by segment
        margin_seg = pricing.get("margin_by_segment", {})
        if margin_seg:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.barh(list(margin_seg.keys()), [v * 100 for v in margin_seg.values()], color="#8b5cf6")
            ax.set_title("Margin by Product Segment", color="white", fontsize=14)
            ax.set_xlabel("Margin %", color="#cbd5e1")
            self._style_ax(ax)
            charts.append({"title": "Margin by Segment", "image": self._fig_to_b64(fig),
                           "caption": "Profit margin percentage across product segments."})

        return charts[:3]

    # ── Churn charts ────────────────────────────────────────────────
    def _charts_churn(self, analysis: dict, df: pd.DataFrame) -> list[dict]:
        charts = []
        churn = analysis.get("churn_analysis", analysis)

        # Chart 1: churn by department
        dept_rates = churn.get("churn_rate_by_department", {})
        if dept_rates:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.bar(dept_rates.keys(), [v * 100 for v in dept_rates.values()], color="#ef4444")
            ax.set_title("Churn Rate by Department", color="white", fontsize=14)
            ax.set_ylabel("Churn Rate %", color="#cbd5e1")
            self._style_ax(ax)
            plt.xticks(rotation=30, ha="right")
            charts.append({"title": "Churn by Department", "image": self._fig_to_b64(fig),
                           "caption": "Churn rate percentage across departments."})

        # Chart 2: satisfaction histogram
        sat_col = None
        for c in ["satisfaction_score", "satisfaction"]:
            if c in df.columns:
                sat_col = c
                break
        if sat_col:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.hist(df[sat_col].dropna(), bins=20, color="#6366f1", edgecolor="#1e1b4b")
            ax.set_title("Satisfaction Score Distribution", color="white", fontsize=14)
            ax.set_xlabel("Satisfaction Score", color="#cbd5e1")
            self._style_ax(ax)
            charts.append({"title": "Satisfaction Distribution", "image": self._fig_to_b64(fig),
                           "caption": "Distribution of employee satisfaction scores."})

        # Chart 3: tenure vs satisfaction scatter
        if sat_col and "tenure_years" in df.columns:
            fig, ax = plt.subplots(figsize=(8, 5))
            risk_col = "churned" if "churned" in df.columns else "attrition_risk"
            if risk_col in df.columns:
                if df[risk_col].dtype == object:
                    color_map = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"}
                    for risk, color in color_map.items():
                        mask = df[risk_col] == risk
                        ax.scatter(df.loc[mask, "tenure_years"], df.loc[mask, sat_col],
                                   c=color, label=risk, alpha=0.7, s=40)
                    ax.legend(title="Risk Level")
                else:
                    scatter = ax.scatter(df["tenure_years"], df[sat_col], c=df[risk_col],
                                         cmap="RdYlGn_r", alpha=0.7, s=40)
                    plt.colorbar(scatter, ax=ax, label="Churned")
            else:
                ax.scatter(df["tenure_years"], df[sat_col], c="#6366f1", alpha=0.7, s=40)
            ax.set_title("Tenure vs Satisfaction (Risk)", color="white", fontsize=14)
            ax.set_xlabel("Tenure (years)", color="#cbd5e1")
            ax.set_ylabel("Satisfaction", color="#cbd5e1")
            self._style_ax(ax)
            charts.append({"title": "Risk Scatter", "image": self._fig_to_b64(fig),
                           "caption": "Scatter plot of tenure vs satisfaction colored by risk level."})

        return charts[:3]

    # ── Forecasting charts ──────────────────────────────────────────
    def _charts_forecasting(self, analysis: dict, df: pd.DataFrame) -> list[dict]:
        charts = []
        fdata = analysis.get("forecast_df", analysis)

        # Chart 1: historical + forecast line
        hist = fdata.get("historical_values", [])
        forecasts = fdata.get("forecasts", {})
        if hist:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(range(len(hist)), hist, color="#6366f1", linewidth=2, label="Historical")
            if forecasts:
                first_fc = list(forecasts.values())[0]
                fc_val = first_fc.get("mean_forecast", hist[-1])
                ci = first_fc.get("confidence_interval", 0)
                fc_len = 30
                fc_x = range(len(hist), len(hist) + fc_len)
                fc_y = np.linspace(hist[-1], fc_val, fc_len)
                ax.plot(fc_x, fc_y, "--", color="#f59e0b", linewidth=2, label="Forecast")
                ax.fill_between(fc_x, fc_y - ci, fc_y + ci, alpha=0.2, color="#f59e0b")
            ax.set_title("Historical + Forecast", color="white", fontsize=14)
            ax.legend()
            self._style_ax(ax)
            charts.append({"title": "Demand Forecast", "image": self._fig_to_b64(fig),
                           "caption": "Historical demand with projected forecast and confidence interval."})

        # Chart 2: seasonality
        demand_col = None
        date_col = None
        for c in df.columns:
            if "demand" in c.lower() or "units" in c.lower():
                demand_col = c
            if "date" in c.lower():
                date_col = c
        if demand_col and date_col:
            df_c = df.copy()
            try:
                df_c[date_col] = pd.to_datetime(df_c[date_col])
                df_c["month"] = df_c[date_col].dt.month_name()
                monthly = df_c.groupby(df_c[date_col].dt.month)[demand_col].mean()
                fig, ax = plt.subplots(figsize=(8, 5))
                ax.bar(monthly.index, monthly.values, color="#8b5cf6")
                ax.set_title("Average Demand by Month", color="white", fontsize=14)
                ax.set_xlabel("Month", color="#cbd5e1")
                self._style_ax(ax)
                charts.append({"title": "Seasonality Pattern", "image": self._fig_to_b64(fig),
                               "caption": "Monthly average demand showing seasonal patterns."})
            except Exception:
                pass

        # Chart 3: stockout risk
        stockout_days = fdata.get("stockout_risk_days")
        if stockout_days is not None and "inventory" in df.columns and demand_col:
            fig, ax = plt.subplots(figsize=(10, 5))
            df_c = df.head(60).copy()
            x = range(len(df_c))
            ax.plot(x, df_c[demand_col].values, color="#6366f1", label="Demand", linewidth=2)
            ax.plot(x, df_c["inventory"].values, color="#22c55e", label="Inventory", linewidth=2)
            ax.fill_between(x, df_c[demand_col].values, df_c["inventory"].values,
                            where=df_c["inventory"].values < df_c[demand_col].values,
                            alpha=0.3, color="#ef4444", label="Stockout Risk")
            ax.set_title("Demand vs Inventory — Stockout Risk", color="white", fontsize=14)
            ax.legend()
            self._style_ax(ax)
            charts.append({"title": "Stockout Risk", "image": self._fig_to_b64(fig),
                           "caption": f"{stockout_days} days identified with potential stockout risk."})

        return charts[:3]

    def _style_ax(self, ax: plt.Axes) -> None:
        ax.set_facecolor("#0d1424")
        ax.figure.patch.set_facecolor("#0d1424")
        ax.tick_params(colors="#94a3b8")
        for spine in ax.spines.values():
            spine.set_color("#1e2d4a")

    # ── PDF Builder ─────────────────────────────────────────────────
    def _build_pdf(self, insights: list[str], charts: list[dict], analysis: dict,
                   df: pd.DataFrame, agent_type: str, query: str) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{ts}.pdf"
        filepath = OUTPUTS_DIR / filename

        doc = SimpleDocTemplate(str(filepath), pagesize=A4,
                                topMargin=0.8 * inch, bottomMargin=0.8 * inch)
        styles = getSampleStyleSheet()
        accent = colors.Color(PDF_ACCENT_COLOR[0] / 255, PDF_ACCENT_COLOR[1] / 255, PDF_ACCENT_COLOR[2] / 255)
        header_c = colors.Color(PDF_HEADER_COLOR[0] / 255, PDF_HEADER_COLOR[1] / 255, PDF_HEADER_COLOR[2] / 255)

        title_style = ParagraphStyle("CustomTitle", parent=styles["Title"],
                                     textColor=header_c, fontSize=22, spaceAfter=20)
        heading_style = ParagraphStyle("CustomH2", parent=styles["Heading2"],
                                       textColor=accent, fontSize=16, spaceAfter=12)
        body_style = ParagraphStyle("CustomBody", parent=styles["Normal"],
                                     fontSize=11, leading=16, spaceAfter=8)
        footer_style = ParagraphStyle("Footer", parent=styles["Normal"],
                                       fontSize=8, textColor=colors.grey)

        elements: list = []

        # Page 1: Title page
        elements.append(Spacer(1, 1.5 * inch))
        elements.append(Paragraph(PDF_BRAND_NAME, title_style))
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(Paragraph(f"<b>Query:</b> {query}", body_style))
        elements.append(Paragraph(f"<b>Agent:</b> {agent_type.title()}", body_style))
        elements.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style))
        elements.append(Paragraph(f"<b>Dataset:</b> {len(df)} rows × {len(df.columns)} columns", body_style))
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph(PDF_FOOTER, footer_style))
        elements.append(PageBreak())

        # Page 2: Executive Summary
        elements.append(Paragraph("Executive Summary", heading_style))
        elements.append(Spacer(1, 0.2 * inch))
        for insight in insights:
            clean = insight.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            elements.append(Paragraph(f"• {clean}", body_style))
        elements.append(PageBreak())

        # Page 3+: Charts
        for chart in charts:
            elements.append(Paragraph(chart["title"], heading_style))
            img_bytes = base64.b64decode(chart["image"])
            img_buf = io.BytesIO(img_bytes)
            elements.append(RLImage(img_buf, width=6 * inch, height=3.5 * inch))
            elements.append(Paragraph(chart.get("caption", ""), body_style))
            elements.append(Spacer(1, 0.3 * inch))

        # Final page: data overview
        elements.append(PageBreak())
        elements.append(Paragraph("Data Overview (First 10 Rows)", heading_style))
        preview = df.head(10)
        table_data = [list(preview.columns)] + preview.astype(str).values.tolist()
        # Truncate wide tables
        max_cols = 8
        if len(table_data[0]) > max_cols:
            table_data = [row[:max_cols] for row in table_data]
        col_width = min(6.5 * inch / len(table_data[0]), 1.5 * inch)
        t = Table(table_data, colWidths=[col_width] * len(table_data[0]))
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), accent),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph(f"{PDF_FOOTER} — {datetime.now().strftime('%Y-%m-%d %H:%M')}", footer_style))

        doc.build(elements)
        logger.info("PDF report saved: %s", filepath)
        return filename
