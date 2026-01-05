"""
Helpers de Logging - Fonctions simplifiées pour l'équipe
========================================================
Ce module fournit des fonctions helper qui simplifient l'appel du logger
pour chaque agent. Utiliser ces fonctions au lieu d'appeler log_experiment directement.
"""

from src.utils.logger import log_experiment, ActionType


# ============================================================
# HELPERS POUR L'AGENT AUDITOR
# ============================================================

def log_audit(
    model: str,
    input_prompt: str,
    output_response: str,
    file_analyzed: str,
    issues_found: int = 0,
    success: bool = True,
    **extra_details
):
    """
    Log une action d'audit (analyse de code).
    
    Args:
        model: Modèle LLM utilisé (ex: "gemini-2.5-flash")
        input_prompt: Le prompt envoyé au LLM
        output_response: La réponse du LLM
        file_analyzed: Le fichier analysé
        issues_found: Nombre de problèmes trouvés
        success: True si l'analyse a réussi
        **extra_details: Détails supplémentaires optionnels
    
    Example:
        log_audit(
            model="gemini-2.5-flash",
            input_prompt="Analyse ce code...",
            output_response="J'ai trouvé 3 problèmes...",
            file_analyzed="sandbox/code.py",
            issues_found=3
        )
    """
    details = {
        "input_prompt": input_prompt,
        "output_response": output_response,
        "file_analyzed": file_analyzed,
        "issues_found": issues_found,
        **extra_details
    }
    
    log_experiment(
        agent_name="Auditor",
        model_used=model,
        action=ActionType.ANALYSIS,
        details=details,
        status="SUCCESS" if success else "FAILURE"
    )


# ============================================================
# HELPERS POUR L'AGENT FIXER
# ============================================================

def log_fix(
    model: str,
    input_prompt: str,
    output_response: str,
    file_fixed: str,
    issues_fixed: list = None,
    success: bool = True,
    **extra_details
):
    """
    Log une action de correction de code.
    
    Args:
        model: Modèle LLM utilisé
        input_prompt: Le prompt envoyé au LLM
        output_response: La réponse du LLM (code corrigé)
        file_fixed: Le fichier corrigé
        issues_fixed: Liste des problèmes corrigés
        success: True si la correction a réussi
        **extra_details: Détails supplémentaires optionnels
    
    Example:
        log_fix(
            model="gemini-2.5-flash",
            input_prompt="Corrige ce code...",
            output_response="```python\\n...\\n```",
            file_fixed="sandbox/code.py",
            issues_fixed=["docstring", "pep8"]
        )
    """
    details = {
        "input_prompt": input_prompt,
        "output_response": output_response,
        "file_fixed": file_fixed,
        "issues_fixed": issues_fixed or [],
        **extra_details
    }
    
    log_experiment(
        agent_name="Fixer",
        model_used=model,
        action=ActionType.FIX,
        details=details,
        status="SUCCESS" if success else "FAILURE"
    )


def log_generation(
    model: str,
    input_prompt: str,
    output_response: str,
    generated_type: str,
    target_file: str,
    success: bool = True,
    **extra_details
):
    """
    Log une action de génération (tests, documentation, etc.).
    
    Args:
        model: Modèle LLM utilisé
        input_prompt: Le prompt envoyé au LLM
        output_response: La réponse du LLM
        generated_type: Type de contenu généré ("tests", "docstring", "documentation")
        target_file: Le fichier cible
        success: True si la génération a réussi
        **extra_details: Détails supplémentaires optionnels
    
    Example:
        log_generation(
            model="gemini-2.5-flash",
            input_prompt="Génère des tests unitaires...",
            output_response="```python\\ndef test_...",
            generated_type="tests",
            target_file="sandbox/test_code.py"
        )
    """
    details = {
        "input_prompt": input_prompt,
        "output_response": output_response,
        "generated_type": generated_type,
        "target_file": target_file,
        **extra_details
    }
    
    log_experiment(
        agent_name="Fixer",
        model_used=model,
        action=ActionType.GENERATION,
        details=details,
        status="SUCCESS" if success else "FAILURE"
    )


# ============================================================
# HELPERS POUR L'AGENT JUDGE
# ============================================================

def log_test_execution(
    model: str,
    input_prompt: str,
    output_response: str,
    tests_passed: int = 0,
    tests_failed: int = 0,
    test_output: str = "",
    success: bool = True,
    **extra_details
):
    """
    Log une exécution de tests par le Judge.
    
    Args:
        model: Modèle LLM utilisé
        input_prompt: Le prompt envoyé au LLM (analyse des résultats)
        output_response: La réponse du LLM
        tests_passed: Nombre de tests réussis
        tests_failed: Nombre de tests échoués
        test_output: Sortie brute de pytest
        success: True si tous les tests passent
        **extra_details: Détails supplémentaires optionnels
    
    Example:
        log_test_execution(
            model="gemini-2.5-flash",
            input_prompt="Analyse ces résultats de tests...",
            output_response="Les tests échouent car...",
            tests_passed=5,
            tests_failed=2,
            test_output="FAILED test_x.py::test_func..."
        )
    """
    details = {
        "input_prompt": input_prompt,
        "output_response": output_response,
        "tests_passed": tests_passed,
        "tests_failed": tests_failed,
        "test_output": test_output,
        **extra_details
    }
    
    log_experiment(
        agent_name="Judge",
        model_used=model,
        action=ActionType.ANALYSIS,
        details=details,
        status="SUCCESS" if success else "FAILURE"
    )


def log_debug(
    model: str,
    input_prompt: str,
    output_response: str,
    error_message: str,
    error_file: str = "",
    error_line: int = 0,
    success: bool = True,
    **extra_details
):
    """
    Log une action de debug (analyse d'erreur).
    
    Args:
        model: Modèle LLM utilisé
        input_prompt: Le prompt envoyé au LLM
        output_response: La réponse du LLM (diagnostic)
        error_message: Le message d'erreur analysé
        error_file: Le fichier contenant l'erreur
        error_line: Le numéro de ligne de l'erreur
        success: True si le diagnostic a réussi
        **extra_details: Détails supplémentaires optionnels
    
    Example:
        log_debug(
            model="gemini-2.5-flash",
            input_prompt="Analyse cette erreur: TypeError...",
            output_response="L'erreur est causée par...",
            error_message="TypeError: 'NoneType' object is not iterable",
            error_file="sandbox/code.py",
            error_line=42
        )
    """
    details = {
        "input_prompt": input_prompt,
        "output_response": output_response,
        "error_message": error_message,
        "error_file": error_file,
        "error_line": error_line,
        **extra_details
    }
    
    log_experiment(
        agent_name="Judge",
        model_used=model,
        action=ActionType.DEBUG,
        details=details,
        status="SUCCESS" if success else "FAILURE"
    )


# ============================================================
# HELPER GÉNÉRIQUE
# ============================================================

def log_action(
    agent_name: str,
    model: str,
    action: ActionType,
    input_prompt: str,
    output_response: str,
    success: bool = True,
    **extra_details
):
    """
    Helper générique pour logger n'importe quelle action.
    
    Args:
        agent_name: Nom de l'agent
        model: Modèle LLM utilisé
        action: Type d'action (ActionType enum)
        input_prompt: Le prompt envoyé au LLM
        output_response: La réponse du LLM
        success: True si l'action a réussi
        **extra_details: Tous les autres détails
    
    Example:
        log_action(
            agent_name="Auditor",
            model="gemini-2.5-flash",
            action=ActionType.ANALYSIS,
            input_prompt="...",
            output_response="...",
            custom_field="valeur"
        )
    """
    details = {
        "input_prompt": input_prompt,
        "output_response": output_response,
        **extra_details
    }
    
    log_experiment(
        agent_name=agent_name,
        model_used=model,
        action=action,
        details=details,
        status="SUCCESS" if success else "FAILURE"
    )
