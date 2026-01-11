"""
Gemini API Client - Interface pour communiquer avec Google Gemini
==================================================================
Ce module fournit une fonction simple pour envoyer des prompts à Gemini
et recevoir des réponses structurées.

Compatible avec google-generativeai v0.3.2
"""

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration de l'API Gemini
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY non trouvée dans .env")

genai.configure(api_key=GEMINI_API_KEY)


def call_gemini(
    prompt: str,
    model_name: str = "gemini-1.5-flash",
    temperature: float = 0.1,
    json_mode: bool = True
) -> str:
    """
    Envoie un prompt à Gemini et retourne la réponse.
    
    Args:
        prompt: Le prompt à envoyer
        model_name: Le modèle Gemini à utiliser
        temperature: Créativité (0.0 = déterministe, 1.0 = créatif)
        json_mode: Si True, demande une réponse JSON
    
    Returns:
        str: La réponse de Gemini
    
    Raises:
        Exception: Si l'appel API échoue
    
    Example:
        response = call_gemini(
            "Analyse ce code Python...",
            model_name="gemini-1.5-flash"
        )
    """
    try:
        # Configuration du modèle pour la version 0.3.2
        generation_config = {
            "temperature": temperature,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
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
        error_msg = f"Erreur lors de l'appel à Gemini: {str(e)}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)


def call_gemini_json(prompt: str, model_name: str = "gemini-1.5-flash") -> dict:
    """
    Appelle Gemini et parse automatiquement la réponse JSON.
    
    Args:
        prompt: Le prompt à envoyer
        model_name: Le modèle Gemini à utiliser
    
    Returns:
        dict: La réponse parsée en JSON
    
    Raises:
        json.JSONDecodeError: Si la réponse n'est pas du JSON valide
        Exception: Si l'appel API échoue
    """
    response_text = call_gemini(prompt, model_name=model_name, json_mode=True)
    
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