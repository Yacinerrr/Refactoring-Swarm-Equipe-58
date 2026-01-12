"""
Test System - Vérification rapide du système complet
=====================================================
Ce script teste tous les composants pour vérifier que tout fonctionne.
"""

import os
import sys
from pathlib import Path

def test_imports():
    """Test que tous les modules s'importent correctement."""
    print("\n🧪 Test 1: Imports des modules...")
    
    try:
        from src.utils.gemini_client import call_gemini_json
        print("  ✅ gemini_client")
    except Exception as e:
        print(f"  ❌ gemini_client: {e}")
        return False
    
    try:
        from src.utils.file_tools import read_file, write_file
        print("  ✅ file_tools")
    except Exception as e:
        print(f"  ❌ file_tools: {e}")
        return False
    
    try:
        from src.refactoring_state import create_initial_state
        print("  ✅ refactoring_state")
    except Exception as e:
        print(f"  ❌ refactoring_state: {e}")
        return False
    
    try:
        from src.orchestrator import build_refactoring_graph
        print("  ✅ orchestrator")
    except Exception as e:
        print(f"  ❌ orchestrator: {e}")
        return False
    
    try:
        from src.agents.auditor_agent import run_auditor_agent
        from src.agents.corrector_agent import run_corrector_agent
        from src.agents.tester_agent import run_tester_agent
        print("  ✅ agents (auditor, corrector, tester)")
    except Exception as e:
        print(f"  ❌ agents: {e}")
        return False
    
    print("✅ Tous les imports réussis!")
    return True


def test_gemini_connection():
    """Test la connexion à l'API Gemini."""
    print("\n🧪 Test 2: Connexion Gemini...")
    
    try:
        from src.utils.gemini_client import call_gemini_json
        
        response = call_gemini_json(
            'Réponds avec ce JSON exact: {"status": "ok", "test": "passed"}'
        )
        
        if response.get("status") == "ok":
            print("  ✅ API Gemini fonctionne!")
            return True
        else:
            print(f"  ⚠️ Réponse inattendue: {response}")
            return False
            
    except Exception as e:
        print(f"  ❌ Erreur Gemini: {e}")
        print("  💡 Vérifiez votre GOOGLE_API_KEY dans .env")
        return False


def test_file_security():
    """Test la sécurité du sandbox."""
    print("\n🧪 Test 3: Sécurité du sandbox...")
    
    try:
        from src.utils.file_tools import write_file, SandboxSecurityError
        
        # Créer un sandbox de test
        test_sandbox = "./sandbox/security_test"
        os.makedirs(test_sandbox, exist_ok=True)
        
        # Test écriture normale (doit réussir)
        write_file("test.txt", "Hello", test_sandbox)
        print("  ✅ Écriture dans sandbox: OK")
        
        # Test écriture hors sandbox (doit échouer)
        try:
            write_file("../../evil.txt", "Malicious", test_sandbox)
            print("  ❌ DANGER: Écriture hors sandbox autorisée!")
            return False
        except SandboxSecurityError:
            print("  ✅ Sécurité: Écriture hors sandbox bloquée")
        
        # Nettoyage
        import shutil
        shutil.rmtree(test_sandbox)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur test sécurité: {e}")
        return False


def test_logging():
    """Test que le système de logging fonctionne."""
    print("\n🧪 Test 4: Système de logging...")
    
    try:
        from src.utils.logger import log_experiment, ActionType
        
        # Logger un test
        log_experiment(
            agent_name="TestAgent",
            model_used="test-model",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": "Test prompt",
                "output_response": "Test response"
            },
            status="SUCCESS"
        )
        
        # Vérifier que le fichier existe
        log_file = Path("logs/experiment_data.json")
        if log_file.exists():
            print("  ✅ Logs créés correctement")
            
            # Vérifier le contenu
            import json
            with open(log_file, 'r') as f:
                data = json.load(f)
                if len(data) > 0:
                    print(f"  ✅ {len(data)} entrée(s) de log trouvée(s)")
                    return True
        
        print("  ❌ Fichier de logs non créé")
        return False
        
    except Exception as e:
        print(f"  ❌ Erreur logging: {e}")
        return False


def test_analysis_tools():
    """Test les outils d'analyse."""
    print("\n🧪 Test 5: Outils d'analyse...")
    
    try:
        from src.utils.analysis_tools import run_pylint, run_pytest
        
        # Créer un fichier Python simple
        test_sandbox = "./sandbox/analysis_test"
        os.makedirs(test_sandbox, exist_ok=True)
        
        test_file = Path(test_sandbox) / "simple.py"
        test_file.write_text("print('Hello')\n")
        
        # Test pylint
        pylint_results = run_pylint(test_sandbox)
        if pylint_results:
            print("  ✅ Pylint fonctionne")
        else:
            print("  ⚠️ Pylint n'a pas retourné de résultats")
        
        # Test pytest
        pytest_results = run_pytest(test_sandbox)
        if pytest_results:
            print("  ✅ Pytest fonctionne")
        else:
            print("  ⚠️ Pytest n'a pas retourné de résultats")
        
        # Nettoyage
        import shutil
        shutil.rmtree(test_sandbox)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur outils d'analyse: {e}")
        return False


def test_langgraph():
    """Test que LangGraph peut créer un graphe."""
    print("\n🧪 Test 6: LangGraph...")
    
    try:
        from langgraph.graph import StateGraph
        from src.refactoring_state import RefactoringState
        
        # Créer un graphe simple
        workflow = StateGraph(RefactoringState)
        print("  ✅ LangGraph importé et fonctionnel")
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur LangGraph: {e}")
        print("  💡 Installez: pip install langgraph")
        return False


def main():
    """Exécute tous les tests."""
    print("="*60)
    print("🔍 TEST DU SYSTÈME REFACTORING SWARM")
    print("="*60)
    
    tests = [
        ("Imports", test_imports),
        ("Gemini API", test_gemini_connection),
        ("Sécurité Sandbox", test_file_security),
        ("Logging", test_logging),
        ("Outils d'analyse", test_analysis_tools),
        ("LangGraph", test_langgraph),
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ Erreur critique dans {name}: {e}")
            results[name] = False
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    print("="*60)
    print(f"Résultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n🎉 TOUS LES TESTS PASSENT!")
        print("Vous pouvez maintenant utiliser:")
        print("  python main.py --target_dir './sandbox/votre_dataset'")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) échoué(s)")
        print("Veuillez corriger les problèmes avant de continuer.")
        return 1


if __name__ == "__main__":
    sys.exit(main())