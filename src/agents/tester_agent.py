"""
Tester Agent (Judge) - Exécute les tests et analyse les résultats
==================================================================
Le Judge exécute pytest et décide si on continue ou si c'est terminé.
"""

import json
from src.utils.logger import log_experiment, ActionType
from src.utils.analysis_tools import run_pytest
from src.utils.gemini_client import call_gemini_json
from src.config import get_model_name


def load_prompt():
    """Charge le prompt système du testeur."""
    with open("src/prompts/tester_prompt.txt", "r", encoding="utf-8") as file:
        return file.read()


def run_tester_agent(target_dir: str, model_used: str = None) -> dict:
    """
    Exécute l'agent Testeur en utilisant les outils du Toolsmith.
    
    Args:
        target_dir (str): Répertoire à tester
        model_used (str): Modèle LLM utilisé (None = utilise config.py)
    
    Returns:
        dict: Résultat avec 'test_status', 'failing_tests', 'action', 'should_continue'
    """
    
    # Utiliser le modèle par défaut si non spécifié
    if model_used is None:
        model_used = get_model_name()
    
    system_prompt = load_prompt()
    
    print(f"🧪 [JUDGE] Exécution des tests dans {target_dir}...")
    
    # ✅ UTILISER L'OUTIL DU TOOLSMITH pour exécuter pytest
    pytest_results = run_pytest(target_dir)
    
    # Analyser les résultats
    failing_tests = []
    total_tests = 0
    failed_tests = 0
    
    for result in pytest_results:
        if not result.get("path"):  # Skip empty entries
            continue
        
        total_tests += 1
        
        if result.get("test_error"):
            failed_tests += 1
            failing_tests.append({
                "test_file": result["path"],
                "error_type": "TestFailure",
                "error_message": result.get("remarks", "Test failed"),
                "return_code": result.get("code", 1)
            })
    
    # Déterminer le statut initial
    if failed_tests == 0 and total_tests > 0:
        initial_status = "success"
    elif total_tests == 0:
        initial_status = "no_tests"
    else:
        initial_status = "failure"
    
    # Construire le prompt pour le LLM
    pytest_summary = json.dumps(pytest_results, indent=2, ensure_ascii=False)
    
    input_prompt = f"""{system_prompt}

=== RÉSULTATS D'EXÉCUTION PYTEST ===
Répertoire testé: {target_dir}
Tests trouvés: {total_tests}
Tests échoués: {failed_tests}

Détails complets:
{pytest_summary}

=== MISSION ===
Analysez ces résultats et répondez UNIQUEMENT en JSON:

{{
  "test_status": "success" | "failure" | "no_tests",
  "action": "validate" | "return_to_corrector",
  "analysis": "Votre analyse factuelle des problèmes",
  "failing_tests": [
    {{
      "test_name": "nom du test qui échoue",
      "error_type": "type d'erreur",
      "error_message": "message résumé"
    }}
  ]
}}

RÈGLES:
- Si TOUS les tests passent → test_status="success", action="validate"
- Si AU MOINS un test échoue → test_status="failure", action="return_to_corrector"
- Si aucun test trouvé → test_status="no_tests", action="return_to_corrector"
"""
    
    # ✅ APPEL À L'API GEMINI
    try:
        output_response_json = call_gemini_json(input_prompt, model_name=model_used)
        output_response = json.dumps(output_response_json, indent=2, ensure_ascii=False)
        
        # Extraire les informations importantes
        test_status = output_response_json.get("test_status", initial_status)
        action = output_response_json.get("action", "return_to_corrector")
        analysis = output_response_json.get("analysis", "")
        llm_failing_tests = output_response_json.get("failing_tests", [])
        
        # Utiliser les tests défaillants du LLM s'ils sont fournis, sinon ceux qu'on a détectés
        final_failing_tests = llm_failing_tests if llm_failing_tests else failing_tests
        
        # 📋 LOGGING OBLIGATOIRE
        log_experiment(
            agent_name="Judge",
            model_used=model_used,
            action=ActionType.ANALYSIS,
            details={
                "target_dir": target_dir,
                "input_prompt": input_prompt,
                "output_response": output_response,
                "test_status": test_status,
                "total_tests": total_tests,
                "failed_tests": failed_tests,
                "pytest_tool_results": pytest_results
            },
            status="SUCCESS"
        )
        
        # Afficher le résultat
        if test_status == "success":
            print("✅ [JUDGE] Tous les tests passent!")
        elif test_status == "no_tests":
            print("⚠️ [JUDGE] Aucun test trouvé")
        else:
            print(f"❌ [JUDGE] {len(final_failing_tests)} test(s) échoue(nt)")
            if analysis:
                print(f"   Analyse: {analysis[:100]}...")
        
        return {
            "test_status": test_status,
            "failing_tests": final_failing_tests,
            "action": action,
            "should_continue": (action == "return_to_corrector"),
            "summary": f"{failed_tests}/{total_tests} tests failed" if failed_tests > 0 else "All tests passed",
            "analysis": analysis
        }
        
    except Exception as e:
        error_msg = f"Erreur lors de l'appel à Gemini: {str(e)}"
        
        # En cas d'erreur, utiliser les résultats bruts
        log_experiment(
            agent_name="Judge",
            model_used=model_used,
            action=ActionType.DEBUG,
            details={
                "target_dir": target_dir,
                "input_prompt": input_prompt,
                "output_response": error_msg,
                "error": str(e)
            },
            status="FAILURE"
        )
        
        # Retourner quand même un résultat utilisable
        return {
            "test_status": initial_status,
            "failing_tests": failing_tests,
            "action": "validate" if initial_status == "success" else "return_to_corrector",
            "should_continue": (initial_status != "success"),
            "error": error_msg
        }


if __name__ == "__main__":
    # Test avec un sandbox d'exemple
    test_dir = "./sandbox/example"
    result = run_tester_agent(test_dir)
    
    print("\n=== Résultat Final du Judge ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))