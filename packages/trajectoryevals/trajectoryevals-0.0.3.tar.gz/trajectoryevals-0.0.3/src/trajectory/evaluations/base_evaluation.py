from __future__ import annotations

import concurrent.futures as cf  # ← alias the module to avoid shadowing
import os
import pickle
import subprocess
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests
import yaml

try:
    import cloudpickle as cp  # robust pickling for __main__ classes
except Exception:
    cp = None


class BaseEvaluation:
    def run_agent(self, task: str, **agent_kwargs: Any) -> dict[str, Any]:
        return {"task": task, "output": None, "trace_id": None}

    def run(
        self,
        config_path: str,
        use_concurrency: bool = False,  # ← renamed (was `concurrent`)
        max_workers: int | None = None,
        evaluation_id: str | None = None,
        trace_scorer: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
        **agent_kwargs: Any,
    ) -> list[dict[str, Any]]:
        with open(config_path) as f:
            ids = yaml.safe_load(f) or []

        base = os.environ.get("BACKEND_BASE", "http://localhost:8000")
        api_key = os.environ.get("TRAJECTORY_API_KEY")
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

        jobs: list[dict[str, Any]] = []
        instance_slugs: set[str] = set()
        example_counter: int = (
            0  # minimal indexing to attach demo scorers for first two tasks
        )
        for uid in ids:
            r = requests.get(f"{base}/api/datasets/{uid}/", headers=headers, timeout=15)
            print("request", r.json())
            r.raise_for_status()
            data = r.json() or {}
            for ex in data.get("examples") or []:
                example_counter += 1
                task_prompt = (ex.get("task_prompt") or "").strip()

                # Minimal: app_data is a slug; compose base URL using env WORKDAY_DB_URL
                slug = str(ex.get("app_data") or "").strip()
                if slug:
                    instance_slugs.add(slug)

                env_overrides: dict[str, str] = {}
                # WORKDAY_DB_URL = os.environ.get("WORKDAY_DB_URL", "")
                docker_base = os.environ.get(
                    "WORKDAY_DB_URL", "http://localhost:8003"
                ).rstrip("/")
                if docker_base and slug:
                    env_overrides["WORKDAY_API_BASE"] = (
                        f"{docker_base.rstrip('/')}/{slug.lstrip('/')}"
                    )
                print("env_overrides", env_overrides)

                # Optional scorer config passthrough
                scorer_cfg: dict[str, Any] = {}
                if ex.get("scorer_fn") or ex.get("scorer_args") or ex.get("scorer"):
                    if isinstance(ex.get("scorer"), dict):
                        scorer_cfg = ex.get("scorer") or {}
                    else:
                        scorer_cfg = {
                            "fn": ex.get("scorer_fn"),
                            "args": ex.get("scorer_args") or {},
                        }
                # Minimal testing: if no scorer provided by example, attach demo scorers for first two examples
                if not scorer_cfg:
                    if example_counter == 1:
                        scorer_cfg = {
                            "fn": "trajectory.evaluations.base_evaluation:demo_score_task_a",
                            "args": {"expected": "create", "weight": 2},
                        }
                    elif example_counter == 2:
                        scorer_cfg = {
                            "fn": "trajectory.evaluations.base_evaluation:demo_score_task_b",
                            "args": {"expected": "approve", "weight": 1},
                        }

                jobs.append(
                    {
                        "dataset_id": uid,
                        "example_id": ex.get("id"),
                        "task": task_prompt,
                        "env": env_overrides,
                        "metadata": ({"scorer": scorer_cfg} if scorer_cfg else {}),
                    }
                )

        # Ensure mock server is up and per-instance DBs are present
        try:
            mock_apps_dir = os.environ.get("MOCK_APPS_DIR")
            if not mock_apps_dir:
                # Try to infer relative to repo layout if not provided
                candidate = (
                    Path(__file__).resolve().parents[4] / "post-building" / "mock_apps"
                )
                if candidate.exists():
                    mock_apps_dir = str(candidate)
            if mock_apps_dir:
                # Download instance DBs into mounted directory
                instances_dir = os.environ.get(
                    "WORKDAY_INSTANCES_DIR",
                    str(
                        Path(mock_apps_dir) / "apps" / "workday" / "data" / "instances"
                    ),
                )
                Path(instances_dir).mkdir(parents=True, exist_ok=True)

                supabase_url = os.environ.get("SUPABASE_URL")
                supabase_key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get(
                    "SUPABASE_ANON_KEY"
                )
                bucket = os.environ.get("WORKDAY_INSTANCE_BUCKET", "workday_instances")

                if supabase_url and supabase_key:
                    for slug in sorted(instance_slugs):
                        out_path = Path(instances_dir) / f"{slug}.db"
                        if not out_path.exists():
                            try:
                                # Supabase Storage: GET /storage/v1/object/<bucket>/<path>
                                url = f"{supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{slug}.db"
                                hdrs = {
                                    "apikey": supabase_key,
                                    "Authorization": f"Bearer {supabase_key}",
                                }
                                rr = requests.get(url, headers=hdrs, timeout=30)
                                if rr.status_code == 200:
                                    out_path.write_bytes(rr.content)
                                else:
                                    print(
                                        f"warn: could not fetch db for {slug}: {rr.status_code}"
                                    )
                            except Exception as e:
                                print(f"warn: download failed for {slug}: {e}")

                # Start docker compose service
                try:
                    print(f"[debug] starting docker compose in: {mock_apps_dir}")
                    proc = subprocess.run(
                        ["docker", "compose", "up", "-d", "--build", "workday_app"],
                        cwd=mock_apps_dir,
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    print(f"[debug] docker compose stdout:\n{proc.stdout}")
                    print(f"[debug] docker compose stderr:\n{proc.stderr}")
                except Exception as e:
                    print(f"warn: failed to start mock_apps docker: {e}")
        except Exception:
            pass

        results: list[dict[str, Any]] = []
        eval_id = evaluation_id or str(uuid.uuid4())

        # --- concurrent branch ---
        pickler = cp or pickle
        pickled_self = pickler.dumps(self)

        with cf.ProcessPoolExecutor(max_workers=max_workers or len(jobs) or 1) as pool:
            futs: list[tuple[tuple[str | None, str | None], cf.Future]] = []
            for j in jobs:
                fut = pool.submit(
                    _worker_run_pickled,
                    pickled_self,
                    j["task"],
                    j.get("metadata"),  # metadata with per-task scorer config
                    j["env"],
                    agent_kwargs,
                    eval_id,
                )
                futs.append(((j.get("dataset_id"), j.get("example_id")), fut))

            for (did, eid), fut in futs:
                out = fut.result()
                trace_id = (out or {}).get("trace_id")
                score_out = None
                if trace_id and trace_scorer:
                    try:
                        score_out = trace_scorer(
                            trace_id,
                            {
                                "dataset_id": did,
                                "example_id": eid,
                                "task": (out or {}).get("task"),
                                "evaluation_id": eval_id,
                            },
                        )
                    except Exception:
                        score_out = None

                results.append(
                    {
                        "dataset_id": did,
                        "example_id": eid,
                        "evaluation_id": eval_id,
                        **(out or {}),
                        **({"score": score_out} if score_out is not None else {}),
                    }
                )
                # results.append({"dataset_id": did, "example_id": eid, **(out or {})})

        return results


# --- Minimal demo scorer functions for testing per-trace scorer config ---
def demo_score_task_a(
    trace: dict[str, Any], args: dict[str, Any], ctx: dict[str, Any]
) -> dict[str, Any]:
    # Return an int score and echo args to verify per-trace wiring
    print(
        f"[DEMO base scorer] A: trace_id={trace.get('trace_id')} args={args} ctx={ctx}"
    )
    return {"score": 1, "scorer": "demo_task_a", "args": args}


def demo_score_task_b(
    trace: dict[str, Any], args: dict[str, Any], ctx: dict[str, Any]
) -> dict[str, Any]:
    print(
        f"[DEMO base scorer] B: trace_id={trace.get('trace_id')} args={args} ctx={ctx}"
    )
    return {"score": 0, "scorer": "demo_task_b", "args": args}


def _worker_run_pickled(
    pickled_self: bytes,
    task: str,
    metadata: dict[str, Any] | None,
    env_overrides: dict[str, str] | None,
    agent_kwargs: dict[str, Any],
    evaluation_id: str | None,
) -> dict[str, Any]:
    prev_env: dict[str, str | None] = {}
    try:
        if env_overrides:
            for k, v in env_overrides.items():
                prev_env[k] = os.environ.get(k)
                os.environ[k] = v
        # use the same pickler used to dump
        try:
            from trajectory.common.tracer.core import (
                set_global_evaluation_id,
                set_global_scorer_config,
            )

            set_global_evaluation_id(evaluation_id)
            # Pass through per-task scorer config so core.py can run scorer with raw trace
            try:
                set_global_scorer_config((metadata or {}).get("scorer"))
            except Exception:
                set_global_scorer_config(None)
        except Exception:
            pass
        be_loader = cp or pickle
        be: BaseEvaluation = be_loader.loads(pickled_self)
        res = be.run_agent(task=task, metadata=metadata, **(agent_kwargs or {}))
        return res
    finally:
        if env_overrides:
            for k, old in prev_env.items():
                if old is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = old
