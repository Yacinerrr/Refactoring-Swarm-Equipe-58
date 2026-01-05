"""
Lance pytest sur un fichier de test spécifique, confiné dans le dossier sandbox.
"""
from pathlib import Path
import subprocess
import os
from .common import find_sandbox_root_for_path
from typing import Optional


def run_pytest(file_path: str) -> bool:
    """
    Lance pytest sur `file_path`.
    - Vérifie que le fichier est dans un dossier 'sandbox'.
    - Exécute pytest avec cwd fixé au dossier sandbox.
    - Affiche la sortie dans la console.
    - Retourne True si tous les tests passent, False sinon.
    """
    file_p = Path(file_path)
    sandbox_root = find_sandbox_root_for_path(file_p)
    if sandbox_root is None:
        raise ValueError(f"Le fichier {file_path} n'est pas contenu dans un dossier 'sandbox'. Abandon.")
    if not file_p.exists():
        raise FileNotFoundError(f"Fichier non trouvé: {file_p}")

    try:
        rel_path = file_p.resolve().relative_to(sandbox_root.resolve())
    except Exception:
        rel_path = file_p

    cmd = ["pytest", str(rel_path), "-q"]
    print(f"\n--- Exécution pytest sur: {file_p} (cwd={sandbox_root}) ---")
    env = os.environ.copy()
    env.setdefault("XDG_CACHE_HOME", str(sandbox_root / ".cache"))
    env.setdefault("TMPDIR", str(sandbox_root / ".tmp"))

    try:
        completed = subprocess.run(cmd, cwd=str(sandbox_root), env=env, check=False)
        passed = completed.returncode == 0
        print(f"pytest terminé, returncode={completed.returncode}, passed={passed}")
        return passed
    except FileNotFoundError:
        print("Erreur: 'pytest' introuvable. Installez pytest dans votre environnement.")
        return False
    except Exception as e:
        print(f"Erreur lors de l'exécution de pytest: {e}")
        return False
