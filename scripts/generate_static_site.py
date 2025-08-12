#!/usr/bin/env python3
"""
Script de génération du site statique pour ChaseHound
Génère un site HTML à partir des résultats d'analyse
"""

import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil

def generate_static_site(results_dir: str = "results", output_dir: str = "docs"):
    """
    Génère un site statique à partir des résultats ChaseHound
    
    Args:
        results_dir: Répertoire contenant les résultats
        output_dir: Répertoire de sortie pour le site
    """
    
    # Créer le répertoire de sortie
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Template HTML avec design moderne
    html_template = '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🐾 ChaseHound - Résultats d'analyse</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        
        h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            color: #7f8c8d;
            font-size: 1.1em;
            margin-bottom: 20px;
        }
        
        .status {
            padding: 15px 20px;
            border-radius: 10px;
            margin: 20px 0;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .success {
            background: linear-gradient(135deg, #d4edda, #c3e6cb);
            color: #155724;
            border-left: 4px solid #28a745;
        }
        
        .info {
            background: linear-gradient(135deg, #d1ecf1, #bee5eb);
            color: #0c5460;
            border-left: 4px solid #17a2b8;
        }
        
        .warning {
            background: linear-gradient(135deg, #fff3cd, #ffeaa7);
            color: #856404;
            border-left: 4px solid #ffc107;
        }
        
        .content-section {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        h2 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        
        h3 {
            color: #34495e;
            margin: 20px 0 15px 0;
            font-size: 1.4em;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        
        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        
        th {
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            font-weight: 600;
            color: #495057;
        }
        
        tr:hover {
            background-color: #f8f9fa;
            transform: scale(1.01);
            transition: all 0.2s ease;
        }
        
        .download-btn {
            display: inline-block;
            padding: 12px 24px;
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            text-decoration: none;
            border-radius: 25px;
            margin: 10px 5px;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
        }
        
        .download-btn:hover {
            background: linear-gradient(135deg, #2980b9, #1f5f8b);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(52, 152, 219, 0.4);
        }
        
        .image-container {
            text-align: center;
            margin: 30px 0;
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        
        .image-container img {
            max-width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
            transition: transform 0.3s ease;
        }
        
        .image-container img:hover {
            transform: scale(1.02);
        }
        
        .timestamp {
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 20px;
            text-align: center;
            font-style: italic;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header, .content-section {
                padding: 20px;
            }
            
            h1 {
                font-size: 2em;
            }
            
            table {
                font-size: 0.9em;
            }
            
            th, td {
                padding: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐾 ChaseHound</h1>
            <p class="subtitle">Système d'analyse et de screening boursier automatisé</p>
            
            <div class="status success">
                <span>✅</span>
                <span>Analyse terminée avec succès</span>
            </div>
            
            <div class="timestamp">
                Dernière mise à jour : {timestamp}
            </div>
        </div>
        
        {content}
    </div>
</body>
</html>'''
    
    def generate_content():
        """Génère le contenu HTML du site"""
        content_parts = []
        
        # Statistiques globales
        stats = {
            'csv_files': 0,
            'image_files': 0,
            'total_records': 0
        }
        
        # Chercher les fichiers CSV
        csv_files = list(Path(results_dir).glob('*.csv'))
        stats['csv_files'] = len(csv_files)
        
        if csv_files:
            content_parts.append('<div class="content-section">')
            content_parts.append('<h2>📊 Données d\'analyse</h2>')
            
            for csv_file in csv_files:
                try:
                    df = pd.read_csv(csv_file)
                    stats['total_records'] += len(df)
                    
                    content_parts.append(f'<h3>{csv_file.stem.replace("_", " ").title()}</h3>')
                    content_parts.append(f'<p><strong>Nombre d\'enregistrements :</strong> {len(df):,}</p>')
                    
                    # Afficher les premières lignes
                    if len(df) > 0:
                        content_parts.append('<div style="overflow-x: auto;">')
                        content_parts.append('<table>')
                        content_parts.append('<thead><tr>')
                        for col in df.columns:
                            content_parts.append(f'<th>{col.replace("_", " ").title()}</th>')
                        content_parts.append('</tr></thead>')
                        content_parts.append('<tbody>')
                        
                        for _, row in df.head(10).iterrows():
                            content_parts.append('<tr>')
                            for col in df.columns:
                                value = row[col]
                                # Formater les nombres
                                if isinstance(value, (int, float)):
                                    if isinstance(value, float):
                                        value = f"{value:.2f}"
                                    else:
                                        value = f"{value:,}"
                                content_parts.append(f'<td>{value}</td>')
                            content_parts.append('</tr>')
                        
                        if len(df) > 10:
                            content_parts.append(f'<tr><td colspan="{len(df.columns)}" style="text-align: center; font-style: italic; color: #7f8c8d;">... et {len(df) - 10:,} autres lignes</td></tr>')
                        
                        content_parts.append('</tbody></table>')
                        content_parts.append('</div>')
                        
                        # Bouton de téléchargement
                        content_parts.append(f'<a href="{csv_file.name}" class="download-btn" download>📥 Télécharger {csv_file.name}</a>')
                    else:
                        content_parts.append('<div class="status warning">Aucune donnée trouvée</div>')
                        
                except Exception as e:
                    content_parts.append(f'<div class="status warning">Erreur lors de la lecture de {csv_file.name}: {str(e)}</div>')
            
            content_parts.append('</div>')
        else:
            content_parts.append('<div class="content-section">')
            content_parts.append('<div class="status info">Aucun fichier CSV trouvé dans les résultats</div>')
            content_parts.append('</div>')
        
        # Chercher les images
        image_files = list(Path(results_dir).glob('*.png')) + list(Path(results_dir).glob('*.jpg'))
        stats['image_files'] = len(image_files)
        
        if image_files:
            content_parts.append('<div class="content-section">')
            content_parts.append('<h2>📈 Graphiques et visualisations</h2>')
            
            for img_file in image_files:
                content_parts.append(f'<div class="image-container">')
                content_parts.append(f'<h3>{img_file.stem.replace("_", " ").title()}</h3>')
                content_parts.append(f'<img src="{img_file.name}" alt="{img_file.stem}">')
                content_parts.append(f'<br><a href="{img_file.name}" class="download-btn" download>📥 Télécharger {img_file.name}</a>')
                content_parts.append('</div>')
            
            content_parts.append('</div>')
        
        # Ajouter les statistiques en haut
        if stats['csv_files'] > 0 or stats['image_files'] > 0:
            stats_html = '<div class="content-section">'
            stats_html += '<h2>📈 Statistiques</h2>'
            stats_html += '<div class="stats-grid">'
            stats_html += f'<div class="stat-card"><div class="stat-number">{stats["csv_files"]}</div><div class="stat-label">Fichiers CSV</div></div>'
            stats_html += f'<div class="stat-card"><div class="stat-number">{stats["image_files"]}</div><div class="stat-label">Graphiques</div></div>'
            stats_html += f'<div class="stat-card"><div class="stat-number">{stats["total_records"]:,}</div><div class="stat-label">Enregistrements totaux</div></div>'
            stats_html += '</div></div>'
            
            # Insérer les stats au début
            content_parts.insert(0, stats_html)
        
        return '\n'.join(content_parts)
    
    # Générer le contenu
    content = generate_content()
    timestamp = datetime.now().strftime('%d/%m/%Y à %H:%M:%S')
    
    # Écrire le fichier HTML
    with open(output_path / 'index.html', 'w', encoding='utf-8') as f:
        f.write(html_template.format(content=content, timestamp=timestamp))
    
    # Copier les fichiers de résultats
    results_path = Path(results_dir)
    if results_path.exists():
        for file_path in results_path.glob('*'):
            if file_path.is_file():
                shutil.copy2(file_path, output_path / file_path.name)
    
    print(f'✅ Site statique généré avec succès dans {output_dir}/')
    print(f'📁 Fichiers copiés depuis {results_dir}/')

if __name__ == "__main__":
    import sys
    
    # Arguments en ligne de commande
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "results"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "docs"
    
    generate_static_site(results_dir, output_dir) 