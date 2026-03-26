"""FastAPI backend — routes, SSE streaming, CORS, Supabase logging."""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from functools import partial
from typing import AsyncGenerator

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from config import DEMO_DATASETS, OUTPUTS_DIR
from agents.orchestrator import OrchestratorAgent
from utils.supabase_logger import _init_supabase, new_session_id, log_agent_event

# ─── Logging setup ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

# Initialize Supabase direct logger (only agent events, not all Python logs)
_init_supabase()

logger = logging.getLogger(__name__)

# ─── App ─────────────────────────────────────────────────────────────
app = FastAPI(title="Multi-Agentic AI for Business Intelligence", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/demo-datasets")
async def demo_datasets() -> dict:
    return {"datasets": DEMO_DATASETS}


@app.post("/analyze")
async def analyze(
    query: str = Form(...),
    data_source: str = Form(...),
    file: UploadFile | None = File(None),
    rest_url: str | None = Form(None),
    rest_headers: str | None = Form(None),
    rest_params: str | None = Form(None),
    demo_dataset: str | None = Form(None),
    agent_mode: str = Form("auto"),
    output_override: str | None = Form(None),
) -> StreamingResponse:
    file_bytes = await file.read() if file else None
    session_id = new_session_id()

    # Log the incoming request
    log_agent_event(
        agent="API",
        event="request",
        message=f"New analysis request: {query[:100]}",
        query=query,
        data_source=data_source,
    )

    async def event_stream() -> AsyncGenerator[str, None]:
        loop = asyncio.get_event_loop()
        orchestrator = OrchestratorAgent()
        start_time = time.time()
        run_fn = partial(
            _run_pipeline, orchestrator,
            query=query, agent_mode=agent_mode, output_override=output_override,
            source=data_source, file_bytes=file_bytes,
            rest_url=rest_url, rest_headers=rest_headers,
            rest_params=rest_params, demo_name=demo_dataset,
        )
        events = await loop.run_in_executor(None, run_fn)
        duration_ms = int((time.time() - start_time) * 1000)

        for event in events:
            yield f"data: {json.dumps(event)}\n\n"

        # Log pipeline completion
        log_agent_event(
            agent="Pipeline",
            event="complete",
            message=f"Pipeline finished in {duration_ms}ms",
            duration_ms=duration_ms,
            query=query,
            data_source=data_source,
        )

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _run_pipeline(orchestrator: OrchestratorAgent, **kwargs) -> list[dict]:
    """Run the synchronous agent pipeline — called in executor."""
    return list(orchestrator.run(**kwargs))


@app.get("/download/{filename}")
async def download(filename: str) -> FileResponse:
    filepath = OUTPUTS_DIR / filename
    if not filepath.exists():
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "File not found"}, status_code=404)
    return FileResponse(str(filepath), media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename={filename}"})
