"""
ChaseHound Backend - Google App Engine Entry Point (racine)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from flask import jsonify

# Ajoute la racine du projet au PYTHONPATH (l  ichier est déjà à la racine)
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Importe l'application Flask définie dans backendCDServer
from src_CD.backendCDServer import app  # noqa: E402, I202


@app.route("/health")
def health_check():
    """Endpoint de santé pour App Engine"""
    return jsonify({"status": "healthy", "service": "chasehound-backend"})


if __name__ == "__main__":
    # Exécution locale
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False) 