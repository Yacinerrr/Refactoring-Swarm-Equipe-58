"""
COMPLETE Simple Corrector - Fully Integrated  
=============================================
Works with orchestrator, receives expected_behaviors AND test_feedback.
"""

import json
from src.utils.logger import log_experiment, ActionType
from src.utils.gemini_client import call_gemini, call_gemini_json
from src.utils.file_tools import read_file, write_file, extract_code_from_markdown
from src.config import get_model_name


def load_prompt():
    """Charge le prompt système du correcteur."""
    return """Tu es un expert en correction de code Python.
MISSION: Corriger le code pour qu'il fasse exactement ce qui est attendu."""


def run_corrector_agent(
    audit_plan: dict,
    expected_behaviors: list,
    test_feedback: dict,
    sandbox_dir: str,
    model_used: str = None
) -> dict:
    """
    Version SIMPLE mais COMPLÈTE du Corrector.
    Compatible avec l'orchestrateur existant.
    
    Args:
        audit_plan: Plan de refactoring de l'Auditor (dict)
        expected_behaviors: Comportements attendus (list)
        test_feedback: Feedback du Tester si tests échouent (dict ou None)
        sandbox_dir: Chemin du sandbox
        model_used: Modèle LLM
    
    Returns:
        dict compatible avec orchestrateur:
        {
            "status": "modified",
            "files_modified": [...],
            "changes": [...],
            "ready_for_testing": True
        }
    """
    
    if model_used is None:
        model_used = get_model_name()
    
    print(f"🔧 [CORRECTOR] Correction des fichiers...")
    
    # Get files to fix
    files_to_fix = audit_plan.get("files_to_fix", [])
    
    if not files_to_fix:
        print("  ℹ️ Aucun fichier à corriger")
        return {
            "status": "unchanged",
            "files_modified": [],
            "changes": [],
            "ready_for_testing": True
        }
    
    all_files_modified = []
    all_changes = []
    
    # Process each file
    for file_info in files_to_fix:
        file_path = file_info["file"]
        
        print(f"  📝 Correction de: {file_path}")
        
        try:
            # Read current code
            current_code = read_file(file_path, sandbox_dir)
            
            # Get expected behaviors for THIS file
            file_behaviors = [
                b for b in expected_behaviors 
                if b.get("file") == file_path
            ]
            
            # Build comprehensive prompt
            behaviors_text = json.dumps(file_behaviors, indent=2, ensure_ascii=False)
            
            # Add test feedback if available (from loop)
            feedback_text = ""
            if test_feedback and test_feedback.get("failing_tests"):
                feedback_text = f"""

=== FEEDBACK DES TESTS (PRIORITÉ HAUTE) ===
Les tests ont échoué. Voici les erreurs détaillées:

{json.dumps(test_feedback["failing_tests"], indent=2, ensure_ascii=False)}

IMPORTANT: Utilise ce feedback pour corriger les bugs restants!
"""
            
            input_prompt = f"""Corrige ce code Python pour qu'il fasse EXACTEMENT ce qui est attendu.

=== CODE ACTUEL ===
Fichier: {file_path}

```python
{current_code}
```

=== COMPORTEMENTS ATTENDUS ===
Pour chaque fonction, voici ce qu'elle DOIT faire:

{behaviors_text}

{feedback_text}

=== MISSION ===
1. Pour chaque fonction avec un bug logique (has_logic_bug=true):
   - Compare le code actuel avec expected_formula
   - Applique la correction (ajoute division, comparaison, etc.)
   - GARDE LE MÊME NOM DE FONCTION (ne renomme pas!)

2. Pour chaque fonction avec un problème de qualité (has_quality_issue=true):
   - Améliore les variables internes (ex: x → sum_result)
   - Ajoute/améliore les docstrings
   - ⚠️ NE RENOMME PAS LES FONCTIONS (cela casserait les tests)
   - Si vraiment nécessaire de renommer, indique-le dans le champ "rename_warning"

3. Si feedback de tests fourni:
   - PRIORISE ces corrections
   - Utilise expected vs actual pour comprendre l'erreur

4. Préserve le code non modifié:
   - Garde tous les imports identiques
   - Ne touche pas aux fonctions sans problèmes
   - Retourne le code COMPLET du fichier

APPROCHE GÉNÉRALE:

**Pour bugs logiques:**
- Identifie l'opération/formule attendue dans expected_formula
- Compare avec le code actuel (utilise current_code si disponible)
- Applique la correction minimale (ajoute/modifie seulement ce qui manque)
- Vérifie que la logique correspond maintenant à expected_behavior

**Pour problèmes de qualité:**
- Améliore les noms de variables internes (ex: noms cryptiques → noms descriptifs)
- Ajoute/améliore docstrings (description, Args, Returns, Raises)
- Améliore lisibilité (espaces, commentaires si complexe)
- N'INVENTE PAS de nouvelle logique, améliore juste la forme

**Si feedback de tests:**
- Analyse les assertions qui échouent
- Compare expected vs actual dans les messages d'erreur
- Corrige la logique pour que actual = expected

RÉPONDS EN JSON:
{{
  "file": "{file_path}",
  "status": "modified",
  "changes": [
    {{
      "function": "calculate_average",
      "type": "logic_fix",
      "description": "Ajout de la division par len(numbers)"
    }}
  ],
  "corrected_code": "Code Python complet corrigé (SANS balises markdown)",
  "rename_warning": "Optional: Si une fonction devrait être renommée mais tu ne l'as pas fait"
}}

Si aucune correction nécessaire, status="unchanged".
"""
            
            # Call Gemini
            output_response_json = call_gemini_json(input_prompt, model_name=model_used)
            output_response = json.dumps(output_response_json, indent=2, ensure_ascii=False)
            
            # Extract corrected code
            if output_response_json.get("status") == "modified":
                corrected_code = output_response_json.get("corrected_code", "")
                
                # Clean code (remove markdown if present)
                corrected_code = extract_code_from_markdown(corrected_code)
                
                if corrected_code and corrected_code != current_code:
                    # Write corrected code
                    write_file(file_path, corrected_code, sandbox_dir)
                    all_files_modified.append(file_path)
                    
                    # Track changes
                    changes = output_response_json.get("changes", [])
                    all_changes.extend(changes)
                    
                    print(f"    ✅ {len(changes)} changement(s) appliqué(s)")
                else:
                    print(f"    ℹ️ Aucune modification nécessaire")
            
            # Log
            log_experiment(
                agent_name="Corrector",
                model_used=model_used,
                action=ActionType.FIX,
                details={
                    "file_processed": file_path,
                    "input_prompt": input_prompt,
                    "output_response": output_response,
                    "had_test_feedback": (test_feedback is not None),
                    "code_modified": (output_response_json.get("status") == "modified")
                },
                status="SUCCESS"
            )
            
        except Exception as e:
            print(f"    ❌ Erreur: {e}")
            # Include required fields for logging validation
            error_input = input_prompt if 'input_prompt' in locals() else f"Correction du fichier: {file_path}"
            log_experiment(
                agent_name="Corrector",
                model_used=model_used,
                action=ActionType.DEBUG,
                details={
                    "file_processed": file_path,
                    "input_prompt": error_input,
                    "output_response": f"ERREUR: {str(e)}",
                    "error": str(e)
                },
                status="FAILURE"
            )
    
    print(f"✅ [CORRECTOR] {len(all_files_modified)} fichier(s) modifié(s)")
    
    return {
        "status": "modified" if all_files_modified else "unchanged",
        "files_modified": all_files_modified,
        "changes": all_changes,
        "ready_for_testing": True
    }