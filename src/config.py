"""
Configuration centrale pour le système Refactoring Swarm
=========================================================
IMPORTANT: Modifiez UNIQUEMENT ce fichier pour changer le modèle LLM.
"""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# ============================================================
# CONFIGURATION DU MODÈLE LLM
# ============================================================

# 🔧 CHANGEZ UNIQUEMENT CETTE LIGNE pour changer le modèle partout
DEFAULT_MODEL = "gemini-1.5-flash"

# Modèles disponibles (commentaires pour référence):
# - "gemini-1.5-flash"      : Rapide, gratuit, recommandé
# - "gemini-1.5-pro"        : Plus intelligent, plus lent
# - "gemini-2.5-flash"      : Nouvelle version (si disponible)
# - "gemini-pro"            : Version stable

# ============================================================
# CONFIGURATION DE L'API
# ============================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(
        "❌ GOOGLE_API_KEY non trouvée dans .env\n"
        "   Créez un fichier .env avec:\n"
        "   GOOGLE_API_KEY=votre_clé_ici"
    )

# ============================================================
# CONFIGURATION DES RETRIES ET RATE LIMITING
# ============================================================

MAX_RETRIES = 3  # Nombre de tentatives en cas de rate limit
RETRY_DELAY = 5  # Délai de base entre les tentatives (secondes)

# NOUVELLE CONFIGURATION: Pause entre agents
INTER_AGENT_DELAY = 2  # Secondes d'attente entre chaque agent (évite rate limits)
ENABLE_RATE_LIMIT_PROTECTION = True  # Active la pause automatique

# ============================================================
# CONFIGURATION DE LA GÉNÉRATION
# ============================================================

GENERATION_CONFIG = {
    "temperature": 0.1,      # Créativité (0.0 = déterministe, 1.0 = créatif)
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

# ============================================================
# CONFIGURATION DU SYSTÈME
# ============================================================

MAX_ITERATIONS = 10  # Nombre maximum d'itérations pour la boucle de correction

# ============================================================
# CHEMINS DES FICHIERS
# ============================================================

LOG_FILE = "logs/experiment_data.json"
PROMPTS_DIR = "src/prompts"
SANDBOX_DIR = "sandbox"

# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def get_model_name() -> str:
    """Retourne le nom du modèle configuré."""
    return DEFAULT_MODEL


def get_api_key() -> str:
    """Retourne la clé API."""
    return GOOGLE_API_KEY


def get_generation_config() -> dict:
    """Retourne la configuration de génération."""
    return GENERATION_CONFIG.copy()


def get_inter_agent_delay() -> int:
    """Retourne le délai à attendre entre agents."""
    return INTER_AGENT_DELAY if ENABLE_RATE_LIMIT_PROTECTION else 0


# ============================================================
# AFFICHAGE DE LA CONFIGURATION (pour debug)
# ============================================================

if __name__ == "__main__":
    print("="*60)
    print("🔧 CONFIGURATION DU SYSTÈME")
    print("="*60)
    print(f"Modèle LLM         : {DEFAULT_MODEL}")
    print(f"API Key configurée : {'✅ Oui' if GOOGLE_API_KEY else '❌ Non'}")
    print(f"Max retries        : {MAX_RETRIES}")
    print(f"Max iterations     : {MAX_ITERATIONS}")
    print(f"Temperature        : {GENERATION_CONFIG['temperature']}")
    print(f"\n🚦 Protection Rate Limit:")
    print(f"   Activée         : {'✅ Oui' if ENABLE_RATE_LIMIT_PROTECTION else '❌ Non'}")
    print(f"   Délai inter-agent: {INTER_AGENT_DELAY}s")
    print("="*60)