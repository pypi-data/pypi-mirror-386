import json
import os
from typing import Any

import requests
from anthropic import Anthropic

from trajectory import Tracer, wrap

# Initialize tracer from environment
judgment = Tracer(
    api_key=(os.environ.get("TRAJECTORY_API_KEY")),
    organization_id=(
        os.environ.get("TRAJECTORY_ORG_ID")
        or os.environ.get("TRAJECTORY_ORG_ID")
        or os.environ.get("TRAJECTORY_ORG_ID")
    ),
    project_name=os.environ.get("TRAJECTORY_PROJECT", "workday_eval_project"),
    enable_monitoring=True,
    enable_evaluations=False,
)

anthropic_client = None
try:
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        anthropic_client = wrap(Anthropic(api_key=anthropic_key))
except Exception:
    anthropic_client = None


def _base():
    return os.environ.get("WORKDAY_API_BASE", "http://localhost:8003")


@judgment.observe(span_type="tool")
def wd_get_health() -> dict:
    r = requests.get(f"{_base()}/health", timeout=10)
    r.raise_for_status()
    return (
        r.json()
        if r.headers.get("content-type", "").startswith("application/json")
        else {"text": r.text}
    )


@judgment.observe(span_type="tool")
def wd_get_metrics() -> str:
    r = requests.get(f"{_base()}/metrics", timeout=10)
    r.raise_for_status()
    return r.text  # usually text/plain


@judgment.observe(span_type="tool")
def wd_get_worker(worker_id: str) -> dict:
    print(f"GETting from {_base()}/api/v1/workers/{worker_id}")
    r = requests.get(f"{_base()}/api/v1/workers/{worker_id}", timeout=10)
    r.raise_for_status()
    return r.json()


@judgment.observe(span_type="tool")
def wd_list_workers(limit: int = 50, offset: int = 0, q: str | None = None) -> dict:
    params = {"limit": limit, "offset": offset}
    if q:
        params["q"] = q
    r = requests.get(f"{_base()}/api/v1/workers", params=params, timeout=10)
    r.raise_for_status()
    return r.json()


@judgment.observe(span_type="tool")
def wd_create_worker(
    first_name: str, last_name: str, email: str, job_title: str, department: str
) -> dict:
    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "job_title": job_title,
        "department": department,
    }
    # print url here
    print(f"POSTing to {_base()}/api/v1/workers")
    r = requests.post(f"{_base()}/api/v1/workers", json=payload, timeout=10)
    r.raise_for_status()
    return r.json()


@judgment.observe(span_type="tool")
def wd_add_time_entry(
    worker_id: str, date: str, hours: float, project: str | None = None
) -> dict:
    payload = {"date": date, "hours": hours, "project": project}
    r = requests.post(
        f"{_base()}/api/v1/workers/{worker_id}/time-entries", json=payload, timeout=10
    )
    r.raise_for_status()
    return r.json()


@judgment.observe(span_type="function")
def run_agent(prompt: str) -> str:
    worker_id = "WID_000001"
    try:
        # naive parse: look for token like WID_...
        for tok in str(prompt).split():
            if tok.startswith("WID_"):
                worker_id = tok
                break
    except Exception:
        pass

    # try:
    #     model = os.environ.get("LITELLM_MODEL", "anthropic/claude-3-5-sonnet-20240620")
    #     resp = completion(
    #         model=model,
    #         messages=[
    #             {
    #                 "role": "user",
    #                 "content": (
    #                     f"Given prompt:\n{prompt}\n\n"
    #                     f"Worker JSON:\n{json.dumps(result)}\n\n"
    #                     "Return a single concise sentence acknowledging the worker and their title."
    #                 ),
    #             }
    #         ],
    #         max_tokens=200,
    #     )
    #     text = resp.choices[0].message["content"]
    #     if isinstance(text, str) and text.strip():
    #         return text
    # except Exception:
    #     pass

    # return json.dumps(result)

    health = wd_get_health()
    worker = wd_get_worker("WID_000001")

    # Optional Anthropic call for a concise summary (traced if key present)
    if anthropic_client:
        try:
            msg = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=200,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Given prompt:\n{prompt}\n\n"
                            f"Worker JSON:\n{json.dumps(worker)}\n\n"
                            "Return a single concise sentence acknowledging the worker and their title."
                        ),
                    }
                ],
            )
            text = ""
            try:
                parts = getattr(msg, "content", []) or []
                if parts and hasattr(parts[0], "text"):
                    text = parts[0].text
                elif parts and isinstance(parts[0], dict):
                    text = parts[0].get("text") or ""
            except Exception:
                text = ""
            if text:
                return text
        except Exception:
            pass

        return json.dumps({"health": health, "worker": worker})


if __name__ == "__main__":
    print(run_agent("GET worker WID_000001"))
