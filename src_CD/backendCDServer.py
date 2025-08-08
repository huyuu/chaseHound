"""
BackendCDServer
===============

Serveur backend minimal : reçoit une configuration (JSON), exécute ChaseHound et renvoie les
résultats. Il s'agit d'une implémentation *synchrone* – l'appelant attend la fin de l'exécution.

Prérequis :
    pip install -r src_CD/requirements.txt

Lancement :
    python src_CD/backendCDServer.py   # http://localhost:8000/run
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

from src_python.ChaseHoundConfig import ChaseHoundConfig, ChaseHoundTunableParams
from src_python.ChaseHoundMain import ChaseHoundMain

class Colors:
    """Color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


app = Flask(__name__)
# Enable CORS for remote access
CORS(app, origins="*")  # In production, specify allowed origins

###############################################################################
# Helpers
###############################################################################

def _build_config_from_json(data: Dict[str, Any]) -> ChaseHoundConfig:
    """Convertit le JSON du client en *ChaseHoundConfig*."""
    params = ChaseHoundTunableParams()
    for key, value in data["tunable_params"].items():
        if hasattr(params, key):
            setattr(params, key, value)
    return ChaseHoundConfig(tunableParams=params)


def _collect_results(temp_folder: str | Path) -> List[Dict[str, Any]]:
    """Retourne les contenus CSV générés par ChaseHound."""
    results: List[Dict[str, Any]] = []
    folder = Path(temp_folder)
    if not folder.exists():
        return results

    for csv_path in sorted(folder.glob("*_results.csv")):
        try:
            df = pd.read_csv(csv_path)
            results.append({"file": csv_path.name, "records": df.to_dict(orient="records")})
        except Exception as exc:  # noqa: BLE001
            results.append({"file": csv_path.name, "error": str(exc)})
    return results

###############################################################################
# Routes
###############################################################################

@app.route("/run", methods=["POST"])
def run_chasehound():
    """Endpoint principal : lance ChaseHound et renvoie les résultats."""
    started = time.time()

    # Validation du contenu
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON payload must be an object"}), 400

    # Construction de la config
    try:
        config = _build_config_from_json(payload)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Invalid configuration: {exc}"}), 400

    # Exécution principale
    try:
        engine = ChaseHoundMain(config)
        engine.run()
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Execution failed: {exc}"}), 500

    # Collecte des résultats
    results = _collect_results(Path(engine.temp_folder))
    elapsed = round(time.time() - started, 2)

    print(f"{Colors.GREEN}🐾 ChaseHound Backend Server completed in {elapsed / 60:0.2f} minutes{Colors.ENDC}")

    return jsonify(
        {
            "status": "completed",
            "execution_time": elapsed,
            "generated": datetime.utcnow().isoformat(),
            "results_count": sum(len(r.get("records", [])) for r in results),
            "results": results,
        }
    )


if __name__ == "__main__":
    # Support for environment variables in production
    host = os.getenv("CHASEHOUND_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("CHASEHOUND_PORT", "8000")))  # App Engine uses PORT
    debug = os.getenv("CHASEHOUND_DEBUG", "False").lower() == "true"
    
    print(f"🐾 ChaseHound Backend Server starting on {host}:{port}")
    app.run(host=host, port=port, debug=debug) 