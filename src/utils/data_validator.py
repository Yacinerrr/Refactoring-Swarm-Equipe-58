"""
Data Validator - Phase 1 : Outils du Data Manager
==================================================
Ce module fournit des outils pour valider et analyser les logs d'expérimentation.
Utilisé par le Data Manager pour garantir la qualité des données.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pandas as pd

# Chemin du fichier de logs
LOG_FILE = os.path.join("logs", "experiment_data.json")

# ============================================================
# SCHÉMA DE DONNÉES OBLIGATOIRE
# ============================================================

REQUIRED_FIELDS = ["id", "timestamp", "agent", "model", "action", "details", "status"]
REQUIRED_DETAILS_FIELDS = ["input_prompt", "output_response"]
VALID_ACTIONS = ["CODE_ANALYSIS", "CODE_GEN", "DEBUG", "FIX"]
VALID_STATUSES = ["SUCCESS", "FAILURE", "INFO"]
VALID_AGENTS = ["Auditor", "Fixer", "Judge", "System"]


def load_logs(filepath: str = LOG_FILE) -> List[Dict]:
    """
    Charge les logs depuis le fichier JSON.
    
    Args:
        filepath: Chemin vers le fichier de logs
        
    Returns:
        Liste des entrées de logs
    """
    if not os.path.exists(filepath):
        print(f"⚠️ Fichier de logs non trouvé : {filepath}")
        return []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"❌ Erreur JSON dans {filepath}: {e}")
        return []


def validate_entry(entry: Dict, index: int) -> Tuple[bool, List[str]]:
    """
    Valide une entrée individuelle du log.
    
    Args:
        entry: L'entrée à valider
        index: L'index de l'entrée dans la liste
        
    Returns:
        Tuple (is_valid, list_of_errors)
    """
    errors = []
    
    # Vérifier les champs obligatoires de premier niveau
    for field in REQUIRED_FIELDS:
        if field not in entry:
            errors.append(f"Entrée #{index}: Champ '{field}' manquant")
    
    # Vérifier le type d'action
    if "action" in entry and entry["action"] not in VALID_ACTIONS + ["STARTUP"]:
        errors.append(f"Entrée #{index}: Action invalide '{entry.get('action')}'")
    
    # Vérifier le status
    if "status" in entry and entry["status"] not in VALID_STATUSES:
        errors.append(f"Entrée #{index}: Status invalide '{entry.get('status')}'")
    
    # Vérifier les champs obligatoires dans details (sauf pour STARTUP)
    if "details" in entry and "action" in entry:
        if entry["action"] in VALID_ACTIONS:  # Pas STARTUP
            if isinstance(entry["details"], dict):
                for detail_field in REQUIRED_DETAILS_FIELDS:
                    if detail_field not in entry["details"]:
                        errors.append(f"Entrée #{index}: Champ 'details.{detail_field}' manquant (OBLIGATOIRE)")
            else:
                errors.append(f"Entrée #{index}: 'details' doit être un dictionnaire")
    
    return len(errors) == 0, errors


def validate_all_logs(filepath: str = LOG_FILE) -> Dict:
    """
    Valide toutes les entrées du fichier de logs.
    
    Returns:
        Rapport de validation complet
    """
    logs = load_logs(filepath)
    
    report = {
        "total_entries": len(logs),
        "valid_entries": 0,
        "invalid_entries": 0,
        "errors": [],
        "warnings": [],
        "is_valid": True
    }
    
    if not logs:
        report["warnings"].append("Le fichier de logs est vide")
        report["is_valid"] = False
        return report
    
    for i, entry in enumerate(logs):
        is_valid, errors = validate_entry(entry, i)
        if is_valid:
            report["valid_entries"] += 1
        else:
            report["invalid_entries"] += 1
            report["errors"].extend(errors)
            report["is_valid"] = False
    
    return report


def get_logs_summary(filepath: str = LOG_FILE) -> Dict:
    """
    Génère un résumé statistique des logs avec Pandas.
    
    Returns:
        Dictionnaire avec les statistiques
    """
    logs = load_logs(filepath)
    
    if not logs:
        return {"error": "Aucun log trouvé"}
    
    df = pd.DataFrame(logs)
    
    summary = {
        "total_entries": len(df),
        "agents": {},
        "actions": {},
        "statuses": {},
        "date_range": {}
    }
    
    # Statistiques par agent
    if "agent" in df.columns:
        summary["agents"] = df["agent"].value_counts().to_dict()
    
    # Statistiques par action
    if "action" in df.columns:
        summary["actions"] = df["action"].value_counts().to_dict()
    
    # Statistiques par status
    if "status" in df.columns:
        summary["statuses"] = df["status"].value_counts().to_dict()
    
    # Plage de dates
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        summary["date_range"] = {
            "first": df["timestamp"].min().isoformat(),
            "last": df["timestamp"].max().isoformat()
        }
    
    return summary


def check_completeness(filepath: str = LOG_FILE) -> Dict:
    """
    Vérifie que tous les agents requis ont des entrées.
    
    Returns:
        Rapport de complétude
    """
    logs = load_logs(filepath)
    required_agents = ["Auditor", "Fixer", "Judge"]
    
    df = pd.DataFrame(logs) if logs else pd.DataFrame()
    
    present_agents = df["agent"].unique().tolist() if "agent" in df.columns else []
    
    report = {
        "required_agents": required_agents,
        "present_agents": present_agents,
        "missing_agents": [a for a in required_agents if a not in present_agents],
        "is_complete": all(a in present_agents for a in required_agents)
    }
    
    return report


def print_validation_report(filepath: str = LOG_FILE):
    """
    Affiche un rapport de validation complet et formaté.
    """
    print("\n" + "="*60)
    print("📊 RAPPORT DE VALIDATION DES LOGS - DATA MANAGER")
    print("="*60)
    
    # 1. Validation du format
    print("\n🔍 1. VALIDATION DU FORMAT JSON")
    print("-"*40)
    validation = validate_all_logs(filepath)
    
    print(f"   Total entrées    : {validation['total_entries']}")
    print(f"   Entrées valides  : {validation['valid_entries']} ✅")
    print(f"   Entrées invalides: {validation['invalid_entries']} {'❌' if validation['invalid_entries'] > 0 else ''}")
    
    if validation['errors']:
        print("\n   ❌ Erreurs détectées:")
        for error in validation['errors'][:10]:  # Limiter à 10 erreurs
            print(f"      - {error}")
        if len(validation['errors']) > 10:
            print(f"      ... et {len(validation['errors']) - 10} autres erreurs")
    
    if validation['warnings']:
        print("\n   ⚠️ Avertissements:")
        for warning in validation['warnings']:
            print(f"      - {warning}")
    
    # 2. Résumé statistique
    print("\n📈 2. STATISTIQUES")
    print("-"*40)
    summary = get_logs_summary(filepath)
    
    if "error" not in summary:
        print(f"   Total entrées: {summary['total_entries']}")
        
        print("\n   Par Agent:")
        for agent, count in summary.get('agents', {}).items():
            print(f"      - {agent}: {count}")
        
        print("\n   Par Action:")
        for action, count in summary.get('actions', {}).items():
            print(f"      - {action}: {count}")
        
        print("\n   Par Status:")
        for status, count in summary.get('statuses', {}).items():
            emoji = "✅" if status == "SUCCESS" else "❌" if status == "FAILURE" else "ℹ️"
            print(f"      - {status}: {count} {emoji}")
    
    # 3. Vérification de complétude
    print("\n✅ 3. COMPLÉTUDE")
    print("-"*40)
    completeness = check_completeness(filepath)
    
    print(f"   Agents requis : {completeness['required_agents']}")
    print(f"   Agents présents: {completeness['present_agents']}")
    
    if completeness['missing_agents']:
        print(f"\n   ⚠️ Agents manquants: {completeness['missing_agents']}")
    else:
        print(f"\n   ✅ Tous les agents sont présents!")
    
    # 4. Verdict final
    print("\n" + "="*60)
    if validation['is_valid'] and completeness['is_complete']:
        print("🎉 VERDICT: LOGS VALIDES ET COMPLETS")
    elif validation['is_valid']:
        print("⚠️ VERDICT: FORMAT VALIDE MAIS INCOMPLET")
    else:
        print("❌ VERDICT: LOGS INVALIDES - CORRECTIONS NÉCESSAIRES")
    print("="*60 + "\n")


# ============================================================
# POINT D'ENTRÉE POUR TEST
# ============================================================

if __name__ == "__main__":
    print_validation_report()
