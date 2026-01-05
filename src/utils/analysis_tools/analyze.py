"""
Parcourt un sandbox et lance pylint/pytest sur les fichiers Python.
"""
from pathlib import Path
from typing import Dict, Any, Optional
import json
from .pylint_runner import run_pylint
from .pytest_runner import run_pytest


def analyze_sandbox(sandbox_dir: str) -> Dict[str, Dict[str, Any]]:
    """
    Parcourt tous les fichiers Python dans sandbox_dir et ses sous-dossiers.
    - Pour chaque fichier .py :
        - lance run_pylint(file)
        - si le nom commence par 'test_', lance run_pytest(file)
    - Retourne un dictionnaire prêt pour sérialisation JSON.
    - Affiche le rapport et le sauve dans sandbox/logs/report.json.
    """
    sandbox_path = Path(sandbox_dir).resolve()
    if not sandbox_path.exists() or not sandbox_path.is_dir():
        raise ValueError(f"Le dossier sandbox spécifié n'existe pas: {sandbox_dir}")

    if sandbox_path.name != "sandbox" and not any(p.name == "sandbox" for p in sandbox_path.parents):
        raise ValueError(f"Le dossier fourni ne semble pas être un 'sandbox': {sandbox_path}")

    report: Dict[str, Dict[str, Any]] = {}

    print(f"\nAnalyse du sandbox: {sandbox_path}")

    for py_file in sandbox_path.rglob("*.py"):
        try:
            rel_key = str(py_file.relative_to(sandbox_path).as_posix())
        except Exception:
            rel_key = str(py_file)

        try:
            pylint_res = run_pylint(str(py_file))
            # run_pylint retourne (returncode:int, summary:str)
            if isinstance(pylint_res, tuple) and len(pylint_res) >= 2:
                pylint_code, pylint_summary = pylint_res[0], pylint_res[1]
            else:
                pylint_code = int(pylint_res)
                pylint_summary = ""
        except Exception as e:
            print(f"Erreur en lançant pylint pour {py_file}: {e}")
            pylint_code = -1
            pylint_summary = f"Erreur: {e}"

        pytest_result: Optional[bool] = None
        if py_file.name.startswith("test_"):
            try:
                pytest_result = run_pytest(str(py_file))
            except Exception as e:
                print(f"Erreur en lançant pytest pour {py_file}: {e}")
                pytest_result = False

    report[rel_key] = {"pylint_returncode": pylint_code, "pylint_summary": pylint_summary, "pytest_passed": pytest_result}

    report_json = json.dumps(report, indent=2, ensure_ascii=False)
    print("\n--- Rapport d'analyse ---")
    print(report_json)

    logs_dir = sandbox_path / "logs"
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        report_file = logs_dir / "report.json"
        with report_file.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Rapport sauvegardé dans: {report_file}")
    except Exception as e:
        print(f"Impossible d'écrire le rapport dans {logs_dir}: {e}")
    print("\n=== Résultat final (dictionnaire Python) ===")
    print(report)
    return report
