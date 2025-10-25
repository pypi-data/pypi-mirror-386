"""
Script pour explorer la base de données CLASH
"""

import pandas as pd
import numpy as np

print("="*70)
print("EXPLORATION BASE DE DONNÉES CLASH")
print("="*70)

# Charger Excel
try:
    df = pd.read_excel('Data/Database_20050101.xls')
    
    print(f"\n[OK] Fichier charge avec succes!")
    print(f"Nombre de lignes: {len(df)}")
    print(f"Nombre de colonnes: {len(df.columns)}")
    
    print("\nCOLONNES DISPONIBLES:")
    print("-" * 70)
    for i, col in enumerate(df.columns, 1):
        print(f"{i:3d}. {col}")
    
    print("\nSTATISTIQUES DESCRIPTIVES (premieres colonnes):")
    print("-" * 70)
    print(df.describe().iloc[:, :10])
    
    print("\nAPERCU DES DONNEES (5 premieres lignes):")
    print("-" * 70)
    print(df.head())
    
    print("\nSAUVEGARDE INFO COLONNES:")
    with open('Data/clash_columns.txt', 'w', encoding='utf-8') as f:
        f.write("COLONNES BASE CLASH\n")
        f.write("="*70 + "\n\n")
        for i, col in enumerate(df.columns, 1):
            f.write(f"{i:3d}. {col}\n")
    print("Info sauvegardée dans: Data/clash_columns.txt")
    
except FileNotFoundError:
    print("[ERROR] Fichier non trouve: Data/Database_20050101.xls")
except Exception as e:
    print(f"[ERROR] Erreur: {e}")

