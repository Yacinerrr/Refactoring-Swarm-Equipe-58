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


def _generate_tests_for_batch(batch_behaviors: list, model_used: str, sandbox_dir: str) -> tuple:
    """Generate tests for a batch of behaviors.
    
    Returns:
        tuple: (test_code, generation_prompt, gen_response_str)
    """
    
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
    
    generation_prompt = f"""Génère des tests pytest PRÉCIS et STABLES qui valident la LOGIQUE métier.

=== COMPORTEMENTS ATTENDUS ===
{behaviors_text}

=== IMPORTS REQUIS ===
```python
import pytest
{imports_text}
```

=== FONCTIONS À TESTER ===
{names_list}

⚠️ RÈGLES CRITIQUES:
1. Utilise EXACTEMENT ces noms de fonctions (ne les invente pas)!
2. Tests DOIVENT correspondre à expected_behavior et expected_formula
3. Pour les exceptions, regarde bug_description pour savoir quel type d'erreur est attendu
4. Génère des tests STABLES qui ne changeront pas entre exécutions

=== MISSION ===
Pour chaque fonction, génère 2-4 tests qui valident:

**Tests normaux:**
- Cas typiques basés sur expected_formula
- Exemple: Si expected_formula="(part/total)*100", teste calculate_percentage(50,100)==50.0

**Tests limites:**
- Cas aux limites (zéro, négatifs, listes vides)
- Si has_logic_bug=true et bug_description mentionne "division by zero":
  - Teste division par zéro avec pytest.raises(ValueError) ou ZeroDivisionError
  - Choisis le type basé sur bug_description

**Format de sortie:**
```python
def test_function_name():
    # Test cas normal
    assert function_name(input) == expected_output
    
    # Test edge case
    with pytest.raises(ExceptionType):  # Si applicable
        function_name(invalid_input)
```

RÉPONDS EN JSON:
{{
  "test_code": "Code Python pur (SANS balises markdown, SANS imports)",
  "count": nombre_de_fonctions_testées
}}

⚠️ IMPORTANT: Ne génère QUE les fonctions de test, PAS les imports (ils seront ajoutés automatiquement).
"""
    
    try:
        gen_response_json = call_gemini_json(generation_prompt, model_name=model_used)
        gen_response_str = json.dumps(gen_response_json, indent=2, ensure_ascii=False)
        test_code = gen_response_json.get("test_code") or gen_response_json.get("test_file_content", "")
        
        if "```python" in test_code:
            test_code = test_code.split("```python")[1].split("```")[0]
        elif "```" in test_code:
            test_code = test_code.split("```")[1].split("```")[0]
        
        return test_code.strip(), generation_prompt, gen_response_str
    except Exception as e:
        print(f"    ⚠️ Erreur batch: {e}")
        return "", generation_prompt, f"Error: {str(e)}"


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
    
    # PHASE 1: Generate Tests with batching
    print("  📝 Phase 1: Génération des tests sémantiques...")
    
    # Batch behaviors if too many to avoid token limits
    num_behaviors = len(expected_behaviors)
    batch_size = 6  # Process max 6 functions at a time
    all_test_code = []
    all_prompts = []
    all_responses = []
    
    if num_behaviors > batch_size:
        print(f"    ℹ️ {num_behaviors} fonctions - traitement en {(num_behaviors + batch_size - 1) // batch_size} batch(s)")
        
        for i in range(0, num_behaviors, batch_size):
            batch = expected_behaviors[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            print(f"    📦 Batch {batch_num}: {len(batch)} fonction(s)")
            
            batch_test_code, batch_prompt, batch_response = _generate_tests_for_batch(batch, model_used, sandbox_dir)
            if batch_test_code:
                all_test_code.append(batch_test_code)
                all_prompts.append(batch_prompt)
                all_responses.append(batch_response)
        
        # Combine all batches
        test_code = "\n\n".join(all_test_code) if all_test_code else ""
        generation_prompt = "\n\n---NEXT BATCH---\n\n".join(all_prompts) if all_prompts else ""
        gen_response = "\n\n---NEXT BATCH---\n\n".join(all_responses) if all_responses else ""
        
    else:
        # Process all at once if small enough
        test_code, generation_prompt, gen_response = _generate_tests_for_batch(expected_behaviors, model_used, sandbox_dir)
        if not test_code:
            test_code = ""
    
    # Add imports at the top
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
        
        # Write test file only if it doesn't exist or if it's the first iteration
        # This prevents regeneration which creates a moving target
        from pathlib import Path
        sandbox_path = Path(sandbox_dir).resolve()
        
        # Check if we're in a subdirectory of sandbox
        test_filename = "test_generated.py"
        if sandbox_path.parent.name == "sandbox":
            # We're directly in sandbox (e.g., sandbox/testlocal)
            # Write test file relative to sandbox root
            subdir_name = sandbox_path.name
            test_file_path = f"{subdir_name}/{test_filename}"
        elif sandbox_path.name == "sandbox":
            # We're at the sandbox root
            test_file_path = test_filename
        else:
            # Try to find the relative path from sandbox
            for parent in sandbox_path.parents:
                if parent.name == "sandbox":
                    rel_path = sandbox_path.relative_to(parent)
                    test_file_path = f"{rel_path}/{test_filename}".replace("\\", "/")
                    break
            else:
                # Fallback to just the filename
                test_file_path = test_filename
        
        # Check if test file already exists
        actual_sandbox_root = sandbox_path
        for parent in [sandbox_path] + list(sandbox_path.parents):
            if parent.name == "sandbox":
                actual_sandbox_root = parent
                break
        
        test_file_full_path = actual_sandbox_root / test_file_path
        
        if test_file_full_path.exists():
            print(f"    ℹ️ Tests déjà générés ({test_file_path}) - réutilisation")
            # Don't overwrite - use existing tests
        else:
            # First time - write the tests
            write_file(test_file_path, test_code, sandbox_dir)
            
            if syntax_valid:
                print(f"    ✅ {tests_count} test(s) généré(s) dans {test_file_path}")
            else:
                print(f"    ⚠️ {tests_count} test(s) généré(s) dans {test_file_path} (avec erreurs de syntaxe)")
        
        # Log generation
        log_experiment(
            agent_name="Tester",
            model_used=model_used,
            action=ActionType.GENERATION,
            details={
                "sandbox_dir": sandbox_dir,
                "input_prompt": generation_prompt,
                "output_response": gen_response,
                "tests_generated": tests_count,
                "num_behaviors": num_behaviors
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
    
    # Check for pytest installation error
    if pytest_results and pytest_results[0].get("error_type") == "pytest_not_installed":
        print(f"  ❌ ERREUR: {pytest_results[0].get('remarks')}")
        return {
            "test_status": "error",
            "failing_tests": [],
            "action": "validate",
            "should_continue": False,
            "error": "pytest not installed",
            "summary": "Cannot run tests - pytest not installed"
        }
    
    # Analyze results - sum up all test counts from all test files
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    failing_test_details = []
    
    for result in pytest_results:
        path = result.get("path", "")
        if not path:
            continue
        
        # Sum up test counts from this file
        file_total = result.get("total_tests", 0)
        file_passed = result.get("passed", 0)
        file_failed = result.get("failed", 0)
        
        total_tests += file_total
        passed_tests += file_passed
        failed_tests += file_failed
        
        if result.get("test_error") and file_failed > 0:
            failing_test_details.append({
                "test_file": result["path"],
                "error_message": result.get("remarks", "Test failed"),
                "return_code": result.get("code", 1),
                "failed_count": file_failed,
                "total_count": file_total
            })
    
    # Handle case where no tests were found
    if total_tests == 0:
        print("  ⚠️ Aucun test trouvé - validation par défaut")
        return {
            "test_status": "no_tests",
            "failing_tests": [],
            "action": "validate",
            "should_continue": False,
            "summary": "No tests found"
        }
    
    # PHASE 3: Analyze Results with LLM
    print("  🔍 Phase 3: Analyse des résultats...")
    
    # Prepare behaviors text for analysis
    behaviors_text = json.dumps(expected_behaviors, indent=2, ensure_ascii=False)
    
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
                    "passed_tests": passed_tests,
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
        print(f"  ✅ {passed_tests}/{total_tests} test(s) réussi(s)")
        
        log_experiment(
            agent_name="Tester",
            model_used=model_used,
            action=ActionType.ANALYSIS,
            details={
                "sandbox_dir": sandbox_dir,
                "input_prompt": f"Tests exécutés: {total_tests} test(s)",
                "output_response": f"SUCCÈS: {passed_tests}/{total_tests} tests ont réussi",
                "total_tests": total_tests,
                "passed_tests": passed_tests,
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