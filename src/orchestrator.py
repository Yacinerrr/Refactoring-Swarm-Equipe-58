"""
LangGraph Orchestrator - Moteur de workflow pour le système multi-agents
=========================================================================
Ce module orchestre la collaboration entre Auditor, Fixer et Judge
en utilisant LangGraph pour gérer le flux d'exécution.
"""

from langgraph.graph import StateGraph, END
from typing import Dict, Any
import json

from src.refactoring_state import (
    RefactoringState,
    create_initial_state,
    check_iteration_limit,
    increment_iteration,
    mark_mission_complete
)
from src.agents.auditor_agent import run_auditor_agent
from src.agents.corrector_agent import run_corrector_agent
from src.agents.tester_agent import run_tester_agent


# ============================================================
# NŒUDS DU GRAPHE (Agent Functions)
# ============================================================

def auditor_node(state: RefactoringState) -> RefactoringState:
    """
    Nœud Auditor: Analyse le code et produit un plan de refactoring.
    
    Args:
        state: État actuel du système
    
    Returns:
        RefactoringState: État mis à jour avec le plan d'audit
    """
    print("\n🔍 [AUDITOR] Analyse du code en cours...")
    
    try:
        # Appeler l'agent Auditor
        result = run_auditor_agent(
            sandbox_dir=state["sandbox_dir"],
            model_used=state["model_used"]
        )
        
        # Mettre à jour l'état
        state["audit_complete"] = True
        state["audit_plan"] = result.get("refactoring_plan", {})
        state["total_issues_found"] = result.get("issues_found", 0)
        
        # Extraire la liste des fichiers à corriger
        files_to_fix = []
        if "files_to_fix" in state["audit_plan"]:
            for file_info in state["audit_plan"]["files_to_fix"]:
                files_to_fix.append(file_info["file"])
        
        state["files_to_fix"] = files_to_fix
        
        print(f"✅ [AUDITOR] {len(files_to_fix)} fichier(s) à corriger")
        print(f"   Total problèmes: {state['total_issues_found']}")
        
        # Si aucun problème trouvé, on peut terminer
        if state["total_issues_found"] == 0:
            print("✨ [AUDITOR] Aucun problème détecté!")
            state["should_continue"] = False
            state["tests_passed"] = True
        
    except Exception as e:
        print(f"❌ [AUDITOR] Erreur: {e}")
        state["error_occurred"] = True
        state["error_message"] = f"Auditor error: {str(e)}"
        state["should_continue"] = False
    
    return state


def fixer_node(state: RefactoringState) -> RefactoringState:
    """
    Nœud Fixer: Applique les corrections selon le plan d'audit.
    
    Args:
        state: État actuel du système
    
    Returns:
        RefactoringState: État mis à jour avec les corrections appliquées
    """
    print(f"\n🔧 [FIXER] Correction des fichiers (Itération {state['current_iteration'] + 1})...")
    
    try:
        # Incrémenter le compteur d'itérations
        state = increment_iteration(state)
        
        # Vérifier la limite d'itérations
        if check_iteration_limit(state):
            print(f"⚠️ [FIXER] Limite d'itérations atteinte ({state['max_iterations']})")
            state["should_continue"] = False
            state["error_occurred"] = True
            state["error_message"] = "Max iterations reached"
            return state
        
        # Récupérer le plan d'audit
        audit_plan_json = json.dumps(state["audit_plan"], indent=2, ensure_ascii=False)
        
        # Pour chaque fichier à corriger
        files_fixed_this_iteration = 0
        for file_info in state["audit_plan"].get("files_to_fix", []):
            file_path = file_info["file"]
            
            # Si on a des résultats de tests qui ont échoué, les inclure
            test_feedback = ""
            if state["failing_tests"]:
                test_feedback = "\n\n=== FEEDBACK DES TESTS ===\n"
                test_feedback += json.dumps(state["failing_tests"], indent=2, ensure_ascii=False)
            
            print(f"   📝 Correction de: {file_path}")
            
            # Appeler l'agent Fixer
            result = run_corrector_agent(
                audit_plan=audit_plan_json + test_feedback,
                target_file=file_path,
                sandbox_dir=state["sandbox_dir"],
                model_used=state["model_used"]
            )
            
            if result.get("status") == "modified":
                files_fixed_this_iteration += 1
                state["total_issues_fixed"] += len(result.get("changes", []))
        
        print(f"✅ [FIXER] {files_fixed_this_iteration} fichier(s) modifié(s)")
        
    except Exception as e:
        print(f"❌ [FIXER] Erreur: {e}")
        state["error_occurred"] = True
        state["error_message"] = f"Fixer error: {str(e)}"
        state["should_continue"] = False
    
    return state


def judge_node(state: RefactoringState) -> RefactoringState:
    """
    Nœud Judge: Exécute les tests et décide si on continue ou pas.
    
    Args:
        state: État actuel du système
    
    Returns:
        RefactoringState: État mis à jour avec les résultats des tests
    """
    print("\n⚖️ [JUDGE] Exécution des tests...")
    
    try:
        # Appeler l'agent Tester
        result = run_tester_agent(
            target_dir=state["sandbox_dir"],
            model_used=state["model_used"]
        )
        
        # Mettre à jour l'état
        state["test_results"] = result
        state["tests_passed"] = (result.get("test_status") == "success")
        state["failing_tests"] = result.get("failing_tests", [])
        
        # Décider si on continue
        if state["tests_passed"]:
            print("✅ [JUDGE] Tous les tests passent!")
            state["should_continue"] = False
            state = mark_mission_complete(state, success=True)
        else:
            print(f"❌ [JUDGE] {len(state['failing_tests'])} test(s) échoue(nt)")
            
            # Vérifier si on doit continuer
            if check_iteration_limit(state):
                print(f"⚠️ [JUDGE] Limite d'itérations atteinte, arrêt.")
                state["should_continue"] = False
                state = mark_mission_complete(state, success=False)
            else:
                print("🔁 [JUDGE] Retour au Fixer pour corrections...")
                state["should_continue"] = True
        
    except Exception as e:
        print(f"❌ [JUDGE] Erreur: {e}")
        state["error_occurred"] = True
        state["error_message"] = f"Judge error: {str(e)}"
        state["should_continue"] = False
    
    return state


# ============================================================
# FONCTIONS DE ROUTAGE (Conditional Edges)
# ============================================================

def should_continue_fixing(state: RefactoringState) -> str:
    """
    Décide si on doit continuer la boucle Fixer → Judge.
    
    Args:
        state: État actuel
    
    Returns:
        str: "continue" pour retourner au Fixer, "end" pour terminer
    """
    # Si erreur ou mission terminée, on arrête
    if state["error_occurred"] or state["mission_complete"]:
        return "end"
    
    # Si les tests passent, on termine
    if state["tests_passed"]:
        return "end"
    
    # Si on doit continuer et qu'on n'a pas atteint la limite
    if state["should_continue"] and not check_iteration_limit(state):
        return "continue"
    
    return "end"


def after_audit_routing(state: RefactoringState) -> str:
    """
    Décide quoi faire après l'audit.
    
    Args:
        state: État actuel
    
    Returns:
        str: "fix" pour aller au Fixer, "end" si rien à faire
    """
    # Si erreur, on arrête
    if state["error_occurred"]:
        return "end"
    
    # Si aucun problème trouvé, on peut sauter au Judge pour vérifier
    if state["total_issues_found"] == 0:
        return "judge"
    
    # Sinon, on va au Fixer
    return "fix"


# ============================================================
# CONSTRUCTION DU GRAPHE LANGGRAPH
# ============================================================

def build_refactoring_graph() -> StateGraph:
    """
    Construit le graphe LangGraph pour le système de refactoring.
    
    Architecture du graphe:
    
        START
          ↓
       AUDITOR ─────→ (si aucun problème) → JUDGE → END
          ↓
       FIXER
          ↓
       JUDGE ──→ (si tests OK) → END
          ↓
          └──→ (si tests KO) → FIXER (loop)
    
    Returns:
        StateGraph: Le graphe compilé
    """
    # Créer le graphe
    workflow = StateGraph(RefactoringState)
    
    # Ajouter les nœuds (agents)
    workflow.add_node("auditor", auditor_node)
    workflow.add_node("fixer", fixer_node)
    workflow.add_node("judge", judge_node)
    
    # Définir le point d'entrée
    workflow.set_entry_point("auditor")
    
    # Ajouter les arêtes conditionnelles
    workflow.add_conditional_edges(
        "auditor",
        after_audit_routing,
        {
            "fix": "fixer",
            "judge": "judge",
            "end": END
        }
    )
    
    # Du Fixer au Judge (toujours)
    workflow.add_edge("fixer", "judge")
    
    # Du Judge, soit on termine, soit on retourne au Fixer
    workflow.add_conditional_edges(
        "judge",
        should_continue_fixing,
        {
            "continue": "fixer",
            "end": END
        }
    )
    
    # Compiler le graphe
    return workflow.compile()


# ============================================================
# FONCTION PRINCIPALE D'EXÉCUTION
# ============================================================

def run_refactoring_swarm(sandbox_dir: str, max_iterations: int = 10) -> Dict[str, Any]:
    """
    Lance le système de refactoring multi-agents sur un sandbox.
    
    Args:
        sandbox_dir: Chemin du dossier sandbox à traiter
        max_iterations: Nombre maximum d'itérations
    
    Returns:
        dict: Résultat final avec statistiques
    """
    print("="*60)
    print("🎯 DÉMARRAGE DU REFACTORING SWARM")
    print("="*60)
    print(f"📁 Sandbox: {sandbox_dir}")
    print(f"🔄 Max itérations: {max_iterations}")
    
    # Créer l'état initial
    initial_state = create_initial_state(sandbox_dir, max_iterations)
    
    # Construire et exécuter le graphe
    graph = build_refactoring_graph()
    
    # Exécuter le workflow
    final_state = graph.invoke(initial_state)
    
    # Afficher le résumé
    print("\n" + "="*60)
    if final_state["mission_complete"] and not final_state["error_occurred"]:
        print("✅ MISSION TERMINÉE AVEC SUCCÈS")
    elif final_state["error_occurred"]:
        print("❌ MISSION ÉCHOUÉE")
        print(f"   Erreur: {final_state['error_message']}")
    else:
        print("⚠️ MISSION INCOMPLÈTE")
    
    print("="*60)
    print(f"📊 Statistiques:")
    print(f"   - Problèmes détectés: {final_state['total_issues_found']}")
    print(f"   - Problèmes corrigés: {final_state['total_issues_fixed']}")
    print(f"   - Itérations utilisées: {final_state['current_iteration']}/{max_iterations}")
    print(f"   - Tests réussis: {'✅ Oui' if final_state['tests_passed'] else '❌ Non'}")
    print("="*60)
    
    return {
        "success": final_state["mission_complete"] and not final_state["error_occurred"],
        "iterations_used": final_state["current_iteration"],
        "issues_found": final_state["total_issues_found"],
        "issues_fixed": final_state["total_issues_fixed"],
        "tests_passed": final_state["tests_passed"],
        "error": final_state.get("error_message")
    }