"""
File Tools - Outils de lecture/écriture sécurisés pour le sandbox
==================================================================
Ce module fournit des fonctions pour manipuler les fichiers de manière sécurisée
en garantissant que toutes les opérations restent dans le sandbox.
"""

import os
from pathlib import Path
from typing import Optional, List


class SandboxSecurityError(Exception):
    """Exception levée quand une opération tente de sortir du sandbox."""
    pass


def get_sandbox_root(target_path: str) -> Path:
    """
    Trouve et valide le dossier sandbox racine.
    
    Args:
        target_path: Chemin vers un dossier dans le sandbox
    
    Returns:
        Path: Chemin absolu du dossier sandbox
    
    Raises:
        SandboxSecurityError: Si le sandbox n'est pas trouvé
    """
    path = Path(target_path).resolve()
    
    # Chercher le dossier "sandbox" dans les parents
    for parent in [path] + list(path.parents):
        if parent.name == "sandbox":
            return parent
    
    # Si on ne trouve pas "sandbox", on considère que target_path EST le sandbox
    return path


def validate_sandbox_path(file_path: str, sandbox_root: Path) -> Path:
    """
    Valide qu'un chemin est bien dans le sandbox.
    
    Args:
        file_path: Chemin du fichier à valider
        sandbox_root: Racine du sandbox
    
    Returns:
        Path: Chemin absolu validé
    
    Raises:
        SandboxSecurityError: Si le chemin sort du sandbox
    """
    # Résoudre le chemin absolu
    abs_path = (sandbox_root / file_path).resolve()
    
    # Vérifier que le chemin est bien dans le sandbox
    try:
        abs_path.relative_to(sandbox_root)
    except ValueError:
        raise SandboxSecurityError(
            f"❌ SÉCURITÉ: Tentative d'accès en dehors du sandbox!\n"
            f"   Fichier: {abs_path}\n"
            f"   Sandbox: {sandbox_root}"
        )
    
    return abs_path


def read_file(file_path: str, sandbox_root: str) -> str:
    """
    Lit un fichier de manière sécurisée depuis le sandbox.
    
    Args:
        file_path: Chemin relatif du fichier dans le sandbox
        sandbox_root: Racine du sandbox
    
    Returns:
        str: Contenu du fichier
    
    Raises:
        SandboxSecurityError: Si tentative de lecture hors sandbox
        FileNotFoundError: Si le fichier n'existe pas
    """
    sandbox_path = get_sandbox_root(sandbox_root)
    abs_path = validate_sandbox_path(file_path, sandbox_path)
    
    if not abs_path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {file_path}")
    
    if not abs_path.is_file():
        raise ValueError(f"Le chemin n'est pas un fichier: {file_path}")
    
    with open(abs_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(file_path: str, content: str, sandbox_root: str) -> bool:
    """
    Écrit dans un fichier de manière sécurisée dans le sandbox.
    
    Args:
        file_path: Chemin relatif du fichier dans le sandbox
        content: Contenu à écrire
        sandbox_root: Racine du sandbox
    
    Returns:
        bool: True si l'écriture a réussi
    
    Raises:
        SandboxSecurityError: Si tentative d'écriture hors sandbox
    """
    sandbox_path = get_sandbox_root(sandbox_root)
    abs_path = validate_sandbox_path(file_path, sandbox_path)
    
    # Créer les dossiers parents si nécessaire
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(abs_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True


def list_python_files(sandbox_root: str, exclude_tests: bool = False) -> List[str]:
    """
    Liste tous les fichiers Python dans le sandbox.
    
    Args:
        sandbox_root: Racine du sandbox
        exclude_tests: Si True, exclut les fichiers test_*.py
    
    Returns:
        List[str]: Liste des chemins relatifs des fichiers Python
    """
    sandbox_path = get_sandbox_root(sandbox_root)
    py_files = []
    
    for file_path in sandbox_path.rglob("*.py"):
        rel_path = file_path.relative_to(sandbox_path)
        
        if exclude_tests and file_path.name.startswith("test_"):
            continue
        
        py_files.append(str(rel_path))
    
    return py_files


def backup_file(file_path: str, sandbox_root: str) -> Optional[str]:
    """
    Crée une sauvegarde d'un fichier avant modification.
    
    Args:
        file_path: Chemin relatif du fichier
        sandbox_root: Racine du sandbox
    
    Returns:
        str: Chemin de la sauvegarde ou None si échec
    """
    try:
        content = read_file(file_path, sandbox_root)
        backup_path = f"{file_path}.backup"
        write_file(backup_path, content, sandbox_root)
        return backup_path
    except Exception as e:
        print(f"⚠️ Impossible de créer une sauvegarde: {e}")
        return None


def extract_code_from_markdown(text: str) -> str:
    """
    Extrait le code Python d'un bloc markdown ```python ... ```.
    
    Args:
        text: Texte contenant potentiellement du code markdown
    
    Returns:
        str: Code extrait, ou texte original si pas de markdown
    """
    # Chercher un bloc ```python ... ```
    import re
    
    pattern = r'```python\s*(.*?)\s*```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        return matches[0].strip()
    
    # Chercher un bloc ``` ... ``` sans langage
    pattern = r'```\s*(.*?)\s*```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        return matches[0].strip()
    
    # Pas de markdown trouvé, retourner le texte tel quel
    return text.strip()


# Test du module
if __name__ == "__main__":
    print("🧪 Test des outils de fichiers...")
    
    # Test de sécurité
    try:
        sandbox = "./sandbox/test"
        os.makedirs(sandbox, exist_ok=True)
        
        # Test d'écriture
        write_file("test.py", "print('Hello')", sandbox)
        print("✅ Écriture réussie")
        
        # Test de lecture
        content = read_file("test.py", sandbox)
        print(f"✅ Lecture réussie: {content[:20]}...")
        
        # Test de sécurité (doit échouer)
        try:
            write_file("../../evil.py", "malicious", sandbox)
            print("❌ ERREUR: Sécurité compromise!")
        except SandboxSecurityError:
            print("✅ Sécurité fonctionne: accès refusé hors sandbox")
        
        print("\n✅ Tous les tests passent!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")