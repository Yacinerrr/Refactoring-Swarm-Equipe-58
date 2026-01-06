from pathlib import Path
import subprocess
import re


def run_pylint(sandbox_root: str) -> list[dict]:
    """
    Exécute pylint sur tous les fichiers Python du sandbox.

    Args:
        sandbox_root (str): chemin du dossier sandbox racine

    Returns:
        list[dict]: liste de résultats pylint par fichier avec indication d'erreur de syntaxe
    """
    sandbox_path = Path(sandbox_root).resolve()
    results = []

    # Trouver tous les fichiers .py dans tous les sous-dossiers
    py_files = list(sandbox_path.rglob("*.py"))

    if not py_files:
        return [{
            "path": "",
            "score": "n/a",
            "code": 0,
            "remarks": "Aucun fichier Python trouvé dans le sandbox.",
            "syntax_error": False
        }]

    for file_p in py_files:
        rel_path = file_p.relative_to(sandbox_path)
        cmd = ["pylint", str(rel_path), "--score=y"]

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

            # Détection d'erreur de syntaxe
            syntax_error = False
            syntax_patterns = [
                r"SyntaxError",
                r"invalid syntax",
                r"unexpected EOF while parsing"
            ]
            combined_output = stdout + "\n" + stderr
            for pattern in syntax_patterns:
                if re.search(pattern, combined_output):
                    syntax_error = True
                    break

            # Extraire la note pylint
            score_match = re.search(
                r"rated at\s*([0-9]+(?:\.[0-9]+)?)/10",
                combined_output
            )
            score = score_match.group(1) if score_match else "n/a"

            # Première remarque utile
            remarks = "Aucun message descriptif disponible."
            for line in stdout.splitlines():
                line = line.strip()
                if line and not (
                    line.startswith("********")
                    or "rated at" in line
                    or line.lower().startswith("pylint")
                ):
                    remarks = line
                    break

            results.append({
                "path": str(rel_path),
                "score": score,
                "code": rc,
                "remarks": remarks,
                "syntax_error": syntax_error
            })

        except FileNotFoundError:
            results.append({
                "path": str(rel_path),
                "score": "n/a",
                "code": 127,
                "remarks": "pylint introuvable dans l'environnement.",
                "syntax_error": False
            })

        except Exception as e:
            results.append({
                "path": str(rel_path),
                "score": "n/a",
                "code": 1,
                "remarks": f"Erreur pylint: {e}",
                "syntax_error": False
            })

    return results
