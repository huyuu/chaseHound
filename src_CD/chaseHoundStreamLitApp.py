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
import re

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
RUN_ENDPOINT = f"{BACKEND_URL}/run"

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


def _prettify_attr_label(attr: str) -> str:
    # Handle snake_case and camelCase / PascalCase
    s = attr.replace("_", " ").replace("-", " ")
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    words = []
    for w in s.split(" "):
        if len(w) <= 3 and w.isupper():
            words.append(w)
        else:
            words.append(w.capitalize())
    return " ".join(words)


def _render_tunable_params_inputs(default_params: "ChaseHoundTunableParams") -> Dict[str, Any]:
    values: Dict[str, Any] = {}
    for attr, default_val in default_params.__dict__.items():
        label = _prettify_attr_label(attr)
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
    return "local-sync"

if submitted:
    backend_mode = _detect_backend_mode()

    if backend_mode == "local-sync":
        with st.status("Starting offloaded job...") as status_box:
            # Build params dict based on param_inputs from the form
            params_dict: Dict[str, Any] = {}
            for _name, _val in param_inputs.items():
                if isinstance(_val, (date, datetime)):
                    _val = _val.strftime("%Y-%m-%d")
                params_dict[_name] = _val

            # Include task_command if available
            body: Dict[str, Any] = {"tunable_params": params_dict}

            try:
                resp = requests.post(RUN_ENDPOINT, json=body, timeout=300)
            except requests.exceptions.RequestException as exc:
                st.error(f"Backend connection error: {exc}")
                st.stop()

            results = resp.json().get("results", None)

            if resp.status_code != 200:
                st.error(f"Backend error {resp.status_code}: {resp.text}")
                st.stop()

            data = resp.json()
            status_box.update(label="Job completed!", state="complete")
            
            # Display execution summary
            st.success(
                f"✅ Completed in {data.get('execution_time', '?')} seconds – "
                f"{data.get('results_count', 0)} total records found"
            )

            # Display results from CSV files
            results = data.get("results", [])
            if not results:
                st.info("No result files were generated.")
            else:
                st.markdown("### 📊 Results")
                
                # If multiple files, let user select which one to display
                if len(results) > 1:
                    file_options = []
                    file_map = {}
                    
                    for result in results:
                        filename = result.get("file", "Unknown")
                        if "error" in result:
                            file_options.append(f"{filename} ❌ (Error)")
                            file_map[f"{filename} ❌ (Error)"] = result
                        else:
                            record_count = len(result.get("records", []))
                            file_options.append(f"{filename} ({record_count} records)")
                            file_map[f"{filename} ({record_count} records)"] = result
                    
                    selected_option = st.selectbox("📁 Select file to display:", file_options)
                    selected_result = file_map[selected_option]
                else:
                    selected_result = results[0]

                # Display the selected result
                if "error" in selected_result:
                    st.error(f"❌ Error reading {selected_result['file']}: {selected_result['error']}")
                else:
                    records = selected_result.get("records", [])
                    if records:
                        df = pd.DataFrame(records)
                        # Move the 'symbol' column to the first position if it exists
                        if "symbol" in df.columns:
                            cols = list(df.columns)
                            cols.insert(0, cols.pop(cols.index("symbol")))
                            df = df[cols]
                        st.markdown(f"**File:** `{selected_result['file']}`")
                        st.markdown(f"**Records:** {len(records)}")
                        
                        # Display the dataframe with enhanced formatting
                        st.dataframe(
                            df, 
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Provide download option
                        csv_data = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download as CSV",
                            data=csv_data,
                            file_name=selected_result['file'],
                            mime="text/csv"
                        )
                    else:
                        st.warning(f"📄 {selected_result['file']} contains no data.")

st.caption("Backend: " + BACKEND_URL) 