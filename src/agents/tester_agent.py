# src/agents/tester_agent.py

import os
import json
import subprocess
from pathlib import Path
from src.utils.logger import log_experiment, ActionType

def load_prompt():
    """Charge le prompt système du testeur."""
    with open("src/prompts/tester_prompt.txt", "r", encoding="utf-8") as file:
        return file.read()


def run_pytest(target_dir: str) -> str:
    """
    Exécute pytest sur le répertoire cible et capture les résultats.
    
    Args:
        target_dir (str): Chemin du dossier à tester.
    
    Returns:
        str: Sortie brute de pytest (stdout + stderr).
    """
    try:
        result = subprocess.run(
            ["pytest", target_dir, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "TIMEOUT: pytest execution exceeded 30 seconds"
    except FileNotFoundError:
        return "ERROR: pytest not installed. Run: pip install pytest"


def run_tester_agent(pytest_logs: str, target_dir: str, model_used: str = "gemini-2.5-flash") -> dict:
    """
    Exécute l'agent Testeur pour analyser les logs de pytest.
    
    Args:
        pytest_logs (str): Sortie brute de pytest.
        target_dir (str): Répertoire testé (pour contexte).
        model_used (str): Modèle LLM utilisé.
    
    Returns:
        dict: Résultat structuré avec 'test_status', 'failing_tests', 'action'.
    """
    
    system_prompt = load_prompt()
    
    # Construire le prompt complet
    # NOTE: Logs complets car essentiels pour le diagnostic
    input_prompt = f"""{system_prompt}

=== LOGS D'EXÉCUTION PYTEST ===
{pytest_logs[:2000]}{"..." if len(pytest_logs) > 2000 else ""}

=== CONTEXTE ===
Répertoire testé: {target_dir}

Analysez ces logs et répondez UNIQUEMENT en JSON.
"""
    
    # ⚠️ INTÉGRATION MODÈLE IA (à compléter selon votre orchestrateur)
    # Pour l'instant, simulation basique
    # À remplacer par: output_response = call_gemini_api(input_prompt)
    
    # Détection simple d'erreurs pour la simulation
    if "FAILED" in pytest_logs or "ERROR" in pytest_logs:
        test_status = "failure"
        failing_tests = [
            {
                "test_name": "test_example",
                "error_type": "AssertionError",
                "error_message": "Extracted from pytest logs"
            }
        ]
        action = "return_to_corrector"
    else:
        test_status = "success"
        failing_tests = []
        action = "validate"
    
    output_response = json.dumps({
        "test_status": test_status,
        "failing_tests": failing_tests,
        "action": action
    })
    
    # 📋 LOGGING OBLIGATOIRE
    log_experiment(
        agent_name="Tester_Agent",
        model_used=model_used,
        action=ActionType.DEBUG,
        details={
            "target_dir": target_dir,
            "input_prompt": input_prompt,  # ✅ OBLIGATOIRE
            "output_response": output_response,  # ✅ OBLIGATOIRE
            "pytest_output_length": len(pytest_logs),
            "test_status": test_status
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
            "should_continue": result.get("action") == "return_to_corrector"
        }
    except json.JSONDecodeError as e:
        log_experiment(
            agent_name="Tester_Agent",
            model_used=model_used,
            action=ActionType.DEBUG,
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
            "error": f"Invalid JSON response: {str(e)}"
        }


def validate_and_test(target_dir: str, model_used: str = "gemini-2.5-flash") -> dict:
    """
    Pipeline complet : run pytest → analyze with Tester Agent.
    
    Args:
        target_dir (str): Répertoire à tester.
        model_used (str): Modèle LLM utilisé.
    
    Returns:
        dict: Résultat final du test.
    """
    
    print(f"🧪 Running pytest on {target_dir}...")
    pytest_output = run_pytest(target_dir)
    
    print("🤖 Analyzing test results with Tester Agent...")
    result = run_tester_agent(
        pytest_logs=pytest_output,
        target_dir=target_dir,
        model_used=model_used
    )
    
    return result


if __name__ == "__main__":
    # Test local
    test_dir = "./sandbox/example"
    
    # Créer un dossier de test minimal pour démo
    os.makedirs(test_dir, exist_ok=True)
    
    # Écrire un test simple
    test_file = Path(test_dir) / "test_example.py"
    test_file.write_text("""
def test_simple():
    assert 1 + 1 == 2

def test_failure():
    assert 1 + 1 == 3
""")
    
    result = validate_and_test(test_dir)
    
    print("=== Résultat du Testeur ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
