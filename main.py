"""
Main Entry Point - Refactoring Swarm
=====================================
Point d'entrée principal pour le système de refactoring multi-agents.

Usage:
    python main.py --target_dir "./sandbox/dataset_1"
    python main.py --target_dir "./sandbox/my_code" --max_iterations 15
"""

import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Importer l'orchestrateur
from src.orchestrator import run_refactoring_swarm
from src.utils.logger import log_experiment, ActionType


def validate_environment():
    """
    Vérifie que l'environnement est correctement configuré.
    
    Raises:
        SystemExit: Si l'environnement n'est pas valide
    """
    errors = []
    
    # Vérifier la clé API
    if not os.getenv("GOOGLE_API_KEY"):
        errors.append("❌ GOOGLE_API_KEY non trouvée dans .env")
    
    # Vérifier les imports critiques
    try:
        import google.generativeai
    except ImportError:
        errors.append("❌ google-generativeai non installé (pip install google-generativeai)")
    
    try:
        from langgraph.graph import StateGraph
    except ImportError:
        errors.append("❌ langgraph non installé (pip install langgraph)")
    
    if errors:
        print("\n".join(errors))
        print("\n💡 Conseil: Exécutez 'python check_setup.py' pour diagnostiquer.")
        sys.exit(1)


def validate_sandbox(target_dir: str) -> Path:
    """
    Valide que le répertoire sandbox existe.
    
    Args:
        target_dir: Chemin du sandbox
    
    Returns:
        Path: Chemin absolu validé
    
    Raises:
        SystemExit: Si le sandbox n'existe pas
    """
    sandbox_path = Path(target_dir).resolve()
    
    if not sandbox_path.exists():
        print(f"❌ Erreur: Le répertoire '{target_dir}' n'existe pas.")
        sys.exit(1)
    
    if not sandbox_path.is_dir():
        print(f"❌ Erreur: '{target_dir}' n'est pas un répertoire.")
        sys.exit(1)
    
    # Vérifier qu'il y a des fichiers Python
    py_files = list(sandbox_path.rglob("*.py"))
    if not py_files:
        print(f"⚠️ Avertissement: Aucun fichier Python trouvé dans '{target_dir}'")
        response = input("Continuer quand même? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    return sandbox_path


def parse_arguments():
    """
    Parse les arguments de la ligne de commande.
    
    Returns:
        argparse.Namespace: Arguments parsés
    """
    parser = argparse.ArgumentParser(
        description="🤖 Refactoring Swarm - Système multi-agents de refactoring automatique",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python main.py --target_dir "./sandbox/dataset_1"
  python main.py --target_dir "./sandbox/my_code" --max_iterations 15
  python main.py --target_dir "./sandbox/test" --verbose

Le système va:
  1. Analyser le code (Auditor)
  2. Corriger les problèmes (Fixer)
  3. Exécuter les tests (Judge)
  4. Boucler jusqu'à ce que tous les tests passent (max 10 itérations)
        """
    )
    
    parser.add_argument(
        "--target_dir",
        type=str,
        required=True,
        help="Chemin du répertoire sandbox à traiter (OBLIGATOIRE)"
    )
    
    parser.add_argument(
        "--max_iterations",
        type=int,
        default=10,
        help="Nombre maximum d'itérations de la boucle de correction (défaut: 10)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Afficher plus de détails pendant l'exécution"
    )
    
    return parser.parse_args()


def main():
    """
    Fonction principale du programme.
    """
    # Parser les arguments
    args = parse_arguments()
    
    print("="*70)
    print("🤖 REFACTORING SWARM - Multi-Agent Code Refactoring System")
    print("="*70)
    
    # Valider l'environnement
    print("\n🔍 Vérification de l'environnement...")
    validate_environment()
    print("✅ Environnement validé")
    
    # Valider le sandbox
    print(f"\n📁 Validation du sandbox: {args.target_dir}")
    sandbox_path = validate_sandbox(args.target_dir)
    print(f"✅ Sandbox validé: {sandbox_path}")
    
    # Logger le démarrage
    log_experiment(
        agent_name="System",
        model_used="gemini-2.5-flash",
        action=ActionType.ANALYSIS,
        details={
            "input_prompt": f"Starting refactoring on {args.target_dir}",
            "output_response": "System initialized successfully",
            "target_dir": str(sandbox_path),
            "max_iterations": args.max_iterations
        },
        status="SUCCESS"
    )
    
    # Exécuter le système de refactoring
    try:
        result = run_refactoring_swarm(
            sandbox_dir=str(sandbox_path),
            max_iterations=args.max_iterations
        )
        
        # Afficher le résultat final
        print("\n" + "="*70)
        if result["success"]:
            print("✅ MISSION ACCOMPLIE!")
            print(f"   Le code a été refactoré avec succès en {result['iterations_used']} itération(s).")
            exit_code = 0
        else:
            print("❌ MISSION ÉCHOUÉE")
            if result.get("error"):
                print(f"   Raison: {result['error']}")
            else:
                print(f"   {result['issues_found'] - result['issues_fixed']} problème(s) non résolu(s).")
            exit_code = 1
        
        print("="*70)
        
        # Logger la fin
        log_experiment(
            agent_name="System",
            model_used="gemini-2.5-flash",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": "Mission complete",
                "output_response": f"Success: {result['success']}",
                "final_result": result
            },
            status="SUCCESS" if result["success"] else "FAILURE"
        )
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Interruption par l'utilisateur (Ctrl+C)")
        log_experiment(
            agent_name="System",
            model_used="gemini-2.5-flash",
            action=ActionType.DEBUG,
            details={
                "input_prompt": "User interrupted execution",
                "output_response": "Interrupted",
                "error": "KeyboardInterrupt"
            },
            status="FAILURE"
        )
        sys.exit(130)
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        
        if args.verbose:
            import traceback
            traceback.print_exc()
        
        log_experiment(
            agent_name="System",
            model_used="gemini-2.5-flash",
            action=ActionType.DEBUG,
            details={
                "input_prompt": "Critical error occurred",
                "output_response": str(e),
                "error": str(e)
            },
            status="FAILURE"
        )
        
        sys.exit(1)


if __name__ == "__main__":
    main()