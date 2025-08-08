#!/usr/bin/env python3
"""
ChaseHound Frontend Deployment Script
=====================================

Ce script déploie le frontend ChaseHound sur Google App Engine.
Le frontend est une application Streamlit qui communique avec le backend.

Usage:
    cd src_CD/frontend
    python deploy.py [--backend-project BACKEND_ID] [--frontend-project FRONTEND_ID]

Prérequis:
    - gcloud CLI installé et configuré
    - Backend déjà déployé pour obtenir l'URL de l'API
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Configuration par défaut
DEFAULT_FRONTEND_PROJECT_ID = "chasehoundfrontend"
DEFAULT_BACKEND_PROJECT_ID = "chasehoundbackend"
DEFAULT_REGION = "asia-northeast1"

# Couleurs pour les messages [[memory:5394581]]
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m' 
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def print_status(level: str, message: str):
    """Affiche un message avec couleur selon le niveau"""
    color = {
        'SUCCESS': Colors.GREEN,
        'ERROR': Colors.RED,
        'WARNING': Colors.YELLOW,
        'INFO': Colors.CYAN
    }.get(level, '')
    print(f"{color}[{level}]{Colors.RESET} {message}")

def run_command(cmd: list, description: str) -> bool:
    """Exécute une commande et gère les erreurs"""
    print_status('INFO', f"{description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout.strip():
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print_status('ERROR', f"{description} failed")
        if e.stderr:
            print(e.stderr)
        return False

def update_frontend_app_yaml(backend_project_id: str):
    """Met à jour frontend_app.yaml avec l'ID du projet backend"""
    frontend_app_yaml_path = Path("frontend_app.yaml")
    if not frontend_app_yaml_path.exists():
        print_status('ERROR', "frontend_app.yaml not found")
        return False
    
    try:
        with open(frontend_app_yaml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer le placeholder par l'ID du projet backend
        content = content.replace('BACKEND_PROJECT_ID', backend_project_id)
        
        with open(frontend_app_yaml_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print_status('SUCCESS', f"frontend_app.yaml updated with backend project: {backend_project_id}")
        return True
        
    except Exception as e:
        print_status('ERROR', f"Failed to update frontend_app.yaml: {e}")
        return False

def check_files():
    """Vérifie que tous les fichiers nécessaires sont présents"""
    required_files = ['frontend_main.py', 'frontend_app.yaml', 'frontend_requirements.txt', 'chaseHoundStreamLitApp.py']
    missing_files = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print_status('ERROR', f"Required files missing: {', '.join(missing_files)}")
        return False
    
    print_status('SUCCESS', "All required files present")
    return True

def deploy_frontend(frontend_project_id: str, backend_project_id: str, region: str) -> bool:
    """Déploie le frontend sur App Engine"""
    
    print("=" * 80)
    print_status('INFO', "ChaseHound Frontend Deployment")
    print("=" * 80)
    print(f"🎨 Frontend Project ID: {frontend_project_id}")
    print(f"🔗 Backend Project ID: {backend_project_id}")
    print(f"🌍 Region: {region}")
    print(f"📁 Working Directory: {os.getcwd()}")
    print("=" * 80)
    
    # Étape 1: Vérification des fichiers
    if not check_files():
        return False
    
    # Étape 2: Configuration du projet frontend
    if not run_command(
        ['gcloud', 'config', 'set', 'project', frontend_project_id],
        f"Setting project to {frontend_project_id}"
    ):
        return False
    
    # Étape 3: Activation des APIs
    if not run_command(
        ['gcloud', 'services', 'enable', 'appengine.googleapis.com', 'cloudbuild.googleapis.com'],
        "Enabling required APIs"
    ):
        return False
    
    # Étape 4: Création de l'application App Engine (si nécessaire)
    print_status('INFO', "Creating App Engine application...")
    result = subprocess.run(
        ['gcloud', 'app', 'create', f'--region={region}'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        if "already contains" in result.stderr:
            print_status('WARNING', "App Engine application already exists")
        else:
            print_status('ERROR', f"Failed to create App Engine application: {result.stderr}")
            return False
    else:
        print_status('SUCCESS', "App Engine application created")
    
    # Étape 5: Mise à jour de la configuration frontend
    if not update_frontend_app_yaml(backend_project_id):
        return False
    
    # Étape 6: Déploiement
    if not run_command(
        ['gcloud', 'app', 'deploy', 'frontend_app.yaml', '--quiet'],
        "Deploying frontend service"
    ):
        return False
    
    # Succès !
    frontend_url = f"https://{frontend_project_id}.appspot.com"
    backend_url = f"https://{backend_project_id}.appspot.com"
    
    print()
    print("=" * 80)
    print_status('SUCCESS', "🎉 ChaseHound Frontend deployment completed!")
    print("=" * 80)
    print_status('SUCCESS', f"🎨 Frontend URL: {frontend_url}")
    print_status('INFO', f"🔗 Backend URL: {backend_url}")
    print_status('INFO', f"📋 Health Check: {frontend_url}/health")
    print_status('INFO', "🎯 The frontend will automatically connect to the backend")
    print("=" * 80)
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Deploy ChaseHound Frontend to Google App Engine"
    )
    parser.add_argument(
        '--frontend-project', 
        default=DEFAULT_FRONTEND_PROJECT_ID,
        help=f"Google Cloud Project ID for frontend (default: {DEFAULT_FRONTEND_PROJECT_ID})"
    )
    parser.add_argument(
        '--backend-project',
        default=DEFAULT_BACKEND_PROJECT_ID,
        help=f"Google Cloud Project ID for backend (default: {DEFAULT_BACKEND_PROJECT_ID})"
    )
    parser.add_argument(
        '--region',
        default=DEFAULT_REGION,
        help=f"App Engine region (default: {DEFAULT_REGION})"
    )
    
    args = parser.parse_args()
    
    # Vérification que nous sommes dans le bon dossier
    if not Path("frontend_main.py").exists():
        print_status('ERROR', "frontend_main.py not found. Please run this script from src_CD/frontend/")
        return False
    
    success = deploy_frontend(
        args.frontend_project,
        args.backend_project, 
        args.region
    )
    
    if success:
        print_status('SUCCESS', "🎉 Deployment completed successfully!")
        return True
    else:
        print_status('ERROR', "❌ Deployment failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 