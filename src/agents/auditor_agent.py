"""
Auditor Agent - Analyse le code et produit un plan de refactoring
==================================================================
L'Auditor lit le code, exécute pylint/pytest via les outils du Toolsmith,
et produit un plan structuré de refactoring.
"""

import json
from pathlib import Path
from src.utils.logger import log_experiment, ActionType
from src.utils.analysis_tools import analyze_sandbox
from src.utils.gemini_client import call_gemini_json


def load_prompt():
    """Charge le prompt système de l'auditeur."""
    with open("src/prompts/auditor_prompt.txt", "r", encoding="utf-8") as file:
        return file.read()


def run_auditor_agent(sandbox_dir: str, model_used: str = "gemini-2.5-flash") -> dict:
    """
    Exécute l'agent Auditeur pour analyser le code dans le sandbox.
    
    Utilise les outils du Toolsmith pour l'analyse statique (pylint + pytest).
    
    Args:
        sandbox_dir (str): Chemin du dossier sandbox à analyser
        model_used (str): Modèle LLM utilisé
    
    Returns:
        dict: Plan de refactoring structuré avec status, sandbox, refactoring_plan
    """
    
    system_prompt = load_prompt()
    
    print(f"🔍 [AUDITOR] Analyse de {sandbox_dir}...")
    
    # ✅ UTILISER L'OUTIL DU TOOLSMITH pour l'analyse complète
    analysis_results = analyze_sandbox(sandbox_dir)
    
    # Préparer les résultats pour le LLM
    files_with_issues = []
    total_issues = 0
    
    for file_analysis in analysis_results:
        file_path = file_analysis["path"]
        pylint_result = file_analysis["pylint_result"]
        pytest_result = file_analysis["pytest_result"]
        
        if not file_path:  # Skip empty entries
            continue
        
        file_info = {
            "file": file_path,
            "issues": []
        }
        
        # Analyser les résultats pylint
        if pylint_result:
            if pylint_result.get("syntax_error"):
                file_info["issues"].append({
                    "type": "syntax_error",
                    "severity": "critical",
                    "description": pylint_result.get("remarks", "Syntax error detected"),
                    "pylint_score": pylint_result.get("score", "n/a")
                })
                total_issues += 1
            
            # Si le score pylint est bas
            score = pylint_result.get("score", "10.0")
            if score not in ["10.0", "n/a"]:
                try:
                    if float(score) < 8.0:
                        file_info["issues"].append({
                            "type": "quality",
                            "severity": "medium",
                            "description": f"Code quality issues (Pylint: {score}/10)",
                            "details": pylint_result.get("remarks", "")
                        })
                        total_issues += 1
                except ValueError:
                    pass
        
        # Analyser les résultats pytest
        if pytest_result and isinstance(pytest_result, dict):
            if pytest_result.get("test_error"):
                file_info["issues"].append({
                    "type": "test_failure",
                    "severity": "high",
                    "description": "Tests are failing",
                    "details": pytest_result.get("remarks", "")
                })
                total_issues += 1
        
        if file_info["issues"]:
            files_with_issues.append(file_info)
    
    # Construire le prompt pour le LLM
    analysis_summary = json.dumps(files_with_issues, indent=2, ensure_ascii=False)
    
    input_prompt = f"""{system_prompt}

=== RÉSULTATS DE L'ANALYSE STATIQUE ===
Outils utilisés: pylint + pytest
Sandbox analysé: {sandbox_dir}

{analysis_summary}

=== MISSION ===
Analysez ces résultats et produisez un PLAN DE REFACTORING structuré en JSON.

Format attendu:
{{
  "summary": "Résumé général des problèmes",
  "total_issues": {total_issues},
  "files_to_fix": [
    {{
      "file": "chemin/fichier.py",
      "priority": "critical" | "high" | "medium" | "low",
      "actions": [
        {{
          "type": "fix_syntax" | "improve_quality" | "fix_tests",
          "description": "Description de l'action"
        }}
      ]
    }}
  ]
}}

Répondez UNIQUEMENT en JSON.
"""
    
    # ✅ APPEL À L'API GEMINI
    try:
        output_response_json = call_gemini_json(input_prompt, model_name=model_used)
        output_response = json.dumps(output_response_json, indent=2, ensure_ascii=False)
        
        # 📋 LOGGING OBLIGATOIRE
        log_experiment(
            agent_name="Auditor",
            model_used=model_used,
            action=ActionType.ANALYSIS,
            details={
                "sandbox_analyzed": sandbox_dir,
                "input_prompt": input_prompt,
                "output_response": output_response,
                "files_analyzed": len(analysis_results),
                "issues_found": total_issues,
                "analysis_tool_results": analysis_results
            },
            status="SUCCESS"
        )
        
        print(f"✅ [AUDITOR] Analyse terminée: {total_issues} problème(s) détecté(s)")
        
        return {
            "status": "success",
            "sandbox": sandbox_dir,
            "refactoring_plan": output_response_json,
            "files_analyzed": len(analysis_results),
            "issues_found": total_issues
        }
        
    except Exception as e:
        error_msg = f"Erreur lors de l'appel à Gemini: {str(e)}"
        
        log_experiment(
            agent_name="Auditor",
            model_used=model_used,
            action=ActionType.DEBUG,
            details={
                "sandbox_analyzed": sandbox_dir,
                "input_prompt": input_prompt,
                "output_response": error_msg,
                "error": str(e)
            },
            status="FAILURE"
        )
        
        raise Exception(error_msg)


if __name__ == "__main__":
    # Test avec un sandbox d'exemple
    import os
    test_sandbox = "./sandbox/example"
    
    os.makedirs(test_sandbox, exist_ok=True)
    test_file = Path(test_sandbox) / "bad_code.py"
    test_file.write_text("""
def foo():
    x = 1  # Variable non utilisée
    return 42
""")
    
    result = run_auditor_agent(test_sandbox)
    print("\n=== Résultat de l'Auditeur ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))