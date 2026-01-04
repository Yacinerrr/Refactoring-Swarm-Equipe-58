# src/agents/corrector_agent.py

import os
import json
from src.utils.logger import log_experiment, ActionType

def load_prompt():
    """Charge le prompt système du correcteur."""
    with open("src/prompts/corrector_prompt.txt", "r", encoding="utf-8") as file:
        return file.read()


def run_corrector_agent(audit_plan: str, target_code: str, target_file: str, model_used: str = "gemini-2.5-flash"):
    """
    Exécute l'agent Correcteur pour appliquer les modifications selon le plan d'audit.
    
    Args:
        audit_plan (str): Le plan de refactoring produit par l'Agent Auditeur.
        target_code (str): Le code source à modifier.
        target_file (str): Le chemin du fichier ciblé (pour contexte et logging).
        model_used (str): Modèle LLM utilisé.
    
    Returns:
        dict: Résultat structuré avec 'status', 'modified_code', et 'changes'.
    """
    
    system_prompt = load_prompt()
    
    # Construire le prompt complet pour le modèle
    # NOTE: Contexte limité pour économiser les tokens
    input_prompt = f"""{system_prompt}

=== PLAN DE REFACTORING (par l'Auditeur) ===
{audit_plan}

=== CODE À MODIFIER ===
Fichier: {target_file}

```python
{target_code}
```

Applique maintenant le plan, fichier par fichier. Réponds UNIQUEMENT en JSON.
"""
    
    # ⚠️ INTÉGRATION MODÈLE IA (à compléter selon votre orchestrateur)
    # Pour l'instant, simulation pour la démonstration
    # À remplacer par: output_response = call_gemini_api(input_prompt)
    
    output_response = f"""{{
  "file": "{target_file}",
  "status": "modified",
  "changes": [
    {{
      "type": "refactor",
      "description": "Applied refactoring according to audit plan"
    }}
  ]
}}"""
    
    # 📋 LOGGING OBLIGATOIRE
    log_experiment(
        agent_name="Corrector_Agent",
        model_used=model_used,
        action=ActionType.FIX,
        details={
            "file_processed": target_file,
            "input_prompt": input_prompt,  # ✅ OBLIGATOIRE
            "output_response": output_response,  # ✅ OBLIGATOIRE
            "audit_plan_summary": audit_plan[:200] + "..." if len(audit_plan) > 200 else audit_plan
        },
        status="SUCCESS"
    )
    
    # Traiter la réponse
    try:
        result = json.loads(output_response)
        return {
            "status": result.get("status", "unknown"),
            "file": result.get("file", target_file),
            "changes": result.get("changes", []),
            "modified_code": target_code  # À remplacer par le vrai code modifié
        }
    except json.JSONDecodeError as e:
        log_experiment(
            agent_name="Corrector_Agent",
            model_used=model_used,
            action=ActionType.DEBUG,
            details={
                "file_processed": target_file,
                "input_prompt": input_prompt,
                "output_response": output_response,
                "error": str(e)
            },
            status="FAILURE"
        )
        return {
            "status": "error",
            "file": target_file,
            "error": f"Invalid JSON response: {str(e)}"
        }


if __name__ == "__main__":
    # Test local
    audit_plan_example = """
    1. Problème: Fonction foo() manque de docstring
       Fichier: example.py
       Action: Ajouter docstring
    
    2. Problème: Variable 'x' non utilisée
       Fichier: example.py
       Action: Supprimer ou utiliser
    """
    
    code_example = """def foo():
    return 42
"""
    
    result = run_corrector_agent(
        audit_plan=audit_plan_example,
        target_code=code_example,
        target_file="example.py"
    )
    
    print("=== Résultat du Correcteur ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
