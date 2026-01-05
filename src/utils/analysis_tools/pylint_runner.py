"""
Fonction pour lancer pylint sur un fichier Python dans le sandbox.
Retourne un dictionnaire avec chemin, score, code retour et remarques.
"""
from pathlib import Path
import subprocess
import re

def run_pylint(file_path: str, sandbox_root: str) -> dict:
    """
    Exécute pylint sur un fichier Python spécifique dans le sandbox.
    
    Args:
        file_path (str): chemin du fichier à analyser
        sandbox_root (str): chemin du dossier sandbox racine

    Returns:
        dict: {
            "path": str,    # chemin relatif dans sandbox
            "score": str,   # note sur 10 sous forme de string
            "code": int,    # code retour pylint
            "remarks": str  # description des problèmes
        }
    """
    file_p = Path(file_path).resolve()
    sandbox_path = Path(sandbox_root).resolve()
    
    # chemin relatif pour pylint
    rel_path = file_p.relative_to(sandbox_path)

    cmd = ["pylint", str(rel_path), "--score=y"]

    print(f"\n--- Exécution pylint sur: {file_p} (cwd={sandbox_path}) ---")

    try:
        completed = subprocess.run(
            cmd, cwd=str(sandbox_path),
            capture_output=True, text=True, check=False
        )

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        rc = completed.returncode

        # Extraire la note sur 10
        score_match = re.search(r"Your code has been rated at\s*([0-9]+(?:\.[0-9]+)?)/10", stdout + "\n" + stderr)
        score = score_match.group(1) if score_match else "n/a"

        # Extraire la première remarque utile
        remarks = ""
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("********") or line.lower().startswith("pylint") or "rated at" in line:
                continue
            remarks = line
            break
        if not remarks:
            # fallback sur stderr
            for line in stderr.splitlines():
                line = line.strip()
                if line:
                    remarks = line
                    break
        if not remarks:
            remarks = "Aucun message descriptif disponible."

        print(f"pylint terminé, returncode={rc}, score={score} , remarks={remarks}")
        return {
            "path": str(rel_path),
            "score": score,
            "code": rc,
            "remarks": remarks
        }

    except FileNotFoundError:
        msg = "Erreur: 'pylint' introuvable. Installez pylint dans votre environnement."
        print(msg)
        return {"path": str(rel_path), "score": "n/a", "code": 127, "remarks": msg}
    except Exception as e:
        msg = f"Erreur lors de l'exécution de pylint: {e}"
        print(msg)
        return {"path": str(rel_path), "score": "n/a", "code": 1, "remarks": msg}
