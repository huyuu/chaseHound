"""
ChaseHound Backend - Google App Engine Entry Point
==================================================

Ce fichier est le point d'entrée pour le backend ChaseHound déployé sur App Engine.
Il utilise l'approche "GitHub Bootstrap" pour cloner le projet complet au runtime.
"""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path

from flask import jsonify, Flask

# Configuration GitHub
GITHUB_REPO = "https://github.com/YOUR_USERNAME/chaseHound.git"  # À remplacer par votre repo
GITHUB_BRANCH = "main"
PROJECT_DIR = "/tmp/chasehound"

def setup_project():
    """Clone le projet depuis GitHub et installe les dépendances"""
    if not os.path.exists(PROJECT_DIR):
        print("🔄 Cloning repository from GitHub...")
        try:
            # Clone le repository
            subprocess.run([
                "git", "clone", "-b", GITHUB_BRANCH, 
                GITHUB_REPO, PROJECT_DIR
            ], check=True, capture_output=True, text=True)
            
            # Ajouter le projet au PYTHONPATH
            sys.path.insert(0, PROJECT_DIR)
            
            # Installer les dépendances Python du projet principal
            requirements_path = os.path.join(PROJECT_DIR, "requirements.txt")
            if os.path.exists(requirements_path):
                print("📦 Installing project dependencies...")
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", requirements_path
                ], check=True)
                
            print("✅ Project setup completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error setting up project: {e}")
            if e.stderr:
                print(f"Error details: {e.stderr}")
            return False
    else:
        # Le projet existe déjà, juste l'ajouter au PYTHONPATH
        sys.path.insert(0, PROJECT_DIR)
        print("✅ Project already cloned, reusing existing setup")
        return True

# Configuration initiale
print("🚀 ChaseHound Backend starting...")
setup_success = setup_project()

if setup_success:
    try:
        # Importe l'application Flask depuis le projet cloné
        print("🔗 Loading ChaseHound application...")
        from src_CD.backendCDServer import app
        print("✅ ChaseHound application loaded successfully")
    except ImportError as e:
        print(f"❌ Failed to import app: {e}")
        # Créer une app Flask de fallback
        app = Flask(__name__)
        
        @app.route("/")
        def fallback():
            return jsonify({
                "error": "Failed to load ChaseHound application", 
                "details": str(e),
                "github_repo": GITHUB_REPO,
                "github_branch": GITHUB_BRANCH
            })
else:
    # Créer une app Flask de fallback
    app = Flask(__name__)
    
    @app.route("/")
    def fallback():
        return jsonify({
            "error": "Failed to setup project from GitHub",
            "github_repo": GITHUB_REPO,
            "github_branch": GITHUB_BRANCH,
            "help": "Check if the GitHub repository is accessible and contains the required files"
        })

@app.route("/health")
def health_check():
    """Endpoint de santé pour App Engine"""
    return jsonify({
        "status": "healthy", 
        "service": "chasehound-backend",
        "project_loaded": setup_success,
        "github_repo": GITHUB_REPO,
        "github_branch": GITHUB_BRANCH,
        "project_dir": PROJECT_DIR
    })

@app.route("/info")
def info():
    """Informations sur le déploiement"""
    return jsonify({
        "service": "ChaseHound Backend",
        "deployment_type": "GitHub Bootstrap",
        "github_repo": GITHUB_REPO,
        "github_branch": GITHUB_BRANCH,
        "project_loaded": setup_success,
        "project_dir": PROJECT_DIR,
        "python_path": sys.path[:3]  # Premiers éléments du PYTHONPATH
    })

if __name__ == "__main__":
    # Exécution locale pour tests
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False) 