#!/usr/bin/env python3
"""
Script d'exécution de ChaseHound pour CI/CD
Charge la configuration CI et lance l'analyse
"""

import sys
import os
import yaml
from pathlib import Path

# Ajouter src_python au path
sys.path.append(str(Path(__file__).parent.parent / 'src_python'))

from ChaseHoundConfig import ChaseHoundTunableParams
from ChaseHoundMain import ChaseHoundMain, ChaseHoundConfig

def load_ci_config() -> dict:
    """Charge la configuration CI depuis le fichier YAML"""
    config_path = Path(__file__).parent.parent / 'config' / 'ci_config.yaml'
    
    if not config_path.exists():
        print("⚠️  Fichier de configuration CI non trouvé, utilisation des paramètres par défaut")
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get('chasehound', {})
    except Exception as e:
        print(f"❌ Erreur lors du chargement de la configuration CI: {e}")
        return {}

def create_tunable_params_from_config(config: dict) -> ChaseHoundTunableParams:
    """Crée un objet ChaseHoundTunableParams à partir de la configuration"""
    params = ChaseHoundTunableParams()
    
    # Mapping des paramètres de configuration vers les attributs
    param_mapping = {
        'start_date': 'start_date',
        'end_date': 'end_date',
        'lowest_market_gap': 'lowest_market_gap',
        'lowest_avg_turnover': 'lowest_avg_turnover',
        'lowest_avg_turnover_days': 'lowest_avg_turnover_days',
        'lowest_price': 'lowest_price',
        'latest_report_date_days': 'latest_report_date_days',
        'turnoverSpikeThreshold': 'turnoverSpikeThreshold',
        'turnoverShortTermDays': 'turnoverShortTermDays',
        'turnoverLongTermDays': 'turnoverLongTermDays',
        'atrSpikeThreshold': 'atrSpikeThreshold',
        'atrShortTermDays': 'atrShortTermDays',
        'atrLongTermDays': 'atrLongTermDays',
        'priceStdShortTermDays': 'priceStdShortTermDays',
        'priceStdLongTermDays': 'priceStdLongTermDays',
        'priceStdSpikeThreshold': 'priceStdSpikeThreshold',
        'volatilityFiltersPassingThreshold': 'volatilityFiltersPassingThreshold',
        'breakoutDetectionDaysLookback': 'breakoutDetectionDaysLookback',
        'breakoutDetectionPriceRatioThreshold': 'breakoutDetectionPriceRatioThreshold',
        'breakoutDetectionMaTolerance': 'breakoutDetectionMaTolerance',
        'breakoutDetectionVolumeAugmentationRatioThreshold': 'breakoutDetectionVolumeAugmentationRatioThreshold',
        'structureConfirmationDaysLookback': 'structureConfirmationDaysLookback',
        'structureConfirmationMaTolerance': 'structureConfirmationMaTolerance',
        'bestTargetsN': 'bestTargetsN'
    }
    
    # Appliquer les paramètres de configuration
    for config_key, param_attr in param_mapping.items():
        if config_key in config:
            value = config[config_key]
            if hasattr(params, param_attr):
                setattr(params, param_attr, value)
                print(f"✅ {config_key}: {value}")
    
    return params

def main():
    """Fonction principale"""
    print("🚀 Démarrage de ChaseHound CI/CD")
    print("=" * 50)
    
    # Charger la configuration CI
    print("📋 Chargement de la configuration CI...")
    ci_config = load_ci_config()
    
    # Créer les paramètres tunables
    print("⚙️  Configuration des paramètres...")
    tunable_params = create_tunable_params_from_config(ci_config)
    
    # Créer la configuration ChaseHound
    print("🔧 Création de la configuration ChaseHound...")
    config = ChaseHoundConfig(tunableParams=tunable_params)
    
    # Créer et exécuter l'instance principale
    print("🎯 Lancement de l'analyse...")
    main_instance = ChaseHoundMain(config)
    
    try:
        main_instance.run()
        print("✅ Analyse ChaseHound terminée avec succès!")
        
        # Afficher un résumé des résultats
        print("\n📊 Résumé des résultats:")
        print("-" * 30)
        
        # Chercher les fichiers de résultats
        temp_dir = Path("temp")
        if temp_dir.exists():
            csv_files = list(temp_dir.glob("*.csv"))
            png_files = list(temp_dir.glob("*.png"))
            
            print(f"📄 Fichiers CSV générés: {len(csv_files)}")
            for csv_file in csv_files:
                print(f"   - {csv_file.name}")
            
            print(f"📈 Graphiques générés: {len(png_files)}")
            for png_file in png_files:
                print(f"   - {png_file.name}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 