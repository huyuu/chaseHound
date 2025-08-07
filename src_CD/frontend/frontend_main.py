"""
ChaseHound Frontend - Google App Engine Entry Point (moved to src_CD/frontend)
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import requests
from flask import Flask, jsonify, request

# Path to project root (three levels up: frontend -> src_CD -> repo)
project_root = Path(__file__).resolve().parents[2]
# Ensure root is on PYTHONPATH for all internal imports
sys.path.insert(0, str(project_root))

app = Flask(__name__)
streamlit_process = None

def start_streamlit() -> None:
    """Launch Streamlit in a separate process."""
    global streamlit_process

    env = os.environ.copy()
    env["STREAMLIT_SERVER_PORT"] = "8501"
    env["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(Path(__file__).parent / "chaseHoundStreamLitApp.py"),
        "--server.port",
        "8501",
        "--server.address",
        "0.0.0.0",
        "--server.headless",
        "true",
    ]

    streamlit_process = subprocess.Popen(cmd, env=env)
    time.sleep(10)  # Wait for Streamlit to start


@app.route("/health")
def health_check():
    """Health endpoint for App Engine."""
    return jsonify({"status": "healthy", "service": "chasehound-frontend"})


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def proxy_to_streamlit(path: str):
    """Proxy all requests to the internal Streamlit server."""
    try:
        streamlit_url = f"http://localhost:8501/{path}"
        headers = {k: v for k, v in request.headers if k.lower() != "host"}

        if request.method == "GET":
            resp = requests.get(streamlit_url, params=request.args, headers=headers, stream=True)
        elif request.method == "POST":
            resp = requests.post(streamlit_url, data=request.get_data(), headers=headers, stream=True)
        else:
            resp = requests.request(
                request.method, streamlit_url, data=request.get_data(), headers=headers, stream=True
            )

        from flask import Response

        return Response(resp.content, status=resp.status_code, headers=dict(resp.headers))
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Proxy error: {exc}"}), 500


# Start Streamlit in production
if "gunicorn" in os.environ.get("SERVER_SOFTWARE", ""):
    threading.Thread(target=start_streamlit, daemon=True).start()

if __name__ == "__main__":
    threading.Thread(target=start_streamlit, daemon=True).start()
    time.sleep(5)
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False) 