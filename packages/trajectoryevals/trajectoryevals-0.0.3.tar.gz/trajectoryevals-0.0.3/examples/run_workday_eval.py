import os
import sys
from typing import Any, Dict, Optional
import importlib.util
from pathlib import Path

# Import BaseEvaluation from installed judgeval package
from trajectory.evaluations import BaseEvaluation

# Robust local import of simple_workday_agent.py (same folder)
_THIS_DIR = Path(__file__).resolve().parent
_AGENT_FILE = _THIS_DIR / "simple_workday_agent.py"
spec = importlib.util.spec_from_file_location("simple_workday_agent", str(_AGENT_FILE))
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)
run_agent = mod.run_agent


class WorkdayEval(BaseEvaluation):
    def run_agent(self, task: str, **_: Any) -> Dict[str, Any]:
        out = run_agent(task)
        return {"task": task, "output": out, "trace_id": None}


if __name__ == "__main__":
    # Example YAML path from argv or default
    cfg = sys.argv[1] if len(sys.argv) > 1 else "datasets.yaml"
    # Ensure API base and key are available
    os.environ.setdefault("BACKEND_BASE", os.environ.get("BACKEND_BASE", "http://localhost:8000"))
    # TRAJECTORY_API_KEY should already be set in env

    # Run sequential
    # res_seq = WorkdayEval().run(cfg, concurrent=False)
    # print("Sequential results:", res_seq)

    # Example simple scorer that attaches evaluation_id for demonstration
    def simple_trace_scorer(trace_id: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        return {"trace_id": trace_id, "evaluation_id": ctx.get("evaluation_id")}
    os.environ.setdefault("BACKEND_BASE", "http://localhost:8000")
    os.environ.setdefault("WORKDAY_API_BASE", "http://localhost:8003")
    # Run concurrent (per-process)
    res_conc = WorkdayEval().run(
        cfg,
        use_concurrency=True,
        max_workers=4,
        trace_scorer=simple_trace_scorer,
    )
    
    print("Concurrent results:", res_conc)


