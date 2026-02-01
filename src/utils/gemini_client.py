"""
Gemini API Client - Interface pour communiquer avec Google Gemini
==================================================================
Ce module fournit une fonction simple pour envoyer des prompts à Gemini
et recevoir des réponses structurées.

Compatible avec google-generativeai v0.3.2
Avec retry automatique pour les rate limits
"""

import json
import time
import google.generativeai as genai
from src.config import (
    get_model_name,
    get_api_key,
    get_generation_config,
    MAX_RETRIES
)

# Configuration de l'API Gemini
genai.configure(api_key=get_api_key())


def call_gemini(
    prompt: str,
    model_name: str = None,  # None = use config default
    temperature: float = None,  # None = use config default
    json_mode: bool = True,
    max_retries: int = None  # None = use config default
) -> str:
    """
    Envoie un prompt à Gemini et retourne la réponse.
    Avec retry automatique en cas de rate limit.
    
    Args:
        prompt: Le prompt à envoyer
        model_name: Le modèle Gemini à utiliser (None = utilise config.py)
        temperature: Créativité (None = utilise config.py)
        json_mode: Si True, demande une réponse JSON
        max_retries: Nombre de tentatives (None = utilise config.py)
    
    Returns:
        str: La réponse de Gemini
    
    Raises:
        Exception: Si l'appel API échoue après toutes les tentatives
    """
    # Utiliser les valeurs par défaut de config.py si non spécifiées
    if model_name is None:
        model_name = get_model_name()
    if max_retries is None:
        max_retries = MAX_RETRIES
    
    generation_config = get_generation_config()
    if temperature is not None:
        generation_config["temperature"] = temperature
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config
            )
            
            # Si on veut du JSON, l'ajouter au prompt
            if json_mode:
                prompt = f"{prompt}\n\nRéponds UNIQUEMENT avec du JSON valide, sans texte avant ou après."
            
            # Générer la réponse
            response = model.generate_content(prompt)
            
            # Extraire le texte
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'parts'):
                return ''.join(part.text for part in response.parts)
            else:
                raise Exception("Format de réponse Gemini inattendu")
                
        except Exception as e:
            error_str = str(e)
            
            # Vérifier si c'est une erreur de rate limit
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                # Extraire le temps d'attente si disponible
                wait_time = 60  # Par défaut 60 secondes
                
                if "retry in" in error_str.lower():
                    try:
                        # Essayer d'extraire le temps d'attente
                        import re
                        match = re.search(r'retry in (\d+\.?\d*)', error_str.lower())
                        if match:
                            wait_time = float(match.group(1))
                    except:
                        pass
                
                if attempt < max_retries - 1:
                    print(f"⚠️ Rate limit atteint. Attente de {wait_time:.0f} secondes...")
                    time.sleep(wait_time + 1)  # +1 seconde de marge
                    continue
                else:
                    error_msg = f"❌ Rate limit dépassé après {max_retries} tentatives"
                    print(error_msg)
                    raise Exception(error_msg)
            else:
                # Autre erreur, on ne réessaie pas
                error_msg = f"Erreur lors de l'appel à Gemini: {error_str}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
    
    raise Exception("Échec après toutes les tentatives")


def call_gemini_json(prompt: str, model_name: str = None, max_retries: int = None) -> dict:
    """
    Appelle Gemini et parse automatiquement la réponse JSON.
    Avec retry automatique en cas de rate limit.
    
    Args:
        prompt: Le prompt à envoyer
        model_name: Le modèle Gemini à utiliser (None = utilise config.py)
        max_retries: Nombre de tentatives (None = utilise config.py)
    
    Returns:
        dict: La réponse parsée en JSON
    
    Raises:
        json.JSONDecodeError: Si la réponse n'est pas du JSON valide
        Exception: Si l'appel API échoue
    """
    response_text = call_gemini(prompt, model_name=model_name, json_mode=True, max_retries=max_retries)
    
    try:
        # Nettoyer la réponse (enlever les balises markdown si présentes)
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"⚠️ Réponse Gemini n'est pas du JSON valide:")
        print(response_text[:500])
        raise e


# Test du module
if __name__ == "__main__":
    print("🧪 Test de connexion à Gemini...")
    
    test_prompt = """
    Réponds avec ce format JSON exact:
    {
        "status": "success",
        "message": "API Gemini fonctionne correctement"
    }
    """
    
    try:
        response = call_gemini_json(test_prompt)
        print("✅ Connexion réussie!")
        print(json.dumps(response, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Erreur: {e}")