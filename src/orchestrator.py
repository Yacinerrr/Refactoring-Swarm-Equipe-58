"""
Updated Orchestrator - 3-Agent Collaborative System
====================================================
AUDITOR → CORRECTOR → TESTER (with feedback loop)
"""

from langgraph.graph import StateGraph, END
from typing import Dict, Any, TypedDict
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
# NŒUDS DU GRAPHE (3 Agents)
# ============================================================

def auditor_node(state: RefactoringState) -> RefactoringState:
    """
    AGENT 1: AUDITOR
    - Analyse code avec pylint
    - Comprend l'intent sémantique des fonctions
    - Produit plan de refactoring + comportements attendus
    """
    print("\n🔍 [AUDITOR] Analyse sémantique du code...")
    
    try:
        result = run_auditor_agent(
            sandbox_dir=state["sandbox_dir"],
            model_used=state["model_used"]
        )
        
        # Update state with Auditor's outputs
        state["audit_complete"] = True
        state["audit_plan"] = result.get("refactoring_plan", {})
        
        # Extract expected_behaviors from result (not from refactoring_plan)
        expected_behaviors = result.get("expected_behaviors", [])
        state["expected_behaviors"] = expected_behaviors
        
        state["total_issues_found"] = result.get("issues_found", 0)
        
        print(f"✅ [AUDITOR] Complete:")
        print(f"   - {len(expected_behaviors)} comportement(s) attendu(s) identifié(s)")
        print(f"   - {state['total_issues_found']} problème(s) détecté(s)")
        
        # If no issues found, we can skip to testing
        if state["total_issues_found"] == 0:
            print("   ℹ️ Aucun problème - passage direct au Tester")
            state["should_continue"] = False
        
    except Exception as e:
        print(f"❌ [AUDITOR] Erreur: {e}")
        state["error_occurred"] = True
        state["error_message"] = f"Auditor error: {str(e)}"
        state["should_continue"] = False
    
    return state


def corrector_node(state: RefactoringState) -> RefactoringState:
    """
    AGENT 2: CORRECTOR
    - Reçoit le plan de l'Auditor (avec comportements attendus)
    - Reçoit le feedback du Tester (si en boucle)
    - Corrige syntax ET logique
    """
    print(f"\n🔧 [CORRECTOR] Correction (Itération {state['current_iteration'] + 1})...")
    
    try:
        # Increment iteration
        state = increment_iteration(state)
        
        # Check iteration limit
        if check_iteration_limit(state):
            print(f"⚠️ [CORRECTOR] Limite d'itérations atteinte ({state['max_iterations']})")
            state["should_continue"] = False
            state["error_occurred"] = True
            state["error_message"] = "Max iterations reached"
            return state
        
        # Get test feedback if we're in a loop
        test_feedback = None
        if state.get("test_results") and not state.get("tests_passed"):
            test_feedback = state["test_results"]
        
        # Get expected_behaviors from state
        expected_behaviors = state.get("expected_behaviors", [])
        
        # Run corrector with ALL context
        result = run_corrector_agent(
            audit_plan=state["audit_plan"],
            expected_behaviors=expected_behaviors,
            test_feedback=test_feedback,
            sandbox_dir=state["sandbox_dir"],
            model_used=state["model_used"]
        )
        
        # Update state
        if result.get("files_modified"):
            state["files_fixed"].extend(result["files_modified"])
            state["total_issues_fixed"] += len(result.get("changes", []))
        
        print(f"✅ [CORRECTOR] {len(result.get('files_modified', []))} fichier(s) modifié(s)")
        
    except Exception as e:
        print(f"❌ [CORRECTOR] Erreur: {e}")
        state["error_occurred"] = True
        state["error_message"] = f"Corrector error: {str(e)}"
        state["should_continue"] = False
    
    return state


def tester_node(state: RefactoringState) -> RefactoringState:
    """
    AGENT 3: TESTER
    - Reçoit les comportements attendus de l'Auditor
    - GÉNÈRE des tests sémantiques intelligents
    - EXÉCUTE pytest
    - ANALYSE les résultats
    - Fournit feedback détaillé au Corrector si échec
    """
    print("\n🧪 [TESTER] Génération et validation des tests...")
    
    try:
        # Get expected_behaviors from state
        expected_behaviors = state.get("expected_behaviors", [])
        
        result = run_tester_agent(
            expected_behaviors=expected_behaviors,
            sandbox_dir=state["sandbox_dir"],
            model_used=state["model_used"]
        )
        
        # Update state with test results
        state["test_results"] = result
        state["tests_passed"] = (result.get("test_status") == "success")
        state["failing_tests"] = result.get("failing_tests", [])
        
        # Decide next action
        if state["tests_passed"]:
            print("✅ [TESTER] Tous les tests passent!")
            state["should_continue"] = False
            state = mark_mission_complete(state, success=True)
        else:
            print(f"❌ [TESTER] {len(state['failing_tests'])} test(s) échoue(nt)")
            
            # Check if we should continue
            if check_iteration_limit(state):
                print(f"⚠️ [TESTER] Limite d'itérations atteinte, arrêt")
                state["should_continue"] = False
                state = mark_mission_complete(state, success=False)
            else:
                print("🔁 [TESTER] Retour au Corrector avec feedback...")
                state["should_continue"] = True
        
    except Exception as e:
        print(f"❌ [TESTER] Erreur: {e}")
        import traceback
        traceback.print_exc()  # Print full error for debugging
        state["error_occurred"] = True
        state["error_message"] = f"Tester error: {str(e)}"
        state["should_continue"] = False
    
    return state


# ============================================================
# FONCTIONS DE ROUTAGE
# ============================================================

def should_go_to_corrector(state: RefactoringState) -> str:
    """Décide si on passe au Corrector ou si on skip."""
    if state["error_occurred"]:
        return "end"
    
    if state["total_issues_found"] == 0:
        return "tester"  # No issues, go straight to testing
    
    return "corrector"  # Issues found, need fixing


def should_continue_loop(state: RefactoringState) -> str:
    """Décide si on continue la boucle Corrector ← Tester."""
    # If error or mission complete, stop
    if state["error_occurred"] or state["mission_complete"]:
        return "end"
    
    # If tests passed, we're done
    if state["tests_passed"]:
        return "end"
    
    # If should continue and not at limit, go back to corrector
    if state["should_continue"] and not check_iteration_limit(state):
        return "corrector"
    
    return "end"


# ============================================================
# CONSTRUCTION DU GRAPHE
# ============================================================

def build_refactoring_graph() -> StateGraph:
    """
    Construit le graphe LangGraph pour le système 3-agents.
    
    FLOW:
    START → AUDITOR → (decision) → CORRECTOR → TESTER → (loop?) → END
                           ↓
                       (no issues)
                           ↓
                        TESTER → END
    """
    workflow = StateGraph(RefactoringState)
    
    # Add the 3 agent nodes
    workflow.add_node("auditor", auditor_node)
    workflow.add_node("corrector", corrector_node)
    workflow.add_node("tester", tester_node)
    
    # Set entry point
    workflow.set_entry_point("auditor")
    
    # Auditor → Corrector or Tester (depending on issues found)
    workflow.add_conditional_edges(
        "auditor",
        should_go_to_corrector,
        {
            "corrector": "corrector",
            "tester": "tester",
            "end": END
        }
    )
    
    # Corrector → always goes to Tester
    workflow.add_edge("corrector", "tester")
    
    # Tester → either END or back to Corrector (feedback loop)
    workflow.add_conditional_edges(
        "tester",
        should_continue_loop,
        {
            "corrector": "corrector",  # Loop back with feedback
            "end": END
        }
    )
    
    return workflow.compile()


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def run_refactoring_swarm(sandbox_dir: str, max_iterations: int = 10) -> Dict[str, Any]:
    """
    Lance le système de refactoring à 3 agents.
    
    Args:
        sandbox_dir: Chemin du dossier sandbox
        max_iterations: Nombre maximum d'itérations
    
    Returns:
        dict: Résultat final avec statistiques
    """
    print("="*70)
    print("🤖 REFACTORING SWARM - 3-Agent Collaborative System")
    print("="*70)
    print(f"📁 Sandbox: {sandbox_dir}")
    print(f"🔄 Max itérations: {max_iterations}")
    print("\n🎯 Workflow: AUDITOR → CORRECTOR → TESTER (loop)")
    
    # Create initial state
    initial_state = create_initial_state(sandbox_dir, max_iterations)
    
    # Build and run workflow
    graph = build_refactoring_graph()
    final_state = graph.invoke(initial_state)
    
    # Display summary
    print("\n" + "="*70)
    if final_state["mission_complete"] and not final_state["error_occurred"]:
        print("✅ MISSION TERMINÉE AVEC SUCCÈS")
    elif final_state["error_occurred"]:
        print("❌ MISSION ÉCHOUÉE")
        print(f"   Erreur: {final_state['error_message']}")
    else:
        print("⚠️ MISSION INCOMPLÈTE")
    
    print("="*70)
    print(f"📊 Statistiques:")
    print(f"   - Problèmes détectés: {final_state['total_issues_found']}")
    print(f"   - Problèmes corrigés: {final_state['total_issues_fixed']}")
    print(f"   - Itérations utilisées: {final_state['current_iteration']}/{max_iterations}")
    print(f"   - Tests réussis: {'✅ Oui' if final_state['tests_passed'] else '❌ Non'}")
    print(f"   - Comportements validés: {len(final_state.get('expected_behaviors', []))}")
    print("="*70)
    
    return {
        "success": final_state["mission_complete"] and not final_state["error_occurred"],
        "iterations_used": final_state["current_iteration"],
        "issues_found": final_state["total_issues_found"],
        "issues_fixed": final_state["total_issues_fixed"],
        "tests_passed": final_state["tests_passed"],
        "behaviors_validated": len(final_state.get("expected_behaviors", [])),
        "error": final_state.get("error_message")
    }