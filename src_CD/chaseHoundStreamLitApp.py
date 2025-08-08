"""
ChaseHound Streamlit App
========================

Interface graphique minimaliste permettant :
1. La saisie d'une configuration ChaseHound
2. L'envoi de cette configuration vers le backend (endpoint /run)
3. L'affichage des résultats retournés (CSV -> table)

Lancement :
    streamlit run src_CD/chaseHoundStreamLitApp.py
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, Any

import pandas as pd
import requests
import streamlit as st
import base64
import time
import yaml
from pathlib import Path
import sys
import os

# Add src_python to path to import ChaseHoundTunableParams
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src_python'))
from ChaseHoundConfig import ChaseHoundTunableParams

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Backend URL configuration - Support for remote access
import os


def _load_confidential_config() -> Dict[str, Any]:
    """Load confidential config from repo root or local copied path."""
    candidates = [
        # Repo root: ../../config/config_confidential.yaml
        Path(__file__).resolve().parents[2] / "config" / "config_confidential.yaml",
        # Deployed/copy-local: ./config/config_confidential.yaml
        Path(__file__).resolve().parent / "config" / "config_confidential.yaml",
    ]
    for path in candidates:
        try:
            if path.exists():
                with path.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    return data
        except Exception:
            continue
    return {}


def _get_backend_url_from_config(cfg: Dict[str, Any]) -> str:
    """Derive backend base URL from config. Supports either explicit URL or project_id."""
    # Common locations/keys
    url = (
        cfg.get("backend", {}).get("url")
        or cfg.get("app", {}).get("backend_url")
        or cfg.get("backend_url")
    )
    if isinstance(url, str) and url.strip():
        return url.strip().rstrip("/")

    # Project ID variants
    project_id = (
        cfg.get("backend", {}).get("project_id")
        or cfg.get("app", {}).get("backend_project_id")
        or cfg.get("BACKEND_PROJECT_ID")
        or cfg.get("backend_project_id")
    )
    if isinstance(project_id, str) and project_id.strip():
        return f"https://{project_id.strip()}.appspot.com"

    # Fallback: keep legacy localhost for local dev
    return "http://localhost:8000"


_cfg = _load_confidential_config()
BACKEND_URL = _get_backend_url_from_config(_cfg)
OFFLOAD_START_ENDPOINT = f"{BACKEND_URL}/offload/start"
OFFLOAD_STATUS_ENDPOINT = f"{BACKEND_URL}/offload/status"
INFO_ENDPOINT = f"{BACKEND_URL}/info"
HEALTH_ENDPOINT = f"{BACKEND_URL}/health"

# Optional offload settings from confidential config (not env)
OFFLOAD_TASK_COMMAND = (
    _cfg.get("offload", {}).get("task_command")
    or _cfg.get("app", {}).get("offload_task_command")
)
OFFLOAD_MAX_MINUTES = int(
    _cfg.get("offload", {}).get("max_minutes")
    or _cfg.get("app", {}).get("offload_max_minutes")
    or 60
)

default_start = date(datetime.now().year - 1, 1, 1)
default_end = datetime.now().date()

# ---------------------------------------------------------------------------
# Configuration form
# ---------------------------------------------------------------------------

st.title("🐾 ChaseHound – Stock Screener")

# ---------------------------------------------------------------------------
# Helper functions for tunable parameters handling
# ---------------------------------------------------------------------------

def _render_tunable_params_inputs(default_params: "ChaseHoundTunableParams") -> Dict[str, Any]:
    values: Dict[str, Any] = {}
    for attr, default_val in default_params.__dict__.items():
        label = attr.replace("_", " ").title()
        if isinstance(default_val, (int, float)):
            step = 1 if isinstance(default_val, int) else 0.01
            values[attr] = st.number_input(label, value=default_val, step=step)
        elif isinstance(default_val, str):
            if attr.endswith("date") or attr in ("start_date", "end_date"):
                try:
                    default_date = datetime.strptime(default_val, "%Y-%m-%d").date()
                except ValueError:
                    default_date = datetime.now().date()
                dt = st.date_input(label, value=default_date)
                values[attr] = dt
            else:
                values[attr] = st.text_input(label, value=default_val)
        else:
            values[attr] = st.text_input(label, value=str(default_val))
    return values

def _create_tunable_params_from_dict(data: Dict[str, Any]) -> "ChaseHoundTunableParams":
    tp = ChaseHoundTunableParams()
    for k, v in data.items():
        if not hasattr(tp, k):
            continue
        if isinstance(v, (date, datetime)):
            v = v.strftime("%Y-%m-%d")
        setattr(tp, k, v)
    return tp

with st.form("ch_config"):
    st.markdown("### 🔧 Tunable Parameters")

    # Dynamically render one input widget per tunable parameter
    tp_defaults = ChaseHoundTunableParams()
    param_inputs = _render_tunable_params_inputs(tp_defaults)

    submitted = st.form_submit_button("🚀 Launch")

# ---------------------------------------------------------------------------
# Submission & results display
# ---------------------------------------------------------------------------

def _detect_backend_mode() -> str:
    return "offload-only"

if submitted:
    backend_mode = _detect_backend_mode()

    if backend_mode == "offload-only":
        with st.status("Starting offloaded job...") as status_box:
            # Build params dict based on param_inputs from the form
            params_dict: Dict[str, Any] = {}
            for _name, _val in param_inputs.items():
                if isinstance(_val, (date, datetime)):
                    _val = _val.strftime("%Y-%m-%d")
                params_dict[_name] = _val

            # Include task_command if available
            body: Dict[str, Any] = {"tunable_params": params_dict}
            if OFFLOAD_TASK_COMMAND:
                body["task_command"] = OFFLOAD_TASK_COMMAND

            try:
                resp = requests.post(OFFLOAD_START_ENDPOINT, json=body, timeout=300)
            except requests.exceptions.RequestException as exc:
                st.error(f"Backend connection error: {exc}")
                st.stop()

        if resp.status_code not in (200, 202):
            st.error(f"Backend error {resp.status_code}: {resp.text}")
            st.stop()

        job_id = (resp.json() or {}).get("job_id")
        if not job_id:
            st.error("No job_id returned by backend.")
            st.stop()

        st.info(f"Offload job started. Job ID: {job_id}")

        # Poll job status until result is available
        poll_interval_sec = 5
        deadline = time.time() + OFFLOAD_MAX_MINUTES * 60

        status_placeholder = st.empty()
        while True:
            if time.time() > deadline:
                st.error("Timeout waiting for offload job to complete.")
                st.stop()

            try:
                s = requests.get(f"{OFFLOAD_STATUS_ENDPOINT}/{job_id}", timeout=15)
            except requests.exceptions.RequestException as exc:
                status_placeholder.warning(f"Temporary status fetch error: {exc}")
                time.sleep(poll_interval_sec)
                continue

            if s.status_code == 404:
                status_placeholder.error("Job not found on backend.")
                st.stop()
            if not s.ok:
                status_placeholder.warning(f"Status error {s.status_code}: {s.text}")
                time.sleep(poll_interval_sec)
                continue

            job = s.json() or {}
            vm_name = job.get("vm_name") or job.get("instance")
            job_state = job.get("state") or job.get("status") or ("result" in job and "completed") or "running"
            status_placeholder.info(f"Job state: {job_state} | VM: {vm_name or 'n/a'}")

            result = job.get("result")
            if result is not None:
                exit_code = result.get("exit_code")
                stdout_b64 = result.get("stdout_b64", "")
                stderr_b64 = result.get("stderr_b64", "")

                def _b64_to_text(b64s: str) -> str:
                    try:
                        if not b64s:
                            return ""
                        return base64.b64decode(b64s.encode("utf-8"), validate=False).decode("utf-8", errors="replace")
                    except Exception:
                        return ""

                stdout_text = _b64_to_text(stdout_b64)
                stderr_text = _b64_to_text(stderr_b64)

                if exit_code == 0:
                    st.success("Offloaded job completed successfully (exit_code=0)")
                else:
                    st.error(f"Offloaded job finished with errors (exit_code={exit_code})")

                with st.expander("Job stdout"):
                    st.code(stdout_text or "<empty>")
                with st.expander("Job stderr"):
                    st.code(stderr_text or "<empty>")

                st.stop()

            time.sleep(poll_interval_sec)

    else:
        with st.status("Sending configuration..."):
            _params_json: Dict[str, Any] = {}
            for _name, _val in param_inputs.items():
                if isinstance(_val, (date, datetime)):
                    _val = _val.strftime("%Y-%m-%d")
                _params_json[_name] = _val

            payload = {
                "tunable_params": _params_json
            }

            try:
                resp = requests.post(OFFLOAD_START_ENDPOINT, json=payload, timeout=None)
            except requests.exceptions.RequestException as exc:
                st.error(f"Backend connection error: {exc}")
                st.stop()

        if resp.status_code != 200:
            st.error(f"Backend error {resp.status_code}: {resp.text}")
            st.stop()

        data = resp.json()
        st.success(
            f"Completed in {data.get('execution_time', '?')} s – "
            f"{data.get('results_count', 0)} records"
        )

        # List of results_*.csv files
        results = data.get("results", [])
        if not results:
            st.info("No result files returned.")
            st.stop()

        filenames = [r["file"] for r in results]
        sel_file = st.selectbox("File to display", filenames)
        recs = next((r.get("records", []) for r in results if r["file"] == sel_file), [])

        if recs:
            st.dataframe(pd.DataFrame(recs), use_container_width=True)
        else:
            st.warning("This file contains no data (or an error occurred).")

st.caption("Backend: " + BACKEND_URL) 