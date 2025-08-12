# 🚀 ChaseHound CI/CD Pipeline

Ce document explique le système de CI/CD (Continuous Integration/Continuous Deployment) de ChaseHound qui automatise l'analyse boursière et le déploiement des résultats.

## 📋 Vue d'ensemble

Le pipeline CI/CD de ChaseHound fonctionne comme suit :

1. **Déclenchement automatique** : À chaque commit sur `main`/`master`
2. **Exécution de l'analyse** : Lancement automatique de ChaseHound avec des paramètres optimisés
3. **Génération du site** : Création d'un site statique avec les résultats
4. **Déploiement** : Publication automatique sur GitHub Pages

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Git Commit    │───▶│  GitHub Actions │───▶│  GitHub Pages   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ ChaseHound Run  │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ Static Website  │
                       │   Generation    │
                       └─────────────────┘
```

## 📁 Structure des fichiers

```
chaseHound/
├── .github/
│   └── workflows/
│       └── chasehound-ci.yml          # Workflow GitHub Actions
├── config/
│   └── ci_config.yaml                 # Configuration CI
├── scripts/
│   ├── run_chasehound_ci.py          # Script d'exécution CI
│   └── generate_static_site.py       # Générateur de site statique
└── docs/                              # Site statique généré
    └── index.html
```

## ⚙️ Configuration

### Fichier de configuration CI (`config/ci_config.yaml`)

Ce fichier contient les paramètres optimisés pour l'exécution automatisée :

```yaml
chasehound:
  # Paramètres de date
  start_date: "2024-01-01"
  end_date: "2024-12-31"
  
  # Filtres fondamentaux (plus permissifs)
  lowest_market_gap: 10000000
  lowest_avg_turnover: 10000000
  # ... autres paramètres
```

### Personnalisation

Pour modifier les paramètres d'analyse :

1. Éditez `config/ci_config.yaml`
2. Committez les changements
3. Le pipeline se relancera automatiquement

## 🔄 Workflow GitHub Actions

### Déclencheurs

- **Push** sur `main` ou `master`
- **Pull Request** vers `main` ou `master`
- **Manuel** via l'interface GitHub Actions

### Étapes du workflow

1. **Setup** : Installation de Python et des dépendances
2. **Run ChaseHound** : Exécution de l'analyse avec configuration CI
3. **Generate Website** : Création du site statique
4. **Deploy** : Déploiement sur GitHub Pages

## 🌐 Site statique généré

### Fonctionnalités

- **Design moderne** : Interface responsive avec gradient et animations
- **Données tabulaires** : Affichage des résultats CSV avec pagination
- **Graphiques** : Visualisation des graphiques générés
- **Téléchargements** : Boutons de téléchargement pour tous les fichiers
- **Statistiques** : Résumé des données analysées

### Accès

Le site est accessible à l'adresse : `https://[username].github.io/[repository-name]`

## 🛠️ Développement local

### Tester le pipeline localement

```bash
# Installer les dépendances
pip install -r requirements.txt

# Exécuter ChaseHound avec configuration CI
python scripts/run_chasehound_ci.py

# Générer le site statique
python scripts/generate_static_site.py results docs

# Visualiser le site (optionnel)
python -m http.server 8000
# Puis ouvrir http://localhost:8000/docs/
```

### Modifier le design du site

Éditez le fichier `scripts/generate_static_site.py` pour personnaliser :

- Le template HTML
- Les styles CSS
- La logique d'affichage des données

## 📊 Monitoring et logs

### Accès aux logs

1. Allez sur votre repository GitHub
2. Cliquez sur l'onglet "Actions"
3. Sélectionnez le workflow "ChaseHound CI/CD Pipeline"
4. Cliquez sur la dernière exécution pour voir les logs

### Artifacts

Les résultats sont sauvegardés comme artifacts GitHub Actions :

- **Rétention** : 30 jours
- **Contenu** : Fichiers CSV et graphiques PNG
- **Accès** : Via l'interface GitHub Actions

## 🔧 Dépannage

### Problèmes courants

1. **Timeout** : L'analyse prend trop de temps
   - Solution : Ajuster les paramètres dans `ci_config.yaml`

2. **Erreurs de dépendances** : Packages manquants
   - Solution : Vérifier `requirements.txt`

3. **Échec de déploiement** : Problème GitHub Pages
   - Solution : Vérifier les permissions du repository

### Logs d'erreur

Les erreurs sont affichées dans les logs GitHub Actions avec des emojis colorés :
- ✅ Succès
- ❌ Erreur
- ⚠️ Avertissement
- ℹ️ Information

## 🚀 Optimisations futures

### Améliorations possibles

1. **Notifications** : Intégration Discord/Slack
2. **Cache** : Mise en cache des données pour accélérer
3. **Tests** : Ajout de tests automatisés
4. **Monitoring** : Métriques de performance
5. **Backup** : Sauvegarde des résultats historiques

### Configuration avancée

Pour des besoins spécifiques, vous pouvez :

- Modifier le workflow GitHub Actions
- Ajouter des étapes personnalisées
- Intégrer d'autres services (AWS, GCP, etc.)
- Personnaliser le design du site

## 📞 Support

Pour toute question ou problème :

1. Vérifiez les logs GitHub Actions
2. Consultez la documentation ChaseHound
3. Ouvrez une issue sur le repository

---

**Note** : Ce système CI/CD remplace efficacement l'utilisation de GCP pour le déploiement, en utilisant uniquement GitHub Actions et GitHub Pages. 