from pathlib import Path

def write_code(file_path: str, new_code: str) -> None:
    """
    Écrase le contenu d'un fichier avec le code donné.

    Args:
        file_path (str): chemin du fichier (dans le repo)
        new_code (str): code à écrire dans le fichier
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Le fichier {file_path} n'existe pas")

    path.write_text(new_code, encoding="utf-8")
