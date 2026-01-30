"""
Refactoring State - Définition de l'état partagé pour LangGraph
================================================================
Ce module définit la structure de données partagée entre tous les agents.
"""

from typing import TypedDict, List, Optional, Dict, Any
from dataclasses import dataclass, field


class RefactoringState(TypedDict):
    """
    État partagé entre tous les agents du système de refactoring.
    
    Cet état est passé à chaque nœud du graphe et peut être modifié
    par chaque agent pour communiquer avec les autres.
    """
    
    # Configuration initiale
    sandbox_dir: str  # Chemin du dossier sandbox à traiter
    max_iterations: int  # Nombre maximum d'itérations (défaut: 10)
    
    # État de l'audit
    audit_complete: bool  # L'audit a-t-il été réalisé?
    audit_plan: Optional[Dict[str, Any]]  # Plan de refactoring de l'Auditor
    files_to_fix: List[str]  # Liste des fichiers à corriger
    
    # État de la correction
    current_iteration: int  # Numéro d'itération actuel
    files_fixed: List[str]  # Fichiers déjà corrigés
    fix_history: List[Dict[str, Any]]  # Historique des corrections
    
    # État des tests
    tests_passed: bool  # Tous les tests passent-ils?
    test_results: Optional[Dict[str, Any]]  # Résultats des tests
    failing_tests: List[Dict[str, Any]]  # Liste des tests qui échouent
    
    # Contrôle du flux
    should_continue: bool  # Continuer la boucle de correction?
    mission_complete: bool  # Mission terminée avec succès?
    error_occurred: bool  # Une erreur s'est produite?
    error_message: Optional[str]  # Message d'erreur si applicable
    
    # Métadonnées
    model_used: str  # Modèle LLM utilisé (ex: "gemini-2.0-flash-exp")
    total_issues_found: int  # Nombre total de problèmes détectés
    total_issues_fixed: int  # Nombre de problèmes corrigés


def create_initial_state(sandbox_dir: str, max_iterations: int = 10) -> RefactoringState:
    """
    Crée l'état initial pour une nouvelle session de refactoring.
    
    Args:
        sandbox_dir: Chemin du dossier sandbox à traiter
        max_iterations: Nombre maximum d'itérations de la boucle
    
    Returns:
        RefactoringState: État initial
    """
    from src.config import get_model_name
    
    return RefactoringState(
        # Configuration
        sandbox_dir=sandbox_dir,
        max_iterations=max_iterations,
        
        # Audit
        audit_complete=False,
        audit_plan=None,
        files_to_fix=[],
        
        # Correction
        current_iteration=0,
        files_fixed=[],
        fix_history=[],
        
        # Tests
        tests_passed=False,
        test_results=None,
        failing_tests=[],
        
        # Flux
        should_continue=True,
        mission_complete=False,
        error_occurred=False,
        error_message=None,
        
        # Métadonnées
        model_used="gemini-2.5-flash",
        total_issues_found=0,
        total_issues_fixed=0
    )


def check_iteration_limit(state: RefactoringState) -> bool:
    """
    Vérifie si on a atteint la limite d'itérations.
    
    Args:
        state: État actuel
    
    Returns:
        bool: True si limite atteinte
    """
    return state["current_iteration"] >= state["max_iterations"]


def increment_iteration(state: RefactoringState) -> RefactoringState:
    """
    Incrémente le compteur d'itérations.
    
    Args:
        state: État actuel
    
    Returns:
        RefactoringState: État mis à jour
    """
    state["current_iteration"] += 1
    return state


def mark_mission_complete(state: RefactoringState, success: bool = True) -> RefactoringState:
    """
    Marque la mission comme terminée.
    
    Args:
        state: État actuel
        success: True si terminée avec succès
    
    Returns:
        RefactoringState: État mis à jour
    """
    state["mission_complete"] = True
    state["should_continue"] = False
    
    if not success:
        state["error_occurred"] = True
    
    return state


def add_fix_to_history(
    state: RefactoringState,
    file_path: str,
    changes: List[Dict[str, Any]]
) -> RefactoringState:
    """
    Ajoute une correction à l'historique.
    
    Args:
        state: État actuel
        file_path: Fichier corrigé
        changes: Liste des modifications appliquées
    
    Returns:
        RefactoringState: État mis à jour
    """
    state["fix_history"].append({
        "iteration": state["current_iteration"],
        "file": file_path,
        "changes": changes
    })
    
    if file_path not in state["files_fixed"]:
        state["files_fixed"].append(file_path)
    
    return state