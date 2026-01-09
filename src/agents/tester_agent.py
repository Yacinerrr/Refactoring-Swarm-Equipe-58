# src/agents/tester_agent.py

import os
import json
from pathlib import Path
from src.utils.logger import log_experiment, ActionType
from src.utils.analysis_tools import run_pytest  # ✅ Use toolsmith's pytest runner


def load_prompt():
    """Charge le prompt système du testeur."""
    with open("src/prompts/tester_prompt.txt", "r", encoding="utf-8") as file:
        return file.read()


def run_tester_agent(target_dir: str, model_used: str = "gemini-2.5-flash") -> dict:
    """
    Exécute l'agent Testeur en utilisant les outils du Toolsmith.
    
    Args:
        target_dir (str): Répertoire à tester.
        model_used (str): Modèle LLM utilisé.
    
    Returns:
        dict: Résultat structuré avec 'test_status', 'failing_tests', 'action'.
    """
    
    system_prompt = load_prompt()
    
    # ✅ UTILISER L'OUTIL DU TOOLSMITH pour exécuter pytest
    print(f"🧪 Running pytest using toolsmith's runner on {target_dir}...")
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
    
    # Déterminer le statut
    if failed_tests == 0 and total_tests > 0:
        test_status = "success"
        action = "validate"
    elif total_tests == 0:
        test_status = "no_tests"
        action = "return_to_corrector"  # Need to generate tests
    else:
        test_status = "failure"
        action = "return_to_corrector"
    
    # Construire le prompt pour le LLM
    pytest_summary = json.dumps(pytest_results, indent=2, ensure_ascii=False)
    
    input_prompt = f"""{system_prompt}

=== RÉSULTATS D'EXÉCUTION PYTEST ===
Répertoire testé: {target_dir}
Tests trouvés: {total_tests}
Tests échoués: {failed_tests}

Détails:
{pytest_summary}

=== MISSION ===
Analysez ces résultats et répondez UNIQUEMENT en JSON:
{{
  "test_status": "success" | "failure" | "no_tests",
  "action": "validate" | "return_to_corrector",
  "analysis": "Votre analyse des problèmes"
}}
"""
    
    # ⚠️ INTÉGRATION MODÈLE IA
    # À remplacer par: output_response = call_gemini_api(input_prompt)
    
    output_response = json.dumps({
        "test_status": test_status,
        "failing_tests": failing_tests,
        "action": action,
        "total_tests": total_tests,
        "failed_tests": failed_tests,
        "summary": f"{failed_tests}/{total_tests} tests failed" if failed_tests > 0 else "All tests passed"
    }, indent=2)
    
    # 📋 LOGGING OBLIGATOIRE
    log_experiment(
        agent_name="Fixer",
        model_used=model_used,
        action=ActionType.ANALYSIS,
        details={
            "target_dir": target_dir,
            "input_prompt": input_prompt,  # ✅ OBLIGATOIRE
            "output_response": output_response,  # ✅ OBLIGATOIRE
            "test_status": test_status,
            "total_tests": total_tests,
            "failed_tests": failed_tests,
            "pytest_tool_results": pytest_results  # Données brutes du toolsmith
        },
        status="SUCCESS"
    )
    
    # Traiter la réponse
    try:
        result = json.loads(output_response)
        return {
            "test_status": result.get("test_status", "unknown"),
            "failing_tests": result.get("failing_tests", []),
            "action": result.get("action", "unknown"),
            "should_continue": result.get("action") == "return_to_corrector",
            "summary": result.get("summary", "")
        }
    except json.JSONDecodeError as e:
        log_experiment(
            agent_name="Tester_Agent",
            model_used=model_used,
            action=ActionType.ANALYSIS,
            details={
                "target_dir": target_dir,
                "input_prompt": input_prompt,
                "output_response": output_response,
                "error": str(e)
            },
            status="FAILURE"
        )
        return {
            "test_status": "error",
            "action": "error",
            "error": f"Invalid JSON response: {str(e)}",
            "should_continue": False
        }


def validate_and_test(target_dir: str, model_used: str = "gemini-2.5-flash") -> dict:
    """
    Pipeline complet utilisant les outils du Toolsmith.
    """
    print(f"🚀 Starting test validation for {target_dir}...")
    result = run_tester_agent(target_dir, model_used)
    
    # Afficher un résumé
    if result["test_status"] == "success":
        print("✅ All tests passed!")
    elif result["test_status"] == "failure":
        print(f"❌ {len(result.get('failing_tests', []))} test(s) failed")
    elif result["test_status"] == "no_tests":
        print("⚠️ No tests found - need to generate tests")
    else:
        print(f"⚠️ Test execution error: {result.get('error', 'Unknown error')}")
    
    return result


if __name__ == "__main__":
    test_dir = "./sandbox/example"
    result = validate_and_test(test_dir)
    print("\n=== Résultat Final ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))