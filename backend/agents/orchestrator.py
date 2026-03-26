"""Orchestrator agent — routes queries to specialist agents via LLM intent detection."""

import logging
from typing import Any, Generator

from config import INTENT_KEYWORDS, OUTPUT_KEYWORDS, DEFAULT_OUTPUT_FORMAT
from utils.llm import call_llm
from utils.validators import validate_agent_output, validate_and_ground, validate_dataframe_quality
from utils.column_mapper import check_specialist_viable, map_columns
from utils.supabase_logger import log_agent_event
from agents.ingestion import DataIngestionAgent
from agents.analysis import AnalysisAgent
from agents.pricing import DynamicPricingAgent
from agents.churn import EmployeeChurnAgent
from agents.forecasting import DemandForecastingAgent
from agents.output import OutputAgent

logger = logging.getLogger(__name__)

_SPECIALIST_MAP = {
    "pricing": DynamicPricingAgent,
    "churn": EmployeeChurnAgent,
    "forecasting": DemandForecastingAgent,
    "general": AnalysisAgent,
}


class OrchestratorAgent:
    """Routes user queries through the multi-agent pipeline via intent detection."""

    def run(self, *, query: str, agent_mode: str, output_override: str | None,
            source: str, file_bytes: bytes | None = None,
            rest_url: str | None = None, rest_headers: str | None = None,
            rest_params: str | None = None, demo_name: str | None = None
            ) -> Generator[dict[str, Any], None, None]:

        # 1. Detect intent
        if agent_mode == "auto":
            intent = self._detect_intent(query)
        else:
            intent = agent_mode if agent_mode in _SPECIALIST_MAP else "general"

        # 2. Detect output format
        output_format = output_override or self._detect_output(query)

        logger.info("Orchestrator: intent=%s, output=%s", intent, output_format)
        yield {"event": "agent_start", "agent": "Orchestrator"}
        yield {"event": "agent_done", "agent": "Orchestrator",
               "detail": f"Intent: {intent}, Output: {output_format}"}

        # 3. Data ingestion
        yield {"event": "agent_start", "agent": "DataIngestion"}
        try:
            ingestion = DataIngestionAgent()
            data = ingestion.run(source=source, file_bytes=file_bytes,
                                 rest_url=rest_url, rest_headers=rest_headers,
                                 rest_params=rest_params, demo_name=demo_name)
            df = data["dataframe"]
            # Validate data quality
            quality = validate_dataframe_quality(df)
            quality_detail = f"{data['metadata']['rows']} rows, {len(data['metadata']['columns'])} cols"
            if quality['warnings']:
                quality_detail += f" ⚠ {len(quality['warnings'])} warnings"
                for w in quality['warnings'][:3]:
                    logger.warning("Data quality: %s", w)
            yield {"event": "agent_done", "agent": "DataIngestion",
                   "detail": quality_detail}
        except Exception as e:
            logger.error("Ingestion failed: %s", e)
            yield {"event": "error", "agent": "DataIngestion", "message": str(e)}
            yield {"event": "done"}
            return

        # 4. Column viability check — does the data fit the specialist?
        if intent != "general":
            viable, confidence, mapping = check_specialist_viable(df, intent)
            if not viable:
                logger.warning(
                    "Specialist '%s' not viable for this data (confidence=%.0f%%). "
                    "Falling back to General Analysis.",
                    intent, confidence * 100
                )
                yield {"event": "agent_done", "agent": "ColumnMapper",
                       "detail": f"Specialist '{intent}' not viable (confidence: {confidence*100:.0f}%). Falling back to General Analysis."}
                intent = "general"
            else:
                # Map columns to canonical names before passing to specialist
                df, mapping, confidence = map_columns(df, intent)
                col_detail = f"Mapped {len(mapping)} columns (confidence: {confidence*100:.0f}%)"
                if mapping:
                    mapped_str = ", ".join(f"{orig}→{canon}" for canon, orig in mapping.items())
                    col_detail += f": {mapped_str}"
                logger.info("Column mapper: %s", col_detail)

        # 5. Specialist agent
        specialist_name = _SPECIALIST_MAP[intent].__name__
        yield {"event": "agent_start", "agent": specialist_name}
        try:
            specialist = _SPECIALIST_MAP[intent]()
            result = specialist.run(df, query)

            if not validate_agent_output(result):
                logger.warning("Validation failed for %s, retrying once", specialist_name)
                result = specialist.run(df, query)
                if not validate_agent_output(result):
                    logger.warning("Retry failed, falling back to AnalysisAgent")
                    specialist = AnalysisAgent()
                    specialist_name = "AnalysisAgent"
                    intent = "general"
                    result = specialist.run(df, query)

            # 5b. Hallucination guard — ground insights against computed data
            result, grounding_score = validate_and_ground(result, intent)
            insight_count = len(result.get('insights', []))
            yield {"event": "agent_done", "agent": specialist_name,
                   "detail": f"{insight_count} grounded insights (score: {grounding_score:.0%})"}

            # Log grounding score to Supabase
            log_agent_event(
                agent=specialist_name,
                event="grounding",
                message=f"Grounding score: {grounding_score:.2f} ({insight_count} insights)",
                grounding_score=grounding_score,
                query=query,
            )
        except Exception as e:
            logger.error("%s failed: %s", specialist_name, e)
            yield {"event": "error", "agent": specialist_name, "message": str(e)}
            # Log error to Supabase
            log_agent_event(
                agent=specialist_name,
                event="error",
                message=str(e),
                query=query,
                level="ERROR",
            )
            # Fallback to general analysis
            try:
                specialist = AnalysisAgent()
                specialist_name = "AnalysisAgent"
                intent = "general"
                result = specialist.run(df, query)
                result, grounding_score = validate_and_ground(result, intent)
                insight_count = len(result.get('insights', []))
                yield {"event": "agent_done", "agent": specialist_name,
                       "detail": f"Fallback completed: {insight_count} grounded insights (score: {grounding_score:.0%})"}
                
                log_agent_event(
                    agent=specialist_name,
                    event="grounding",
                    message=f"Fallback grounding score: {grounding_score:.2f} ({insight_count} insights)",
                    grounding_score=grounding_score,
                    query=query,
                )
            except Exception as e2:
                # Log inner fallback error to Supabase
                log_agent_event(
                    agent="AnalysisAgent",
                    event="error",
                    message=f"Fallback failed: {str(e2)}",
                    query=query,
                    level="ERROR",
                )
                yield {"event": "error", "agent": "AnalysisAgent", "message": str(e2)}
                yield {"event": "done"}
                return

        # 6. Output agent
        yield {"event": "agent_start", "agent": "OutputAgent"}
        try:
            output_agent = OutputAgent()
            # Build the analysis dict to pass — depends on agent type
            analysis_dict = result.get("analysis_dict", result.get("pricing_analysis",
                            result.get("churn_analysis", result.get("forecast_df", {}))))
            if isinstance(analysis_dict, str):
                analysis_dict = {}

            out = output_agent.run(
                insights=result.get("insights", []),
                analysis_dict=result,
                df=df,
                output_format=output_format,
                agent_type=intent,
                query=query,
            )
            yield {"event": "agent_done", "agent": "OutputAgent", "detail": f"Format: {output_format}"}

            if out["type"] == "text":
                yield {"event": "output_text", "content": out["content"]}
            elif out["type"] == "charts":
                yield {"event": "output_charts", "charts": out["charts"]}
            elif out["type"] == "report":
                yield {"event": "output_report", "filename": out["filename"],
                       "download_url": f"/download/{out['filename']}"}
                if out.get("charts"):
                    yield {"event": "output_charts", "charts": out["charts"]}
        except Exception as e:
            logger.error("OutputAgent failed: %s", e)
            yield {"event": "error", "agent": "OutputAgent", "message": str(e)}

        yield {"event": "done"}

    def _detect_intent(self, query: str) -> str:
        q_lower = query.lower()
        # Keyword matching first
        for intent, keywords in INTENT_KEYWORDS.items():
            if any(kw in q_lower for kw in keywords):
                return intent
        # LLM fallback
        try:
            prompt = (
                f"Classify this business query into one category: pricing, churn, forecasting, or general.\n"
                f"Query: {query}\n\nRespond with ONLY the category name, nothing else."
            )
            result = call_llm("orchestrator", prompt).strip().lower()
            if result in _SPECIALIST_MAP:
                return result
        except Exception:
            pass
        return "general"

    def _detect_output(self, query: str) -> str:
        q_lower = query.lower()
        for fmt, keywords in OUTPUT_KEYWORDS.items():
            if any(kw in q_lower for kw in keywords):
                return fmt
        return DEFAULT_OUTPUT_FORMAT

