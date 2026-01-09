# src/agents/auditor_agent.py

import os
import json
from src.utils.logger import log_experiment, ActionType

def load_prompt():
    with open("src/prompts/auditor_prompt.txt", "r", encoding="utf-8") as file:
        prompt = file.read()
    return prompt

def run_auditor_agent(code_to_analyze, file_path: str = "unknown", model_used: str = "gemini-2.5-flash"):
    """
    Exécute l'agent Auditeur pour analyser du code.
    
    Args:
        code_to_analyze (str): Le code à analyser
        file_path (str): Chemin du fichier analysé
        model_used (str): Modèle LLM utilisé
    
    Returns:
        dict: Résultat structuré avec 'audit_plan', 'issues_found', etc.
    """
    system_prompt = load_prompt()
    
    # Construire le prompt complet
    input_prompt = f"""{system_prompt}

=== CODE À ANALYSER ===
Fichier: {file_path}
```python
{code_to_analyze}
```

Analysez ce code et produisez un plan d'audit structuré en JSON.
"""
    
    # ⚠️ INTÉGRATION MODÈLE IA (à compléter selon votre orchestrateur)
    # À remplacer par: output_response = call_gemini_api(input_prompt)
    
    # Simulation pour démonstration
    output_response = json.dumps({
        "file": file_path,
        "issues": [
            {
                "type": "missing_docstring",
                "line": 1,
                "severity": "medium",
                "description": "Function lacks docstring"
            }
        ],
        "audit_plan": "Add docstrings and improve code quality"
    })
    
    # 📋 LOGGING OBLIGATOIRE
    try:
        result = json.loads(output_response)
        issues_count = len(result.get("issues", []))
        
        log_experiment(
            agent_name="Auditor",
            model_used=model_used,
            action=ActionType.ANALYSIS,
            details={
                "file_analyzed": file_path,
                "input_prompt": input_prompt,  # ✅ OBLIGATOIRE
                "output_response": output_response,  # ✅ OBLIGATOIRE
                "issues_found": issues_count,
                "code_length": len(code_to_analyze)
            },
            status="SUCCESS"
        )
        
        return {
            "status": "success",
            "file": file_path,
            "issues": result.get("issues", []),
            "audit_plan": result.get("audit_plan", ""),
            "issues_count": issues_count
        }
        
    except json.JSONDecodeError as e:
        log_experiment(
            agent_name="Auditor",
            model_used=model_used,
            action=ActionType.ANALYSIS,
            details={
                "file_analyzed": file_path,
                "input_prompt": input_prompt,
                "output_response": output_response,
                "error": str(e)
            },
            status="FAILURE"
        )
        
        return {
            "status": "error",
            "file": file_path,
            "error": f"Invalid JSON response: {str(e)}"
        }


if __name__ == "__main__":
    example_code = """def foo():
    return 42
"""
    result = run_auditor_agent(example_code, file_path="example.py")
    print("=== Résultat de l'Auditeur ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))