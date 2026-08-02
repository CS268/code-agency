from flask import Flask, jsonify, request, Response
import re
import time
import hashlib
import os
import smtplib
from email.mime.text import MIMEText
from langdetect import detect, DetectorFactory

# Ensure consistent language detection
DetectorFactory.seed = 0

app = Flask(__name__)

# Rate limit store
_rate_limit_store = {}

# CORS configuration
CORS_ALLOWED_ORIGIN = "https://cs268.github.io"

def _check_rate_limit(ip):
    """Check if the IP has exceeded the rate limit (10 requests per 60 seconds)."""
    current_time = time.time()
    if ip in _rate_limit_store:
        # Remove timestamps older than 60 seconds
        _rate_limit_store[ip] = [t for t in _rate_limit_store[ip] if current_time - t < 60]
        if len(_rate_limit_store[ip]) >= 10:
            return False
        _rate_limit_store[ip].append(current_time)
    else:
        _rate_limit_store[ip] = [current_time]
    return True

def _get_cors_headers():
    """Return CORS headers for the allowed origin."""
    return {
        "Access-Control-Allow-Origin": CORS_ALLOWED_ORIGIN,
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }

def _call_mistral_api(messages, max_tokens=512, temperature=0.7):
    """
    Call the Mistral API with the provided messages using the Mistral API key.
    Returns a dictionary with the parsed Mistral response.
    """
    import requests
    
    # Detect language from the last user message using langdetect
    last_user_message = ""
    for msg in reversed(messages):
        if msg.get('role') == 'user':
            last_user_message = msg.get('content', '')
            break
    
    # Language detection using langdetect with fallback
    detected_language = 'fr'  # default to French
    
    if last_user_message and len(last_user_message.strip()) > 20:  # Only detect if message is substantial
        try:
            detected_language = detect(last_user_message)
            # Normalize language codes
            if detected_language == 'en':
                detected_language = 'en'
            elif detected_language == 'nl':
                detected_language = 'nl'
            else:
                detected_language = 'fr'  # fallback to French for other languages
        except:
            detected_language = 'fr'  # fallback to French if detection fails
    
    # Get the appropriate system prompt for the detected language
    if detected_language == 'en':
        updated_system_prompt = SYSTEM_PROMPT_EN
    elif detected_language == 'nl':
        updated_system_prompt = SYSTEM_PROMPT_NL
    else:
        updated_system_prompt = SYSTEM_PROMPT_FR
    
    # Get Mistral API key from environment
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    if not mistral_api_key:
        raise ValueError("MISTRAL_API_KEY environment variable is not set")
    
    # Mistral API endpoint
    url = "https://api.mistral.ai/v1/chat/completions"
    
    # Prepare headers
    headers = {
        "Authorization": f"Bearer {mistral_api_key}",
        "Content-Type": "application/json"
    }
    
    # Prepare payload - use updated system prompt with detected language
    payload = {
        "model": "mistral-large-latest",
        "messages": [{"role": "system", "content": updated_system_prompt}] + messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    try:
        # Make the API call
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        
        # Extract the assistant's reply
        if "choices" in result and len(result["choices"]) > 0:
            assistant_reply = result["choices"][0]["message"]["content"]
            return {
                "reply": assistant_reply,
                "lead_name": None,
                "lead_email": None,
                "lead_phone": None,
                "lead_sector": None,
                "propose_meeting": False,
                "conversation_status": "general"
            }
        else:
            raise ValueError("No choices in Mistral response")
            
    except Exception as e:
        print(f"⚠️ Error calling Mistral API: {e}")
        # Return a fallback response
        return {
            "reply": "Désolé, je n'ai pas pu contacter le service d'intelligence artificielle. Veuillez réessayer plus tard.",
            "lead_name": None,
            "lead_email": None,
            "lead_phone": None,
            "lead_sector": None,
            "propose_meeting": False,
            "conversation_status": "general"
        }

SYSTEM_PROMPT = """
Tu es JCODE Assistant, commercial intelligent de JCODE Agency à Mons, Belgique. 
Réponds UNIQUEMENT en JSON valide sans texte avant ou après, avec cette structure exacte:
{
  "reply": "texte de ta réponse en français (ou néerlandais/anglais si demandé)",
  "lead_name": "nom du client si mentionné, sinon null",
  "lead_email": "email si mentionné, sinon null",
  "lead_phone": "téléphone si mentionné, sinon null",
  "lead_sector": "secteur d'activité si mentionné, sinon null",
  "propose_meeting": true/false,
  "conversation_status": "collecting_info" | "presenting_offer" | "closing" | "general"
}

RÈGLES:
- Saluer avec enthousiasme si première interaction
- Poser questions qualifiantes: secteur, budget, délais, site existant
- Ne JAMAIS donner de prix personnalisé hors forfaits officiels
- Si intéressé, proposer visioconférence gratuite 15 min
- Si demande de générer un site maintenant, rediriger vers paiement Stripe sur la page forfaits
- Hors sujet → rediriger poliment
- Contacts: matovuruky@gmail.com, 0466/06.22.73
"""

# Language-specific system prompts
SYSTEM_PROMPT_FR = """
Tu es JCODE Assistant, commercial intelligent de JCODE Agency à Mons, Belgique. 
Réponds UNIQUEMENT en JSON valide sans texte avant ou après, avec cette structure exacte:
{
  "reply": "texte de ta réponse en français",
  "lead_name": "nom du client si mentionné, sinon null",
  "lead_email": "email si mentionné, sinon null",
  "lead_phone": "téléphone si mentionné, sinon null",
  "lead_sector": "secteur d'activité si mentionné, sinon null",
  "propose_meeting": true/false,
  "conversation_status": "collecting_info" | "presenting_offer" | "closing" | "general"
}

RÈGLES:
- Saluer avec enthousiasme si première interaction
- Poser des questions qualifiantes: secteur d'activité, budget, délais, site existant
- Ne JAMAIS donner de prix personnalisé hors forfaits officiels
- Si le prospect est intéressé, proposer une visioconférence gratuite de 15 minutes
- Si demande de générer un site maintenant, rediriger vers le paiement Stripe sur la page des forfaits
- Pour les demandes hors sujet, rediriger poliment vers les services de JCODE
- Contacts: matovuruky@gmail.com, 0466/06.22.73
"""

SYSTEM_PROMPT_EN = """
You are JCODE Assistant, an intelligent salesperson for JCODE Agency in Mons, Belgium. 
Reply ONLY with valid JSON without any text before or after, using this exact structure:
{
  "reply": "your response text in English",
  "lead_name": "client name if mentioned, otherwise null",
  "lead_email": "email if mentioned, otherwise null",
  "lead_phone": "phone if mentioned, otherwise null",
  "lead_sector": "industry/sector if mentioned, otherwise null",
  "propose_meeting": true/false,
  "conversation_status": "collecting_info" | "presenting_offer" | "closing" | "general"
}

RULES:
- Greet enthusiastically if first interaction
- Ask qualifying questions: industry, budget, timeline, existing website
- NEVER provide custom pricing outside official packages
- If interested, propose a free 15-minute video conference
- If request to generate a site now, redirect to Stripe payment on the packages page
- For off-topic requests, politely redirect to JCODE's services
- Contacts: matovuruky@gmail.com, 0466/06.22.73
"""

SYSTEM_PROMPT_NL = """
Je bent JCODE Assistant, een intelligente verkoper voor JCODE Agency in Bergen, België. 
Reageer ALLEEN met geldige JSON zonder tekst ervoor of erna, met deze exacte structuur:
{
  "reply": "jouw antwoordtekst in het Nederlands",
  "lead_name": "klantnaam als genoemd, anders null",
  "lead_email": "email als genoemd, anders null",
  "lead_phone": "telefoon als genoemd, anders null",
  "lead_sector": "sector/activiteit als genoemd, anders null",
  "propose_meeting": true/false,
  "conversation_status": "collecting_info" | "presenting_offer" | "closing" | "general"
}

REGELS:
- Begroet enthousiast als het de eerste interactie is
- Stel kwalificerende vragen: sector, budget, termijn, bestaande website
- Geef NOOIT aangepaste prijzen buiten de officiële pakketten
- Als geïnteresseerd, stel een gratis 15-minuten videogesprek voor
- Als gevraagd wordt om nu een site te genereren, verwijs naar de Stripe-betalingspagina
- Voor vragen buiten het bestek, verwijs beleefd naar de diensten van JCODE
- Contacten: matovuruky@gmail.com, 0466/06.22.73
"""

@app.route('/chatbot', methods=['POST'])
def chatbot():
    """Endpoint POST /chatbot for handling chatbot requests."""
    try:
        # Check rate limit
        client_ip = request.remote_addr
        if not _check_rate_limit(client_ip):
            return jsonify({"error": "Too many requests. Please try again later."}), 429

        # Get JSON data
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"reply": "Message manquant. Veuillez envoyer un message valide.", "lead_captured": False, "lead_complete": False, "conversation_id": "error"}), 400

        message = data.get('message')
        history = data.get('history', [])

        # Check message length
        if len(message) > 2000:
            return jsonify({"reply": "Message trop long. Limite: 2000 caractères.", "lead_captured": False, "lead_complete": False, "conversation_id": "error"}), 400

        # Build Mistral messages
        mistral_messages = []
        for msg in history:
            mistral_messages.append({"role": msg.get('role', 'user'), "content": msg.get('content', '')})
        mistral_messages.append({"role": "user", "content": message})

        # Call Mistral API
        mistral_response = _call_mistral_api(mistral_messages)

        # Parse Mistral response defensively
        reply_text = mistral_response.get('reply', "Désolé, je n'ai pas pu traiter votre demande.")
        lead_name = mistral_response.get('lead_name')
        lead_email = mistral_response.get('lead_email')
        lead_phone = mistral_response.get('lead_phone')
        lead_sector = mistral_response.get('lead_sector')
        propose_meeting = mistral_response.get('propose_meeting', False)
        conversation_status = mistral_response.get('conversation_status', 'general')

        # Normalize response
        response_data = {
            "reply": reply_text,
            "lead_captured": any([lead_name, lead_email, lead_phone, lead_sector]),
            "lead_complete": bool(lead_name and lead_email),
            "conversation_id": hashlib.md5((client_ip + str(time.time())).encode()).hexdigest()
        }

        # Send email if lead is complete
        if response_data["lead_complete"]:
            try:
                sender_email = os.getenv("SMTP_USER", "matovuruky@gmail.com")
                smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
                smtp_port = int(os.getenv("SMTP_PORT", 587))
                smtp_password = os.getenv("SMTP_PASSWORD", "")

                msg = MIMEText(f"""Nouveau lead capturé par le chatbot:
Nom: {lead_name}
Email: {lead_email}
Téléphone: {lead_phone}
Secteur: {lead_sector}
Message: {message}""")
                msg['Subject'] = f"[JCODE LEAD] Nouveau prospect complet"
                msg['From'] = sender_email
                msg['To'] = "matovuruky@gmail.com"

                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(sender_email, smtp_password)
                    server.send_message(msg)
                print(f"✅ Email sent for lead: {lead_name} ({lead_email})")
            except Exception as e:
                print(f"⚠️ Failed to send email: {e}")

        # Return response with CORS headers
        response = jsonify(response_data)
        response.headers.update(_get_cors_headers())
        return response

    except Exception as e:
        print(f"⚠️ Error in /chatbot: {e}")
        response_data = {
            "reply": "Je rencontre un problème technique. Contactez-moi directement au 0466/06.22.73 ou matovuruky@gmail.com",
            "lead_captured": False,
            "lead_complete": False,
            "conversation_id": "error"
        }
        response = jsonify(response_data)
        response.headers.update(_get_cors_headers())
        return response, 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200

@app.route('/generate-site', methods=['POST'])
def generate_site():
    """Existing endpoint for generating sites."""
    return jsonify({"message": "Endpoint exists but not implemented here."}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)