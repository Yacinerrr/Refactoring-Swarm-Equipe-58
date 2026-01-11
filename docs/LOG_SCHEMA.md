# 📊 Schéma des Logs d'Expérimentation

## Vue d'ensemble

Tous les logs sont enregistrés dans `logs/experiment_data.json`. Ce fichier est **OBLIGATOIRE** pour la soumission du projet.

---

## 📋 Structure d'une Entrée de Log

```json
{
  "id": "uuid-unique-identifier",
  "timestamp": "2025-12-26T01:26:41.177789",
  "agent": "Auditor",
  "model": "gemini-2.5-flash",
  "action": "CODE_ANALYSIS",
  "details": {
    "input_prompt": "Le prompt envoyé au LLM",
    "output_response": "La réponse du LLM"
  },
  "status": "SUCCESS"
}
```

---

## 🔴 Champs Obligatoires (7 champs)

| Champ | Type | Description | Exemple |
|-------|------|-------------|---------|
| `id` | string (UUID) | Identifiant unique généré automatiquement | `"9e82e9b0-9b43-4a78-af43-d5d5ef848a2f"` |
| `timestamp` | string (ISO 8601) | Date/heure de l'action | `"2025-12-26T01:26:41.177789"` |
| `agent` | string | Nom de l'agent qui effectue l'action | `"Auditor"`, `"Fixer"`, `"Judge"` |
| `model` | string | Modèle LLM utilisé | `"gemini-2.5-flash"`, `"gpt-4"` |
| `action` | string (ActionType) | Type d'action effectuée | `"CODE_ANALYSIS"`, `"FIX"` |
| `details` | object | Dictionnaire avec les détails | Voir section suivante |
| `status` | string | Résultat de l'action | `"SUCCESS"`, `"FAILURE"` |

---

## 📦 Champs Obligatoires dans `details`

> ⚠️ **CRITIQUE**: Ces champs sont **OBLIGATOIRES** pour toutes les actions sauf `STARTUP`

| Champ | Type | Description | Obligatoire |
|-------|------|-------------|-------------|
| `input_prompt` | string | Le prompt complet envoyé au LLM | ✅ OUI |
| `output_response` | string | La réponse complète du LLM | ✅ OUI |

### Champs Optionnels Recommandés

| Champ | Type | Description | Agent concerné |
|-------|------|-------------|----------------|
| `file_analyzed` | string | Fichier analysé | Auditor |
| `issues_found` | int | Nombre de problèmes détectés | Auditor |
| `file_fixed` | string | Fichier corrigé | Fixer |
| `issues_fixed` | list | Liste des corrections | Fixer |
| `tests_passed` | int | Tests réussis | Judge |
| `tests_failed` | int | Tests échoués | Judge |
| `error_message` | string | Message d'erreur | Tous |

---

## 🎭 Types d'Actions (ActionType)

| ActionType | Valeur | Description | Utilisé par |
|------------|--------|-------------|-------------|
| `ANALYSIS` | `"CODE_ANALYSIS"` | Audit, lecture, recherche de bugs | Auditor |
| `GENERATION` | `"CODE_GEN"` | Création de nouveau code/tests/docs | Fixer |
| `DEBUG` | `"DEBUG"` | Analyse d'erreurs d'exécution | Judge |
| `FIX` | `"FIX"` | Application de correctifs | Fixer |

### Utilisation en Python

```python
from src.utils.logger import ActionType

# Méthode 1: Utiliser l'Enum
action=ActionType.ANALYSIS

# Méthode 2: Utiliser la string directement
action="CODE_ANALYSIS"
```

---

## 🤖 Agents Valides

| Agent | Rôle | Actions Typiques |
|-------|------|------------------|
| `Auditor` | Analyse le code, détecte les problèmes | `CODE_ANALYSIS` |
| `Fixer` | Corrige le code, génère des tests | `FIX`, `CODE_GEN` |
| `Judge` | Exécute les tests, valide les corrections | `DEBUG`, `CODE_ANALYSIS` |
| `System` | Actions système (démarrage, etc.) | `STARTUP` (exempt de validation) |

---

## ✅ Statuts Valides

| Status | Signification | Quand l'utiliser |
|--------|---------------|------------------|
| `SUCCESS` | Action réussie | Le LLM a répondu correctement, l'action s'est bien passée |
| `FAILURE` | Action échouée | Erreur LLM, parsing échoué, exception |
| `INFO` | Information système | Logs de démarrage, événements non-critiques |

### Critères de Décision

```
SUCCESS si:
├── Le LLM a répondu sans erreur
├── La réponse est parseable (si JSON attendu)
├── L'action demandée a été accomplie
└── Pas d'exception Python

FAILURE si:
├── Timeout du LLM
├── Réponse non parseable
├── Exception Python levée
├── Action impossible à accomplir
└── Erreur de syntaxe dans le code généré
```

---

## 📝 Exemples Complets

### Exemple 1: Audit de Code (Auditor)

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2025-12-26T10:30:00.000000",
  "agent": "Auditor",
  "model": "gemini-2.5-flash",
  "action": "CODE_ANALYSIS",
  "details": {
    "input_prompt": "Analyse ce code Python et identifie les problèmes:\n\ndef foo():\nreturn 42",
    "output_response": "J'ai identifié 2 problèmes:\n1. Indentation incorrecte\n2. Pas de docstring",
    "file_analyzed": "sandbox/buggy.py",
    "issues_found": 2
  },
  "status": "SUCCESS"
}
```

### Exemple 2: Correction de Code (Fixer)

```json
{
  "id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
  "timestamp": "2025-12-26T10:31:00.000000",
  "agent": "Fixer",
  "model": "gemini-2.5-flash",
  "action": "FIX",
  "details": {
    "input_prompt": "Corrige ce code selon le plan d'audit...",
    "output_response": "```python\ndef foo():\n    \"\"\"Returns 42.\"\"\"\n    return 42\n```",
    "file_fixed": "sandbox/buggy.py",
    "issues_fixed": ["indentation", "docstring"]
  },
  "status": "SUCCESS"
}
```

### Exemple 3: Exécution de Tests (Judge)

```json
{
  "id": "c3d4e5f6-a7b8-9012-cdef-345678901234",
  "timestamp": "2025-12-26T10:32:00.000000",
  "agent": "Judge",
  "model": "gemini-2.5-flash",
  "action": "DEBUG",
  "details": {
    "input_prompt": "Analyse ces résultats de tests pytest...",
    "output_response": "Les tests passent maintenant. Action: validate",
    "tests_passed": 5,
    "tests_failed": 0,
    "test_output": "===== 5 passed in 0.02s ====="
  },
  "status": "SUCCESS"
}
```

### Exemple 4: Échec (FAILURE)

```json
{
  "id": "d4e5f6a7-b8c9-0123-defa-456789012345",
  "timestamp": "2025-12-26T10:33:00.000000",
  "agent": "Fixer",
  "model": "gemini-2.5-flash",
  "action": "FIX",
  "details": {
    "input_prompt": "Corrige ce code...",
    "output_response": "Invalid JSON response from model",
    "file_fixed": "sandbox/buggy.py",
    "error": "JSONDecodeError: Expecting value at line 1"
  },
  "status": "FAILURE"
}
```

---

## ⚠️ Erreurs Courantes à Éviter

| ❌ Ne pas faire | ✅ Faire |
|-----------------|----------|
| Oublier `input_prompt` | Toujours inclure le prompt complet |
| Oublier `output_response` | Toujours inclure la réponse du LLM |
| Utiliser un `action` invalide | Utiliser `ActionType` enum |
| Statut `SUCCESS` sur une erreur | Utiliser `FAILURE` si exception |
| Écraser le fichier de logs | Append seulement (géré par logger) |

---

## 🔍 Validation

Exécutez le validateur pour vérifier vos logs:

```bash
python -m src.utils.data_validator
```

Résultat attendu:
```
🎉 VERDICT: LOGS VALIDES ET COMPLETS
```

---

## 📁 Fichier de Sortie

**Chemin**: `logs/experiment_data.json`

> ⚠️ Ce fichier est dans `.gitignore`. Pour la soumission, exécutez:
> ```bash
> git add -f logs/experiment_data.json
> ```
