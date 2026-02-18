"""
COMPLETE Simple Auditor - Fully Integrated
===========================================
This version works with the existing orchestrator and state management.
"""

import json
from pathlib import Path
from src.utils.logger import log_experiment, ActionType
from src.utils.gemini_client import call_gemini_json
from src.utils.file_tools import read_file, list_python_files
from src.config import get_model_name


def load_prompt():
    """Charge le prompt système de l'auditeur."""
    # Use existing prompt or inline
    return """Tu es un expert en analyse sémantique de code Python.
MISSION: Analyser le code et comprendre l'intent de chaque fonction."""


def run_auditor_agent(sandbox_dir: str, model_used: str = None) -> dict:
    """
    Version SIMPLE mais COMPLÈTE de l'Auditor.
    Compatible avec l'orchestrateur existant.
    
    Args:
        sandbox_dir: Chemin du sandbox
        model_used: Modèle LLM (None = config)
    
    Returns:
        dict compatible avec l'orchestrateur:
        {
            "status": "success",
            "refactoring_plan": {...},
            "expected_behaviors": [...],
            "issues_found": int
        }
    """
    
    if model_used is None:
        model_used = get_model_name()
    
    print(f"🔍 [AUDITOR] Analyse sémantique de {sandbox_dir}...")
    
    # Get all Python files (exclude tests)
    py_files = list_python_files(sandbox_dir, exclude_tests=True)
    
    if not py_files:
        print("  ⚠️ Aucun fichier Python trouvé")
        return {
            "status": "success",
            "refactoring_plan": {"summary": "No files", "total_issues": 0, "files_to_fix": []},
            "expected_behaviors": [],
            "issues_found": 0
        }
    
    all_expected_behaviors = []
    all_files_to_fix = []
    total_issues = 0
    
    # Analyze each file with ONE LLM call per file
    for file_path in py_files:
        print(f"  📄 Analyse de: {file_path}")
        
        try:
            code = read_file(file_path, sandbox_dir)
            
            # ONE COMPREHENSIVE LLM CALL
            input_prompt = f"""Analyse ce code Python de manière complète.

=== FICHIER ===
{file_path}

=== CODE ===
```python
{code}
```

=== MISSION ===
Pour CHAQUE fonction dans ce code:

1. **COMPRENDS L'INTENT SÉMANTIQUE**
   - Que DEVRAIT faire cette fonction? (basé sur nom, docstring, paramètres)
   - Quelle est la formule/algorithme attendu?
   
2. **DÉTECTE LES BUGS LOGIQUES ET QUALITÉ**
   - Compare le code actuel avec l'intent attendu
   - Y a-t-il des opérations manquantes? (division, comparaison, etc.)
   - Y a-t-il des erreurs de syntaxe?
   - Y a-t-il des problèmes de qualité? (noms non descriptifs, variables sans sens, docstring manquante)

3. **PROPOSE DES STRATÉGIES DE TEST**
   - Comment tester cette fonction pour valider la LOGIQUE?
   - Quels inputs/outputs utiliser?

MÉTHODOLOGIE D'ANALYSE:

1. Lis le nom de la fonction + docstring + paramètres
2. Déduis l'intention sémantique (que DEVRAIT-elle faire?)
3. Lis l'implémentation actuelle
4. Compare: intention vs implémentation
5. Détecte les écarts:
   - Opérations manquantes (ex: calcul incomplet, pas de validation)
   - Logique incorrecte (ex: retourne mauvaise valeur, mauvaise condition)
   - Syntaxe invalide (ex: deux-points manquants, indentation)
   - Qualité faible (ex: noms cryptiques, pas de docstring)

6. Pour les tests, pense aux:
   - Cas normaux (inputs valides typiques)
   - Cas limites (valeurs extrêmes, collections vides)
   - Cas d'erreur (inputs invalides)

RÉPONDS EN JSON:
{{
  "functions": [
    {{
      "name": "nom_fonction",
      "line": 5,
      "current_code": "Code actuel de la fonction (pour contexte)",
      "semantic_intent": "description de ce qu'elle devrait faire",
      "expected_behavior": "comportement attendu détaillé",
      "expected_formula": "formule ou code attendu",
      "has_logic_bug": true,
      "bug_description": "description du bug si has_logic_bug=true",
      "has_quality_issue": true,
      "quality_suggestions": "comment améliorer la qualité si has_quality_issue=true",
      "suggested_name": "nom suggéré si renommage nécessaire (ATTENTION: peut casser les tests)",
      "test_strategy": "comment tester",
      "test_samples": [
        {{"input": "exemple d'input", "expected_output": "résultat attendu", "reasoning": "pourquoi"}}
      ]
    }}
  ],
  "file_issues": {{
    "syntax_errors": 0,
    "logic_bugs": 2,
    "quality_issues": 1
  }}
}}

NOTE IMPORTANTE:
- has_logic_bug = code ne fait PAS ce qu'il devrait (bug fonctionnel)
- has_quality_issue = code fonctionne mais mal écrit (nommage, style)
- Pour les bugs logiques, fournis expected_formula
- Pour la qualité, fournis quality_suggestions
- N'INVENTE PAS de code, cite le code réel que tu vois
"""
            
            # Call Gemini
            output_response_json = call_gemini_json(input_prompt, model_name=model_used)
            output_response = json.dumps(output_response_json, indent=2, ensure_ascii=False)
            
            # Process results
            functions = output_response_json.get("functions", [])
            file_issues = output_response_json.get("file_issues", {})
            
            file_total_issues = sum(file_issues.values())
            total_issues += file_total_issues
            
            # Build expected_behaviors for Corrector and Tester
            for func in functions:
                all_expected_behaviors.append({
                    "function": func.get("name"),
                    "file": file_path,
                    "line": func.get("line"),
                    "current_code": func.get("current_code", ""),
                    "semantic_intent": func.get("semantic_intent"),
                    "expected_behavior": func.get("expected_behavior"),
                    "expected_formula": func.get("expected_formula"),
                    "has_logic_bug": func.get("has_logic_bug", False),
                    "bug_description": func.get("bug_description"),
                    "has_quality_issue": func.get("has_quality_issue", False),
                    "quality_suggestions": func.get("quality_suggestions"),
                    "suggested_name": func.get("suggested_name"),
                    "test_strategy": func.get("test_strategy"),
                    "test_samples": func.get("test_samples", [])
                })
            
            # Build files_to_fix if there are issues
            if file_total_issues > 0:
                file_actions = []
                
                for func in functions:
                    if func.get("has_logic_bug") or func.get("has_quality_issue"):
                        action_desc = func.get("bug_description") if func.get("has_logic_bug") else func.get("quality_suggestions", "Quality improvement needed")
                        action_type = "logic_bug" if func.get("has_logic_bug") else "quality_issue"
                        
                        file_actions.append({
                            "function": func["name"],
                            "type": action_type,
                            "description": action_desc,
                            "expected_fix": func.get("expected_formula") or func.get("suggested_name", ""),
                            "current_code": func.get("current_code", "")
                        })
                
                all_files_to_fix.append({
                    "file": file_path,
                    "priority": "high" if file_issues.get("syntax_errors", 0) > 0 else "medium",
                    "issues_count": file_total_issues,
                    "functions": [
                        {
                            "name": f["name"],
                            "semantic_intent": f.get("semantic_intent"),
                            "expected_behavior": f.get("expected_behavior"),
                            "current_issue": {
                                "type": f.get("bug_type") or f.get("quality_issue_type"),
                                "description": f.get("bug_description") or f.get("suggested_refactoring"),
                                "expected_code": f.get("expected_formula") or f.get("suggested_name")
                            }
                        }
                        for f in functions if f.get("has_logic_bug") or f.get("has_quality_issue")
                    ],
                    "actions": file_actions
                })
            
            # Log this file's analysis
            log_experiment(
                agent_name="Auditor",
                model_used=model_used,
                action=ActionType.ANALYSIS,
                details={
                    "file_analyzed": file_path,
                    "input_prompt": input_prompt,
                    "output_response": output_response,
                    "functions_found": len(functions),
                    "issues_found": file_total_issues
                },
                status="SUCCESS"
            )
            
            print(f"    ✅ {len(functions)} fonction(s), {file_total_issues} problème(s)")
            
        except Exception as e:
            print(f"    ❌ Erreur: {e}")
            # Include required fields for logging validation
            error_input = input_prompt if 'input_prompt' in locals() else f"Analyse du fichier: {file_path}"
            log_experiment(
                agent_name="Auditor",
                model_used=model_used,
                action=ActionType.DEBUG,
                details={
                    "file_analyzed": file_path,
                    "input_prompt": error_input,
                    "output_response": f"ERREUR: {str(e)}",
                    "error": str(e)
                },
                status="FAILURE"
            )
    
    # Build final refactoring plan (compatible with orchestrator)
    refactoring_plan = {
        "summary": f"Analysé {len(py_files)} fichier(s), trouvé {total_issues} problème(s)",
        "total_issues": total_issues,
        "files_to_fix": all_files_to_fix
        # DON'T put expected_behaviors here - it goes at top level!
    }
    
    print(f"✅ [AUDITOR] Complete:")
    print(f"   - {len(all_expected_behaviors)} fonction(s) analysée(s)")
    print(f"   - {total_issues} problème(s) détecté(s)")
    
    return {
        "status": "success",
        "sandbox": sandbox_dir,
        "refactoring_plan": refactoring_plan,
        "expected_behaviors": all_expected_behaviors,  # For Corrector & Tester
        "files_analyzed": len(py_files),
        "issues_found": total_issues
    }