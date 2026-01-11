from pathlib import Path
import subprocess

def run_pytest(sandbox_root: str) -> list[dict]:
    """
    Exécute pytest sur tous les fichiers Python du sandbox, sans distinction test/src.

    Args:
        sandbox_root (str): chemin du dossier sandbox racine

    Returns:
        list[dict]: liste de résultats pytest par fichier avec code retour et remarque
    """
    sandbox_path = Path(sandbox_root).resolve()
    results = []

    # Trouver tous les fichiers Python dans le sandbox
    py_files = list(sandbox_path.rglob("*.py"))
    if not py_files:
        return [{
            "path": "",
            "code": 0,
            "remarks": "Aucun fichier Python trouvé dans le sandbox.",
            "test_error": False
        }]

    for file_p in py_files:
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

            # Détection d'erreur de test : rc != 0
            test_error = rc != 0

            # Extraire le premier message utile
            remarks = "Aucun message descriptif disponible."
            combined_output = (stdout + "\n" + stderr).splitlines()
            for line in combined_output:
                line = line.strip()
                if line and not line.startswith("=") and not line.lower().startswith("pytest"):
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
