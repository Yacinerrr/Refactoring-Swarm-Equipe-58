from pathlib import Path

def read_code(file_path: str) -> str:
    """
    Lit et retourne le contenu d'un fichier de code.

    Args:
        file_path (str): chemin du fichier à lire

    Returns:
        str: contenu du fichier
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Le fichier {file_path} n'existe pas")

    return path.read_text(encoding="utf-8")
