from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


class TraceService:
    def __init__(self, output_dir: Optional[str] = None) -> None:
        base_dir = Path(output_dir or "output/traces")
        base_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = base_dir

    def record(
        self,
        *,
        task_id: str,
        workspace_id: str,
        semantic: str,
        raw: Optional[Dict[str, Any]] = None,
        event_type: str = "task_event",
    ) -> Path:
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "task_id": task_id,
            "workspace_id": workspace_id,
            "semantic": semantic,
            "raw": raw or {},
        }

        trace_id = (raw or {}).get("trace_id", "no-trace-id")
        safe_trace_id = str(trace_id).replace("/", "_")
        out_path = self.output_dir / f"{safe_trace_id}.jsonl"

        with out_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

        logger.info(
            "TRACE_RECORDED event=%s trace_id=%s task_id=%s ws=%s",
            event_type,
            trace_id,
            task_id,
            workspace_id,
        )
        return out_path