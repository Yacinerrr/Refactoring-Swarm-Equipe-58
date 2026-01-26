# src/agents/auditor_agent.py

import os
import json
from pathlib import Path
from src.utils.log_helpers import log_audit  # ✅ Utiliser le nouveau logger
from src.utils.analysis_tools import run_pylint, analyze_sandbox


def load_prompt():
    """Charge le prompt système de l'auditeur."""
    with open("src/prompts/auditor_prompt.txt", "r", encoding="utf-8") as file:
        return file.read()


def run_auditor_agent(sandbox_dir: str, model_used: str = "gemini-2.5-flash") -> dict:
    """
    Exécute l'agent Auditeur pour analyser le code dans le sandbox.
    
    UTILISE LES OUTILS DU TOOLSMITH pour l'analyse statique.
    
    Args:
        sandbox_dir (str): Chemin du dossier sandbox à analyser
        model_used (str): Modèle LLM utilisé
    
    Returns:
        dict: Plan de refactoring structuré
    """
    
    system_prompt = load_prompt()
    
    # ✅ UTILISER L'OUTIL DU TOOLSMITH pour l'analyse complète
    print(f"🔍 Running analysis tools on {sandbox_dir}...")
    
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
            if score not in ["10.0", "n/a"] and float(score) < 8.0:
                file_info["issues"].append({
                    "type": "quality",
                    "severity": "medium",
                    "description": f"Code quality issues (Pylint: {score}/10)",
                    "details": pylint_result.get("remarks", "")
                })
                total_issues += 1
        
        # Analyser les résultats pytest (si disponibles)
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
    
    # ✅ Construire le prompt pour le LLM avec les résultats d'analyse
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
    
    # ⚠️ INTÉGRATION MODÈLE IA (à compléter)
    # À remplacer par: output_response = call_gemini_api(input_prompt)
    
    # Simulation pour démonstration
    refactoring_plan = {
        "summary": f"Trouvé {total_issues} problème(s) dans {len(files_with_issues)} fichier(s)",
        "total_issues": total_issues,
        "files_to_fix": []
    }
    
    for file_info in files_with_issues:
        actions = []
        priority = "low"
        
        for issue in file_info["issues"]:
            if issue["severity"] == "critical":
                priority = "critical"
                actions.append({
                    "type": "fix_syntax",
                    "description": issue["description"]
                })
            elif issue["severity"] == "high":
                if priority not in ["critical"]:
                    priority = "high"
                actions.append({
                    "type": "fix_tests",
                    "description": issue["description"]
                })
            else:
                if priority not in ["critical", "high"]:
                    priority = "medium"
                actions.append({
                    "type": "improve_quality",
                    "description": issue["description"]
                })
        
        refactoring_plan["files_to_fix"].append({
            "file": file_info["file"],
            "priority": priority,
            "actions": actions
        })
    
    output_response = json.dumps(refactoring_plan, indent=2, ensure_ascii=False)
    
    # 📋 LOGGING OBLIGATOIRE avec le nouveau système
    log_audit(
        model=model_used,
        input_prompt=input_prompt,
        output_response=output_response,
        file_analyzed=sandbox_dir,
        issues_found=total_issues,
        success=True,
        files_analyzed=len(analysis_results),
        analysis_tool_results=analysis_results  # Données brutes du toolsmith
    )
    
    return {
        "status": "success",
        "sandbox": sandbox_dir,
        "refactoring_plan": refactoring_plan,
        "files_analyzed": len(analysis_results),
        "issues_found": total_issues
    }


if __name__ == "__main__":
    # Test avec un sandbox d'exemple
    test_sandbox = "./sandbox/example"
    
    # Créer un fichier exemple avec des problèmes
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