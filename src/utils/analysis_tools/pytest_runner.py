from pathlib import Path
import subprocess
import re

def run_pytest(sandbox_root: str) -> list[dict]:
    """
    Exécute pytest sur tous les fichiers de test du sandbox.

    Args:
        sandbox_root (str): chemin du dossier sandbox racine

    Returns:
        list[dict]: liste de résultats pytest par fichier avec indication d'erreur de test
    """
    sandbox_path = Path(sandbox_root).resolve()
    results = []

    # Trouver tous les fichiers de test dans les dossiers "test"
    test_files = list(sandbox_path.rglob("test_*.py"))
    if not test_files:
        return [{
            "path": "",
            "code": 0,
            "remarks": "Aucun fichier de test trouvé dans le sandbox.",
            "test_error": False
        }]

    for file_p in test_files:
        rel_path = file_p.relative_to(sandbox_path)
        cmd = ["pytest", str(rel_path), "--maxfail=1", "--disable-warnings", "-q"]

        try:
            completed = subprocess.run(
                cmd,
                cwd=str(sandbox_path),
                capture_output=True,
                text=True,
                check=False
            )

            stdout = completed.stdout or ""
            stderr = completed.stderr or ""
            rc = completed.returncode

            # Détection d'erreur de test (similaire à syntax_error)
            test_error = rc != 0

            # Première remarque utile
            remarks = "Aucun message descriptif disponible."
            for line in (stdout + "\n" + stderr).splitlines():
                line = line.strip()
                if line and not line.lower().startswith("pytest") and not line.startswith("="):
                    remarks = line
                    break

            results.append({
                "path": str(rel_path),
                "code": rc,
                "remarks": remarks,
                "test_error": test_error
            })

        except FileNotFoundError:
            results.append({
                "path": str(rel_path),
                "code": 127,
                "remarks": "pytest introuvable dans l'environnement.",
                "test_error": False
            })

        except Exception as e:
            results.append({
                "path": str(rel_path),
                "code": 1,
                "remarks": f"Erreur pytest: {e}",
                "test_error": False
            })

    return results
