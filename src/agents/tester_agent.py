"""
COMPLETE Simple Tester - Fully Integrated
==========================================
Generates tests based on expected_behaviors, runs them, provides feedback.
"""

import json
from src.utils.logger import log_experiment, ActionType
from src.utils.analysis_tools import run_pytest
from src.utils.gemini_client import call_gemini, call_gemini_json
from src.utils.file_tools import write_file
from src.config import get_model_name


def load_prompt():
    """Charge le prompt système du testeur."""
    return """Tu es un expert en Test-Driven Development.
MISSION: Générer des tests qui valident la LOGIQUE métier."""


def run_tester_agent(
    expected_behaviors: list,
    sandbox_dir: str,
    model_used: str = None
) -> dict:
    """
    Version SIMPLE mais COMPLÈTE du Tester.
    Compatible avec l'orchestrateur existant.
    
    Args:
        expected_behaviors: Comportements attendus de l'Auditor (list)
        sandbox_dir: Répertoire sandbox
        model_used: Modèle LLM
    
    Returns:
        dict compatible avec orchestrateur:
        {
            "test_status": "success|failure|no_tests",
            "failing_tests": [...],
            "action": "validate|return_to_corrector",
            "should_continue": bool
        }
    """
    
    if model_used is None:
        model_used = get_model_name()
    
    print(f"🧪 [TESTER] Génération et validation des tests...")
    
    if not expected_behaviors:
        print("  ⚠️ Aucun comportement attendu - skip")
        return {
            "test_status": "no_tests",
            "failing_tests": [],
            "action": "validate",
            "should_continue": False
        }
    
    # PHASE 1: Generate Tests
    print("  📝 Phase 1: Génération des tests sémantiques...")
    
    # Batch behaviors if too many to avoid token limits
    num_behaviors = len(expected_behaviors)
    batch_size = 6  # Process max 6 functions at a time
    all_test_code = []
    all_imports = set()
    
    if num_behaviors > batch_size:
        print(f"    ℹ️ {num_behaviors} fonctions - traitement en {(num_behaviors + batch_size - 1) // batch_size} batch(s)")
        
        for i in range(0, num_behaviors, batch_size):
            batch = expected_behaviors[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            print(f"    📦 Batch {batch_num}: {len(batch)} fonction(s)")
            
            test_code = _generate_tests_for_batch(batch, model_used, sandbox_dir)
            if test_code:
                all_test_code.append(test_code)
        
        # Combine all batches
        test_code = "\n\n".join(all_test_code)
        tests_count = num_behaviors
        
    else:
        # Process all at once if small enough
        test_code = _generate_tests_for_batch(expected_behaviors, model_used, sandbox_dir)
        tests_count = num_behaviors


def _generate_tests_for_batch(batch_behaviors: list, model_used: str, sandbox_dir: str) -> str:
    """Generate tests for a batch of behaviors."""
    
    behaviors_text = json.dumps(batch_behaviors, indent=2, ensure_ascii=False)
    
    # Extract actual function names and generate imports programmatically
    function_imports = []
    function_names = []
    for behavior in batch_behaviors:
        func_name = behavior.get("function")
        file_path = behavior.get("file", "")
        if func_name and file_path:
            # Convert file path to module (e.g., "testlocal\\process.py" -> "testlocal.process")
            module_path = file_path.replace("\\", ".").replace("/", ".").replace(".py", "")
            function_imports.append(f"from {module_path} import {func_name}")
            function_names.append(func_name)
    
    imports_text = "\n".join(sorted(set(function_imports))) if function_imports else "# No imports needed"
    names_list = ", ".join(set(function_names)) if function_names else "None"
    
    generation_prompt = f"""Génère des tests pytest CONCIS qui valident la LOGIQUE métier.

=== COMPORTEMENTS ATTENDUS ===
{behaviors_text}

=== IMPORTS REQUIS ===
```python
import pytest
{imports_text}
```

=== FONCTIONS À TESTER ===
{names_list}

⚠️ Utilise EXACTEMENT ces noms de fonctions!

=== MISSION ===
Génère des tests COMPACTS (max 3 assertions/fonction):

**Format:**
```python
def test_func():
    assert func(input1) == expected1
    assert func(input2) == expected2
```

RÉPONDS EN JSON:
{{
  "test_code": "Code Python pur",
  "count": nombre
}}
"""
    
    try:
        gen_response_json = call_gemini_json(generation_prompt, model_name=model_used)
        test_code = gen_response_json.get("test_code") or gen_response_json.get("test_file_content", "")
        
        if "```python" in test_code:
            test_code = test_code.split("```python")[1].split("```")[0]
        elif "```" in test_code:
            test_code = test_code.split("```")[1].split("```")[0]
        
        return test_code.strip()
    except Exception as e:
        print(f"    ⚠️ Erreur batch: {e}")
        return ""


def run_tester_agent(
    expected_behaviors: list,
    sandbox_dir: str,
    model_used: str = None
) -> dict:
    """
    Version SIMPLE mais COMPLÈTE du Tester.
    Compatible avec l'orchestrateur existant.
    
    Args:
        expected_behaviors: Comportements attendus de l'Auditor (list)
        sandbox_dir: Répertoire sandbox
        model_used: Modèle LLM
    
    Returns:
        dict compatible avec orchestrateur:
        {
            "test_status": "success|failure|no_tests",
            "failing_tests": [...],
            "action": "validate|return_to_corrector",
            "should_continue": bool
        }
    """
    
    if model_used is None:
        model_used = get_model_name()
    
    print(f"🧪 [TESTER] Génération et validation des tests...")
    
    if not expected_behaviors:
        print("  ⚠️ Aucun comportement attendu - skip")
        return {
            "test_status": "no_tests",
            "failing_tests": [],
            "action": "validate",
            "should_continue": False
        }
    
    # PHASE 1: Generate Tests (now already done above with batching)
    print("  📝 Phase 1: Génération des tests sémantiques...")
    
    # Combine imports
    all_imports = set()
    for behavior in expected_behaviors:
        func_name = behavior.get("function")
        file_path = behavior.get("file", "")
        if func_name and file_path:
            module_path = file_path.replace("\\", ".").replace("/", ".").replace(".py", "")
            all_imports.add(f"from {module_path} import {func_name}")
    
    imports_block = "import pytest\n" + "\n".join(sorted(all_imports))
    test_code = imports_block + "\n\n" + test_code
    tests_count = num_behaviors
    
    try:
        
        # Validate test syntax before writing
        try:
            compile(test_code, "<test>", "exec")
            syntax_valid = True
        except SyntaxError as e:
            syntax_valid = False
            print(f"    ⚠️ Avertissement: Tests générés contiennent erreur de syntaxe: {e}")
            print(f"       Ligne {e.lineno}: {e.text}")
        
        # Write test file
        test_filename = "test_generated.py"
        write_file(test_filename, test_code, sandbox_dir)
        
        if syntax_valid:
            print(f"    ✅ {tests_count} test(s) généré(s) dans {test_filename}")
        else:
            print(f"    ⚠️ {tests_count} test(s) généré(s) dans {test_filename} (avec erreurs de syntaxe)")
        
        # Log generation
        log_experiment(
            agent_name="Tester",
            model_used=model_used,
            action=ActionType.GENERATION,
            details={
                "sandbox_dir": sandbox_dir,
                "input_prompt": generation_prompt,
                "output_response": gen_response,
                "tests_generated": tests_count
            },
            status="SUCCESS"
        )
        
    except Exception as e:
        print(f"    ❌ Erreur génération: {e}")
        return {
            "test_status": "error",
            "failing_tests": [],
            "action": "return_to_corrector",
            "should_continue": False,
            "error": str(e)
        }
    
    # PHASE 2: Run Tests
    print("  🏃 Phase 2: Exécution des tests...")
    
    pytest_results = run_pytest(sandbox_dir)
    
    # Analyze results
    total_tests = 0
    failed_tests = 0
    failing_test_details = []
    
    for result in pytest_results:
        if not result.get("path"):
            continue
        
        total_tests += 1
        
        if result.get("test_error"):
            failed_tests += 1
            failing_test_details.append({
                "test_file": result["path"],
                "error_message": result.get("remarks", "Test failed"),
                "return_code": result.get("code", 1)
            })
    
    # PHASE 3: Analyze Results with LLM
    print("  🔍 Phase 3: Analyse des résultats...")
    
    if failed_tests > 0:
        # Ask Gemini to analyze failures
        analysis_prompt = f"""Analyse les échecs de tests et fournis un diagnostic précis.

=== RÉSULTATS PYTEST ===
Tests totaux: {total_tests}
Tests échoués: {failed_tests}

Détails:
{json.dumps(pytest_results, indent=2, ensure_ascii=False)}

=== COMPORTEMENTS ATTENDUS ===
{behaviors_text}

=== MISSION ===
Pour chaque test qui échoue, détermine:
1. Quelle fonction est testée?
2. Quelle était la valeur attendue?
3. Quelle valeur a été obtenue?
4. DIAGNOSTIC précis du problème (ex: "division manquante", "mauvaise comparaison")

RÉPONDS EN JSON:
{{
  "test_status": "failure",
  "action": "return_to_corrector",
  "analysis": "Résumé général",
  "failing_tests": [
    {{
      "test_name": "test_calculate_average",
      "function": "calculate_average",
      "expected": 15,
      "actual": 30,
      "diagnosis": "La fonction retourne sum(numbers)=30 au lieu de sum/len=15. Division manquante."
    }}
  ]
}}
"""
        
        try:
            analysis_response_json = call_gemini_json(analysis_prompt, model_name=model_used)
            analysis_response = json.dumps(analysis_response_json, indent=2, ensure_ascii=False)
            
            # Log analysis
            log_experiment(
                agent_name="Tester",
                model_used=model_used,
                action=ActionType.ANALYSIS,
                details={
                    "sandbox_dir": sandbox_dir,
                    "input_prompt": analysis_prompt,
                    "output_response": analysis_response,
                    "total_tests": total_tests,
                    "failed_tests": failed_tests
                },
                status="SUCCESS"
            )
            
            print(f"  ❌ {failed_tests}/{total_tests} test(s) échoue(nt)")
            
            return {
                "test_status": "failure",
                "failing_tests": analysis_response_json.get("failing_tests", failing_test_details),
                "action": "return_to_corrector",
                "should_continue": True,
                "analysis": analysis_response_json.get("analysis", ""),
                "summary": f"{failed_tests}/{total_tests} tests failed"
            }
            
        except Exception as e:
            print(f"    ⚠️ Erreur analyse: {e}")
            # Fallback to basic results
            return {
                "test_status": "failure",
                "failing_tests": failing_test_details,
                "action": "return_to_corrector",
                "should_continue": True,
                "summary": f"{failed_tests}/{total_tests} tests failed"
            }
    
    else:
        # All tests passed!
        print(f"  ✅ {total_tests}/{total_tests} test(s) réussi(s)")
        
        log_experiment(
            agent_name="Tester",
            model_used=model_used,
            action=ActionType.ANALYSIS,
            details={
                "sandbox_dir": sandbox_dir,
                "input_prompt": f"Tests exécutés: {total_tests} test(s)",
                "output_response": f"SUCCÈS: Tous les {total_tests} tests ont réussi",
                "total_tests": total_tests,
                "failed_tests": 0,
                "all_tests_passed": True
            },
            status="SUCCESS"
        )
        
        return {
            "test_status": "success",
            "failing_tests": [],
            "action": "validate",
            "should_continue": False,
            "summary": "All tests passed",
            "analysis": f"Tous les {total_tests} tests passent!"
        }