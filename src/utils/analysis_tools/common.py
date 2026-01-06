"""\nFonctions utilitaires partagées par les modules d'analyse.
"""
from pathlib import Path
from typing import Optional


def find_sandbox_root_for_path(path: Path) -> Optional[Path]:
    """
    Trouve l'ancêtre nommé 'sandbox' du chemin fourni.
    Retourne le Path absolu du dossier sandbox ou None si non trouvé.
    """
    try:
        path = path.resolve()
    except Exception:
        path = Path(path)
    for p in [path] + list(path.parents):
        if p.name == "sandbox" and p.is_dir():
            return p.resolve()
    return None
