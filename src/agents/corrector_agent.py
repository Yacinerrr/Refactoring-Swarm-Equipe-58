"""
Corrector Agent (Fixer) - Applique les corrections selon le plan d'audit
==========================================================================
Le Fixer lit le plan de refactoring et modifie le code fichier par fichier.
"""

import json
from src.utils.logger import log_experiment, ActionType
from src.utils.gemini_client import call_gemini_json
from src.utils.file_tools import read_file, write_file, extract_code_from_markdown


def load_prompt():
    """Charge le prompt système du correcteur."""
    with open("src/prompts/corrector_prompt.txt", "r", encoding="utf-8") as file:
        return file.read()


def run_corrector_agent(
    audit_plan: str,
    target_file: str,
    sandbox_dir: str,
    model_used: str = "gemini-1.5-flash"
) -> dict:
    """
    Exécute l'agent Correcteur pour appliquer les modifications selon le plan d'audit.
    
    Args:
        audit_plan (str): Le plan de refactoring produit par l'Agent Auditeur (JSON)
        target_file (str): Le chemin du fichier à modifier (relatif au sandbox)
        sandbox_dir (str): Le chemin du dossier sandbox
        model_used (str): Modèle LLM utilisé
    
    Returns:
        dict: Résultat avec 'status', 'file', 'changes', 'modified_code'
    """
    
    system_prompt = load_prompt()
    
    print(f"🔧 [FIXER] Correction de: {target_file}")
    
    # Lire le code actuel du fichier
    try:
        current_code = read_file(target_file, sandbox_dir)
    except FileNotFoundError:
        print(f"⚠️ [FIXER] Fichier non trouvé: {target_file}")
        return {
            "status": "error",
            "file": target_file,
            "error": "File not found",
            "changes": []
        }
    
    # Construire le prompt complet
    input_prompt = f"""{system_prompt}

=== PLAN DE REFACTORING (par l'Auditeur) ===
{audit_plan}

=== CODE ACTUEL À MODIFIER ===
Fichier: {target_file}
```python
{current_code}
```

=== INSTRUCTIONS ===
1. Lis attentivement le plan de refactoring
2. Identifie les actions à appliquer pour CE fichier spécifique: {target_file}
3. Applique UNIQUEMENT les modifications décrites dans le plan
4. Retourne le code modifié complet

Format de sortie OBLIGATOIRE (JSON):
{{
  "file": "{target_file}",
  "status": "modified" | "unchanged",
  "changes": [
    {{
      "type": "fix_syntax | improve_quality | fix_tests | add_docstring",
      "description": "Description de la modification"
    }}
  ],
  "modified_code": "Le code Python complet après modifications (sans balises markdown)"
}}

IMPORTANT: Le champ "modified_code" doit contenir TOUT le code du fichier après modifications,
pas seulement les parties changées. N'utilise PAS de balises ```python```, juste le code pur.
"""
    
    # ✅ APPEL À L'API GEMINI
    try:
        output_response_json = call_gemini_json(input_prompt, model_name=model_used)
        output_response = json.dumps(output_response_json, indent=2, ensure_ascii=False)
        
        # Extraire le code modifié
        modified_code = output_response_json.get("modified_code", "")
        
        # Nettoyer le code (enlever les balises markdown si présentes)
        modified_code = extract_code_from_markdown(modified_code)
        
        # Si le code a été modifié, l'écrire dans le fichier
        if output_response_json.get("status") == "modified" and modified_code:
            write_file(target_file, modified_code, sandbox_dir)
            print(f"✅ [FIXER] Fichier modifié: {target_file}")
        else:
            print(f"ℹ️ [FIXER] Aucune modification pour: {target_file}")
        
        # 📋 LOGGING OBLIGATOIRE
        log_experiment(
            agent_name="Fixer",
            model_used=model_used,
            action=ActionType.FIX,
            details={
                "file_processed": target_file,
                "input_prompt": input_prompt,
                "output_response": output_response,
                "code_modified": output_response_json.get("status") == "modified",
                "changes_count": len(output_response_json.get("changes", []))
            },
            status="SUCCESS"
        )
        
        return {
            "status": output_response_json.get("status", "unknown"),
            "file": target_file,
            "changes": output_response_json.get("changes", []),
            "modified_code": modified_code
        }
        
    except Exception as e:
        error_msg = f"Erreur lors de l'appel à Gemini: {str(e)}"
        
        log_experiment(
            agent_name="Fixer",
            model_used=model_used,
            action=ActionType.DEBUG,
            details={
                "file_processed": target_file,
                "input_prompt": input_prompt,
                "output_response": error_msg,
                "error": str(e)
            },
            status="FAILURE"
        )
        
        return {
            "status": "error",
            "file": target_file,
            "error": str(e),
            "changes": []
        }


if __name__ == "__main__":
    # Test local
    import os
    from pathlib import Path
    
    # Créer un fichier de test
    test_sandbox = "./sandbox/test_fixer"
    os.makedirs(test_sandbox, exist_ok=True)
    
    test_file = "example.py"
    Path(test_sandbox) / test_file
    
    # Écrire un code avec des problèmes
    write_file(test_file, """def foo():
    x = 1
    return 42
""", test_sandbox)
    
    # Plan d'audit exemple
    audit_plan = json.dumps({
        "summary": "Problèmes de qualité détectés",
        "total_issues": 2,
        "files_to_fix": [
            {
                "file": "example.py",
                "priority": "medium",
                "actions": [
                    {
                        "type": "add_docstring",
                        "description": "Ajouter une docstring à la fonction foo"
                    },
                    {
                        "type": "improve_quality",
                        "description": "Supprimer la variable inutilisée x"
                    }
                ]
            }
        ]
    }, indent=2)
    
    result = run_corrector_agent(
        audit_plan=audit_plan,
        target_file=test_file,
        sandbox_dir=test_sandbox
    )
    
    print("\n=== Résultat du Correcteur ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))