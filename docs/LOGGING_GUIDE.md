# 📝 Guide de Logging pour l'Équipe

## Pour qui est ce guide?

- **Orchestrateur**: Intégrer les appels de logging dans `main.py`
- **Toolsmith**: Logger les résultats des outils (pylint, pytest)
- **Prompt Engineer**: S'assurer que les prompts sont loggés correctement

---

## 🚀 Démarrage Rapide

### Option 1: Utiliser les Helpers (Recommandé)

```python
from src.utils.log_helpers import log_audit, log_fix, log_test_execution

# Pour l'Auditor
log_audit(
    model="gemini-2.5-flash",
    input_prompt="Analyse ce code...",
    output_response="J'ai trouvé 3 problèmes...",
    file_analyzed="sandbox/code.py",
    issues_found=3
)

# Pour le Fixer
log_fix(
    model="gemini-2.5-flash",
    input_prompt="Corrige ce code...",
    output_response="```python\n...\n```",
    file_fixed="sandbox/code.py",
    issues_fixed=["docstring", "pep8"]
)

# Pour le Judge
log_test_execution(
    model="gemini-2.5-flash",
    input_prompt="Analyse ces résultats...",
    output_response="Les tests passent",
    tests_passed=5,
    tests_failed=0
)
```

### Option 2: Utiliser `log_experiment()` Directement

```python
from src.utils.logger import log_experiment, ActionType

log_experiment(
    agent_name="Auditor",
    model_used="gemini-2.5-flash",
    action=ActionType.ANALYSIS,
    details={
        "input_prompt": "Le prompt envoyé au LLM",      # ⚠️ OBLIGATOIRE
        "output_response": "La réponse du LLM",         # ⚠️ OBLIGATOIRE
        "file_analyzed": "sandbox/code.py"              # Optionnel
    },
    status="SUCCESS"
)
```

---

## 🎭 Quel Helper pour Quel Agent?

| Agent | Fonction Helper | ActionType |
|-------|-----------------|------------|
| **Auditor** | `log_audit()` | `CODE_ANALYSIS` |
| **Fixer** (correction) | `log_fix()` | `FIX` |
| **Fixer** (génération) | `log_generation()` | `CODE_GEN` |
| **Judge** (tests) | `log_test_execution()` | `CODE_ANALYSIS` |
| **Judge** (debug) | `log_debug()` | `DEBUG` |
| **Générique** | `log_action()` | Tout type |

---

## 📋 Checklist par Rôle

### Pour l'Orchestrateur 🧠

```python
# Dans main.py - À chaque appel d'agent:

# 1. AVANT l'appel LLM
prompt = build_prompt(code, context)

# 2. APPEL LLM
response = call_llm(prompt)

# 3. APRÈS l'appel - TOUJOURS LOGGER
log_audit(
    model=MODEL_NAME,
    input_prompt=prompt,          # ← Le prompt complet
    output_response=response,     # ← La réponse complète
    file_analyzed=current_file,
    issues_found=count_issues(response)
)
```

### Pour le Toolsmith 🛠️

```python
# Après exécution de pylint/pytest:

from src.utils.log_helpers import log_action, ActionType

# Logger les résultats d'analyse
log_action(
    agent_name="System",
    model="pylint",  # ou "pytest"
    action=ActionType.ANALYSIS,
    input_prompt=f"pylint {file_path}",
    output_response=pylint_output,
    tool="pylint",
    score=score
)
```

### Pour le Prompt Engineer 📝

```python
# S'assurer que les prompts sont versionnés dans les logs:

log_audit(
    model="gemini-2.5-flash",
    input_prompt=prompt,
    output_response=response,
    file_analyzed=file,
    issues_found=n,
    prompt_version="v1.2",        # ← Ajouter la version du prompt
    prompt_file="auditor_prompt.txt"
)
```

---

## ⚠️ Règles Critiques

### ✅ À FAIRE

1. **Toujours inclure `input_prompt`**
   ```python
   details={"input_prompt": full_prompt, ...}
   ```

2. **Toujours inclure `output_response`**
   ```python
   details={"output_response": llm_response, ...}
   ```

3. **Logger CHAQUE interaction avec le LLM**
   - Même si la réponse est vide
   - Même si le parsing échoue

4. **Utiliser `FAILURE` pour les erreurs**
   ```python
   except Exception as e:
       log_audit(..., success=False)
   ```

### ❌ À NE PAS FAIRE

1. **Ne pas tronquer les prompts/réponses**
   ```python
   # ❌ MAL
   details={"input_prompt": prompt[:100]}
   
   # ✅ BIEN
   details={"input_prompt": prompt}
   ```

2. **Ne pas oublier de logger les échecs**
   ```python
   # ❌ MAL - Pas de log si erreur
   try:
       response = call_llm(prompt)
       log_audit(...)
   except:
       pass
   
   # ✅ BIEN - Logger aussi les échecs
   try:
       response = call_llm(prompt)
       log_audit(..., success=True)
   except Exception as e:
       log_audit(..., output_response=str(e), success=False)
   ```

3. **Ne pas utiliser des ActionTypes inventés**
   ```python
   # ❌ MAL
   action="REFACTOR"
   
   # ✅ BIEN
   action=ActionType.FIX
   ```

---

## 🔧 Fonctions Helper Disponibles

### `log_audit()` - Pour l'Auditor

```python
log_audit(
    model: str,              # "gemini-2.5-flash"
    input_prompt: str,       # Le prompt complet
    output_response: str,    # La réponse du LLM
    file_analyzed: str,      # "sandbox/code.py"
    issues_found: int = 0,   # Nombre de problèmes
    success: bool = True,    # Réussite ou échec
    **extra_details          # Champs supplémentaires
)
```

### `log_fix()` - Pour le Fixer (corrections)

```python
log_fix(
    model: str,
    input_prompt: str,
    output_response: str,
    file_fixed: str,
    issues_fixed: list = None,  # ["docstring", "pep8"]
    success: bool = True,
    **extra_details
)
```

### `log_generation()` - Pour le Fixer (génération)

```python
log_generation(
    model: str,
    input_prompt: str,
    output_response: str,
    generated_type: str,    # "tests", "docstring", "documentation"
    target_file: str,
    success: bool = True,
    **extra_details
)
```

### `log_test_execution()` - Pour le Judge (tests)

```python
log_test_execution(
    model: str,
    input_prompt: str,
    output_response: str,
    tests_passed: int = 0,
    tests_failed: int = 0,
    test_output: str = "",  # Sortie brute pytest
    success: bool = True,
    **extra_details
)
```

### `log_debug()` - Pour le Judge (debug)

```python
log_debug(
    model: str,
    input_prompt: str,
    output_response: str,
    error_message: str,
    error_file: str = "",
    error_line: int = 0,
    success: bool = True,
    **extra_details
)
```

### `log_action()` - Générique

```python
log_action(
    agent_name: str,
    model: str,
    action: ActionType,
    input_prompt: str,
    output_response: str,
    success: bool = True,
    **extra_details
)
```

---

## 🧪 Tester Votre Logging

```python
# test_logging.py
from src.utils.log_helpers import log_audit
from src.utils.data_validator import print_validation_report

# 1. Créer une entrée de test
log_audit(
    model="test-model",
    input_prompt="Test prompt",
    output_response="Test response",
    file_analyzed="test.py",
    issues_found=0
)

# 2. Valider
print_validation_report()
```

---

## 📞 Contact Data Manager

Si vous avez des questions sur le logging:
- Consultez `docs/LOG_SCHEMA.md` pour le schéma complet
- Utilisez `python -m src.utils.data_validator` pour valider
- Alertez le Data Manager si `input_prompt` ou `output_response` pose problème
