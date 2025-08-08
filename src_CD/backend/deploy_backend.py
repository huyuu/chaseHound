#!/usr/bin/env python3
"""
ChaseHound Backend Deployment Script (GitHub Bootstrap)
=======================================================

Ce script déploie le backend ChaseHound sur Google App Engine en utilisant
une approche "bootstrap" : seuls les fichiers minimaux sont uploadés,
le code complet est cloné depuis GitHub au runtime.

Usage:
    cd src_CD/backend
    python deploy.py [--github-repo URL] [--branch BRANCH] [--project-id ID]

Prérequis:
    - gcloud CLI installé et configuré
    - Repository GitHub accessible publiquement ou avec les bonnes permissions
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Configuration par défaut
DEFAULT_PROJECT_ID = "chasehoundbackend"
DEFAULT_REGION = "asia-northeast1"
DEFAULT_GITHUB_REPO = "https://github.com/YOUR_USERNAME/chaseHound.git"  # À remplacer
DEFAULT_BRANCH = "main"

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

def update_backend_main_py(github_repo: str, branch: str):
    """Met à jour backend_main.py avec les bonnes URLs GitHub"""
    backend_main_py_path = Path("backend_main.py")
    if not backend_main_py_path.exists():
        print_status('ERROR', "backend_main.py not found")
        return False
    
    try:
        with open(backend_main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer les variables GitHub
        content = content.replace(
            'GITHUB_REPO = "https://github.com/YOUR_USERNAME/chaseHound.git"',
            f'GITHUB_REPO = "{github_repo}"'
        )
        content = content.replace(
            'GITHUB_BRANCH = "main"',
            f'GITHUB_BRANCH = "{branch}"'
        )
        
        with open(backend_main_py_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print_status('SUCCESS', "backend_main.py updated with GitHub configuration")
        return True
        
    except Exception as e:
        print_status('ERROR', f"Failed to update backend_main.py: {e}")
        return False

def check_files():
    """Vérifie que tous les fichiers nécessaires sont présents"""
    required_files = ['backend_main.py', 'backend_app.yaml', 'requirements.txt']
    missing_files = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print_status('ERROR', f"Required files missing: {', '.join(missing_files)}")
        return False
    
    print_status('SUCCESS', "All required files present")
    return True

def deploy_backend(project_id: str, region: str, github_repo: str, branch: str) -> bool:
    """Déploie le backend sur App Engine"""
    
    print("=" * 80)
    print_status('INFO', "ChaseHound Backend Deployment (GitHub Bootstrap)")
    print("=" * 80)
    print(f"📋 Project ID: {project_id}")
    print(f"🌍 Region: {region}")
    print(f"📦 GitHub Repository: {github_repo}")
    print(f"🌿 Branch: {branch}")
    print(f"📁 Working Directory: {os.getcwd()}")
    print("=" * 80)
    
    # Étape 1: Vérification des fichiers
    if not check_files():
        return False
    
    # Étape 2: Configuration du projet
    if not run_command(
        ['gcloud', 'config', 'set', 'project', project_id],
        f"Setting project to {project_id}"
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
    
    # Étape 5: Mise à jour de la configuration GitHub
    if not update_backend_main_py(github_repo, branch):
        return False
    
    # Étape 6: Déploiement
    if not run_command(
        ['gcloud', 'app', 'deploy', 'backend_app.yaml', '--quiet'],
        "Deploying backend service"
    ):
        return False
    
    # Succès !
    backend_url = f"https://{project_id}.appspot.com"
    print()
    print("=" * 80)
    print_status('SUCCESS', "🎉 ChaseHound Backend deployment completed!")
    print("=" * 80)
    print_status('SUCCESS', f"🌐 Backend URL: {backend_url}")
    print_status('INFO', f"📋 Health Check: {backend_url}/health")
    print_status('INFO', f"ℹ️  Deployment Info: {backend_url}/info")
    print_status('INFO', "🔄 The backend will clone your GitHub repository on first request")
    print_status('INFO', f"📦 Repository: {github_repo} (branch: {branch})")
    print("=" * 80)
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Deploy ChaseHound Backend with GitHub Bootstrap"
    )
    parser.add_argument(
        '--project-id', 
        default=DEFAULT_PROJECT_ID,
        help=f"Google Cloud Project ID (default: {DEFAULT_PROJECT_ID})"
    )
    parser.add_argument(
        '--region',
        default=DEFAULT_REGION,
        help=f"App Engine region (default: {DEFAULT_REGION})"
    )
    parser.add_argument(
        '--github-repo',
        default=DEFAULT_GITHUB_REPO,
        help=f"GitHub repository URL (default: {DEFAULT_GITHUB_REPO})"
    )
    parser.add_argument(
        '--branch',
        default=DEFAULT_BRANCH,
        help=f"Git branch to use (default: {DEFAULT_BRANCH})"
    )
    
    args = parser.parse_args()
    
    # Vérification que nous sommes dans le bon dossier
    if not Path("backend_main.py").exists():
        print_status('ERROR', "backend_main.py not found. Please run this script from src_CD/backend/")
        return False
    
    # Vérification que l'URL GitHub a été configurée
    if "YOUR_USERNAME" in args.github_repo:
        print_status('ERROR', "Please configure your GitHub repository URL")
        print_status('INFO', "Use: python deploy.py --github-repo https://github.com/YOUR_USERNAME/chaseHound.git")
        return False
    
    success = deploy_backend(
        args.project_id,
        args.region, 
        args.github_repo,
        args.branch
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