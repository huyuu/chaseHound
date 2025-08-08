# ChaseHound Backend Deployment (GitHub Bootstrap)

Ce dossier contient tous les fichiers nécessaires pour déployer le backend ChaseHound sur Google App Engine en utilisant l'approche "GitHub Bootstrap".

## 🚀 Principe

Au lieu d'uploader tous les 70,000+ fichiers du projet, cette solution :
1. **Upload minimal** : Seulement 4 fichiers essentiels
2. **Clone GitHub** : Le serveur clone automatiquement votre repository au démarrage
3. **Installation auto** : Installe les dépendances du projet depuis `requirements.txt`

## 📁 Fichiers

- **`backend_main.py`** : Point d'entrée avec logique de clonage GitHub
- **`backend_app.yaml`** : Configuration App Engine
- **`requirements.txt`** : Dépendances minimales pour le bootstrap
- **`.gcloudignore`** : Exclut tout sauf les fichiers essentiels
- **`deploy.py`** : Script de déploiement intelligent
- **`README.md`** : Cette documentation

## 🛠️ Prérequis

1. **Google Cloud CLI** installé et configuré
2. **Repository GitHub** accessible (public ou avec permissions)
3. **Python 3.11+** pour le script de déploiement

## 📋 Instructions de déploiement

### 1. Préparer votre repository GitHub

```bash
# Commitez et poussez votre code
git add .
git commit -m "Prepare for GitHub bootstrap deployment"
git push origin main
```

### 2. Naviguer vers le dossier backend

```bash
cd src_CD/backend
```

### 3. Déployer avec votre URL GitHub

```bash
# Remplacez YOUR_USERNAME par votre nom d'utilisateur GitHub
python deploy.py --github-repo https://github.com/YOUR_USERNAME/chaseHound.git

# Ou avec des options personnalisées
python deploy.py \
  --github-repo https://github.com/YOUR_USERNAME/chaseHound.git \
  --branch main \
  --project-id votre-projet-gcp \
  --region asia-northeast1
```

### 4. Vérifier le déploiement

Après le déploiement, testez les endpoints :

- **Health Check** : `https://votre-projet.appspot.com/health`
- **Info** : `https://votre-projet.appspot.com/info`
- **API principale** : `https://votre-projet.appspot.com/run`

## 🔧 Options du script de déploiement

```bash
python deploy.py --help
```

- `--github-repo` : URL du repository GitHub
- `--branch` : Branche à utiliser (défaut: main)
- `--project-id` : ID du projet Google Cloud
- `--region` : Région App Engine (défaut: asia-northeast1)

## 🐛 Dépannage

### Repository non trouvé
- Vérifiez que le repository est public ou que vous avez configuré les permissions
- Vérifiez l'URL du repository

### Import errors
- Vérifiez que `src_CD/backendCDServer.py` existe dans votre repository
- Vérifiez que `requirements.txt` contient toutes les dépendances nécessaires

### Limite de fichiers
- Cette solution résout le problème ! Seulement 4 fichiers sont uploadés

## 📊 Avantages

✅ **Résout la limite de 10,000 fichiers**  
✅ **Déploiement ultra-rapide** (quelques secondes)  
✅ **Toujours à jour** (utilise la dernière version du repo)  
✅ **Gestion d'erreurs robuste**  
✅ **Messages colorés et informatifs**  
✅ **Endpoints de diagnostic** (/health, /info)  

## 🔄 Workflow typique

1. Développez votre code localement
2. Commitez et poussez sur GitHub
3. Exécutez `python deploy.py --github-repo VOTRE_REPO`
4. Testez l'API déployée

C'est tout ! Le backend clone automatiquement la dernière version de votre code à chaque redémarrage. 