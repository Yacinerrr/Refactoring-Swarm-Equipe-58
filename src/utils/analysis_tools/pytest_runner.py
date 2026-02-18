from pathlib import Path
import subprocess
import sys

def run_pytest(sandbox_root: str) -> list[dict]:
    """
    Exécute pytest sur tous les fichiers de test du sandbox.

    Args:
        sandbox_root (str): chemin du dossier sandbox racine

    Returns:
        list[dict]: liste de résultats pytest avec statistiques détaillées
    """
    sandbox_path = Path(sandbox_root).resolve()
    
    # Find the actual sandbox root (parent folder named "sandbox")
    actual_sandbox_root = sandbox_path
    for parent in [sandbox_path] + list(sandbox_path.parents):
        if parent.name == "sandbox":
            actual_sandbox_root = parent
            break
    
    results = []

    # Trouver tous les fichiers de test dans le sandbox
    test_files = [f for f in sandbox_path.rglob("*.py") 
                  if f.name.startswith("test_") or f.name.endswith("_test.py")]
    
    if not test_files:
        return [{
            "path": "",
            "code": 0,
            "remarks": "Aucun fichier de test trouvé dans le sandbox.",
            "test_error": False,
            "total_tests": 0,
            "passed": 0,
            "failed": 0
        }]
    
    # Check if pytest is available before running tests
    try:
        import pytest as _pytest_check
    except ImportError:
        print("  ❌ ERREUR: pytest n'est pas installé!")
        print("  📦 Installation: pip install pytest")
        return [{
            "path": "",
            "code": 127,
            "remarks": "pytest n'est pas installé. Installer avec: pip install pytest",
            "test_error": True,
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "error_type": "pytest_not_installed"
        }]

    for file_p in test_files:
        # Calculate path relative to the actual sandbox root for pytest
        rel_path = file_p.relative_to(actual_sandbox_root)
        # Use sys.executable to ensure we use the same Python as the running script
        cmd = [sys.executable, "-m", "pytest", str(rel_path), "-v", "--tb=short", "--disable-warnings"]

        try:
            completed = subprocess.run(
                cmd,
                cwd=str(actual_sandbox_root),  # Run from actual sandbox root
                capture_output=True,
                text=True,
                check=False
            )

            stdout = completed.stdout or ""
            stderr = completed.stderr or ""
            rc = completed.returncode

            # Parse pytest output to count tests
            total_tests = 0
            passed = 0
            failed = 0
            
            # Look for summary line like "1 passed, 2 failed in 0.05s"
            for line in (stdout + "\n" + stderr).splitlines():
                if " passed" in line or " failed" in line:
                    import re
                    # Extract numbers
                    passed_match = re.search(r'(\d+) passed', line)
                    failed_match = re.search(r'(\d+) failed', line)
                    
                    if passed_match:
                        passed = int(passed_match.group(1))
                    if failed_match:
                        failed = int(failed_match.group(1))
                    
                    total_tests = passed + failed
                    break
            
            # If we couldn't parse, fall back to counting PASSED/FAILED markers
            if total_tests == 0:
                for line in stdout.splitlines():
                    if "PASSED" in line:
                        passed += 1
                    elif "FAILED" in line:
                        failed += 1
                total_tests = passed + failed

            # Détection d'erreur de test : rc != 0 ou des tests ont échoué
            test_error = (rc != 0) or (failed > 0)

            # Extraire message d'erreur si présent
            remarks = "Tests exécutés avec succès."
            if test_error:
                # Get failure details
                failure_lines = []
                in_failure = False
                for line in stdout.splitlines():
                    if "FAILED" in line or "ERROR" in line:
                        in_failure = True
                        failure_lines.append(line)
                    elif in_failure and line.strip() and not line.startswith("="):
                        failure_lines.append(line)
                        if len(failure_lines) >= 5:  # Limit to first few lines
                            break
                
                if failure_lines:
                    remarks = "\n".join(failure_lines)
                else:
                    remarks = f"Tests failed (rc={rc})"

            results.append({
                "path": str(rel_path),
                "code": rc,
                "remarks": remarks,
                "test_error": test_error,
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed
            })

        except FileNotFoundError:
            results.append({
                "path": str(rel_path),
                "code": 127,
                "remarks": "pytest introuvable dans l'environnement.",
                "test_error": False,
                "total_tests": 0,
                "passed": 0,
                "failed": 0
            })

        except Exception as e:
            results.append({
                "path": str(rel_path),
                "code": 1,
                "remarks": f"Erreur pytest: {e}",
                "test_error": False,
                "total_tests": 0,
                "passed": 0,
                "failed": 0
            })

    return results
