"""
Parcourt un sandbox et lance pylint/pytest sur les fichiers Python.
"""
from .pylint_runner import run_pylint
from .pytest_runner import run_pytest
from pathlib import Path 
def analyze_sandbox(sandbox_root: str) -> list[dict]:
    """
    Pour chaque fichier Python du sandbox :
    - Récupère le résultat pylint
    - Récupère le résultat pytest correspondant si un test existe

    Args:
        sandbox_root (str): chemin du dossier sandbox

    Returns:
        list[dict]: liste des fichiers avec résultats combinés
    """
    pylint_results = run_pylint(sandbox_root)
    pytest_results = run_pytest(sandbox_root)

    # Dictionnaire pour accéder aux résultats pytest par chemin
    pytest_map = {r["path"]: r for r in pytest_results}

    merged = []

    for r in pylint_results:
        path = r["path"]
        # Nom de base du fichier pour chercher test correspondant
        filename = Path(path).name
        test_name = f"test_{filename}"  # convention pytest

        # Chercher pytest correspondant
        test_result = None
        for p_path, p_r in pytest_map.items():
            if Path(p_path).name == test_name:
                test_result = p_r
                break

        merged.append({
            "path": path,
            "pylint_result": r,
            "pytest_result": test_result
        })

    # Ajouter les fichiers pytest qui n'ont pas de pylint (rare)
    for p_path, p_r in pytest_map.items():
        filename = Path(p_path).name
        original_file = filename[5:] if filename.startswith("test_") else None
        if original_file:
            # Vérifier si ce fichier existe déjà dans merged
            if not any(Path(m["path"]).name == original_file for m in merged):
                merged.append({
                    "path": p_path,
                    "pylint_result": None,
                    "pytest_result": p_r
                })

    return merged

