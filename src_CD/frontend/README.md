# ChaseHound Frontend Deployment

Ce dossier contient tous les fichiers nécessaires pour déployer le frontend ChaseHound sur Google App Engine. Le frontend est une application Streamlit qui fournit une interface utilisateur pour interagir avec le backend ChaseHound.

## 🎨 Principe

Le frontend ChaseHound est une application Streamlit qui :
1. **Interface utilisateur** : Fournit une interface web intuitive
2. **Communication API** : Se connecte au backend via des appels HTTP
3. **Visualisation** : Affiche les résultats d'analyse de ChaseHound
4. **Configuration dynamique** : Se configure automatiquement avec l'URL du backend

## 📁 Fichiers

- **`frontend_main.py`** : Point d'entrée App Engine pour Streamlit
- **`frontend_app.yaml`** : Configuration App Engine
- **`frontend_requirements.txt`** : Dépendances Python pour le frontend
- **`chaseHoundStreamLitApp.py`** : Application Streamlit principale
- **`deploy.py`** : Script de déploiement intelligent
- **`README.md`** : Cette documentation

## 🛠️ Prérequis

1. **Google Cloud CLI** installé et configuré
2. **Backend déployé** : Le backend doit être déployé en premier
3. **Python 3.11+** pour le script de déploiement

## 📋 Instructions de déploiement

### 1. Déployer le backend d'abord

Le frontend a besoin de connaître l'URL du backend :

```bash
# Déployer le backend d'abord
cd src_CD/backend
python deploy.py --github-repo https://github.com/VOTRE_USERNAME/chaseHound.git
```

### 2. Naviguer vers le dossier frontend

```bash
cd ../frontend
```

### 3. Déployer le frontend

```bash
# Déploiement simple (utilise les IDs de projet par défaut)
python deploy.py

# Ou avec des IDs de projet personnalisés
python deploy.py \
  --frontend-project votre-frontend-projet \
  --backend-project votre-backend-projet \
  --region asia-northeast1
```

### 4. Vérifier le déploiement

Après le déploiement, accédez à votre frontend :

- **Application principale** : `https://votre-frontend-projet.appspot.com`
- **Health Check** : `https://votre-frontend-projet.appspot.com/health`

## 🔧 Options du script de déploiement

```bash
python deploy.py --help
```

- `--frontend-project` : ID du projet Google Cloud pour le frontend
- `--backend-project` : ID du projet Google Cloud pour le backend (pour la configuration)
- `--region` : Région App Engine (défaut: asia-northeast1)

## 🔄 Architecture

```
┌─────────────────┐    HTTP/HTTPS    ┌─────────────────┐
│   Frontend      │ ───────────────► │    Backend      │
│  (Streamlit)    │                  │   (Flask API)   │
│                 │ ◄─────────────── │                 │
└─────────────────┘    JSON API      └─────────────────┘
        │                                      │
        │                                      │
        ▼                                      ▼
┌─────────────────┐                  ┌─────────────────┐
│  App Engine     │                  │  App Engine     │
│  (Frontend)     │                  │  (Backend)      │
└─────────────────┘                  └─────────────────┘
```

## 🐛 Dépannage

### Backend non accessible
- Vérifiez que le backend est déployé et accessible
- Vérifiez l'ID du projet backend dans la commande de déploiement

### Erreurs de configuration
- Vérifiez que `frontend_app.yaml` contient la bonne URL du backend
- Le script met à jour automatiquement le placeholder `BACKEND_PROJECT_ID`

### Problèmes de dépendances
- Vérifiez que `frontend_requirements.txt` contient toutes les dépendances nécessaires
- Les versions de Streamlit doivent être compatibles avec App Engine

## 📊 Avantages

✅ **Interface utilisateur moderne** avec Streamlit  
✅ **Déploiement automatisé** avec gestion d'erreurs  
✅ **Configuration dynamique** du backend  
✅ **Messages colorés et informatifs**  
✅ **Scalabilité** avec App Engine  
✅ **Intégration complète** avec le backend ChaseHound  

## 🔄 Workflow typique

1. Développez et testez localement avec `streamlit run chaseHoundStreamLitApp.py`
2. Déployez le backend d'abord
3. Exécutez `python deploy.py` avec les bons IDs de projet
4. Testez l'application déployée

L'application frontend se connecte automatiquement au backend et fournit une interface complète pour ChaseHound ! 