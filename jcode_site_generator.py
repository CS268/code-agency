#!/usr/bin/env python3
"""
JCODE Site Generator - Backend Flask pour la génération de sites web.
Inclut un endpoint /chatbot pour le chatbot IA.
"""

from flask import Flask, jsonify, request, Response
import json
import re
import time
import smtplib
from email.mime.text import MIMEText
from functools import wraps
import hashlib
import os


app = Flask(__name__)

# Store pour le rate-limiting en mémoire
_rate_limit_store = {}

# Liste des origines autorisées pour CORS
ALLOWED_ORIGINS = ["https://cs268.github.io"]


def rate_limit(max_requests, window_seconds):
    """
    Décorateur pour limiter le nombre de requêtes par IP.
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip = request.remote_addr
            current_time = time.time()
            
            # Initialiser la liste des timestamps pour cette IP
            if ip not in _rate_limit_store:
                _rate_limit_store[ip] = []
            
            # Nettoyer les timestamps trop vieux
            _rate_limit_store[ip] = [t for t in _rate_limit_store[ip] if current_time - t < window_seconds]
            
            # Vérifier si la limite est dépassée
            if len(_rate_limit_store[ip]) >= max_requests:
                return jsonify({"error": "Too Many Requests"}), 429
            
            # Ajouter le timestamp de la requête actuelle
            _rate_limit_store[ip].append(current_time)
            
            return f(*args, **kwargs)
        return wrapped
    return decorator


def apply_cors(response):
    """
    Applique les en-têtes CORS pour autoriser uniquement les origines spécifiées.
    """
    origin = request.headers.get('Origin')
    if origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@app.after_request
def after_request(response):
    """
    Applique les en-têtes CORS à toutes les réponses.
    """
    return apply_cors(response)


# Endpoint de base
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})


# Endpoint pour le chatbot IA
@app.route('/chatbot', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60)
def chatbot():
    """
    Endpoint POST /chatbot : Gère les interactions avec le chatbot IA.
    """
    try:
        # Vérifier la longueur du message
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"reply": "Message vide ou format invalide.", "lead_captured": False, "lead_complete": False, "conversation_id": "error"}), 400

        message = data['message']
        if len(message) > 500:
            return jsonify({"reply": "Message trop long. Limite: 500 caractères.", "lead_captured": False, "lead_complete": False, "conversation_id": "error"}), 400

        history = data.get('history', [])

        # Construction du SYSTEM PROMPT pour Mistral
        system_prompt = """Tu es JCODE Assistant, commercial intelligent de JCODE Agency à Mons, Belgique. Réponds UNIQUEMENT en JSON valide sans texte avant ou après, avec cette structure exacte:
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
- Contacts: matovuruky@gmail.com, 0466/06.22.73"""

        # Préparation des messages pour l'API Mistral
        mistral_messages = [
            {"role": "system", "content": system_prompt},
        ]
        mistral_messages.extend(history)
        mistral_messages.append({"role": "user", "content": message})

        # Appel à l'API Mistral (à implémenter selon la clé API disponible)
        # Pour l'instant, on simule une réponse pour tester la logique
        mistral_response = call_mistral_api(mistral_messages)

        # Parsing défensif du JSON retourné par Mistral
        parsed_response = parse_mistral_response(mistral_response)

        # Normalisation de la réponse Flask
        response_data = {
            "reply": parsed_response.get("reply", "Désolé, je n'ai pas pu traiter votre demande."),
            "lead_captured": any([
                parsed_response.get("lead_name") is not None,
                parsed_response.get("lead_email") is not None,
                parsed_response.get("lead_phone") is not None,
                parsed_response.get("lead_sector") is not None,
            ]),
            "lead_complete": (
                parsed_response.get("lead_name") is not None and 
                parsed_response.get("lead_email") is not None
            ),
            "conversation_id": hashlib.md5((request.remote_addr + str(time.time())).encode()).hexdigest()
        }

        # Si lead complet, envoyer un email
        if response_data["lead_complete"]:
            send_lead_email(
                lead_name=parsed_response.get("lead_name"),
                lead_email=parsed_response.get("lead_email"),
                lead_phone=parsed_response.get("lead_phone"),
                lead_sector=parsed_response.get("lead_sector"),
                message=message
            )

        return jsonify(response_data)

    except Exception as e:
        # Gestion d'erreur globale
        print(f"Erreur dans /chatbot : {e}")
        return jsonify({
            "reply": "Je rencontre un problème technique. Contactez-moi directement au 0466/06.22.73 ou matovuruky@gmail.com",
            "lead_captured": False,
            "lead_complete": False,
            "conversation_id": "error"
        }), 500


def call_mistral_api(messages):
    """
    Appelle l'API Mistral avec les messages fournis.
    À implémenter selon la clé API disponible.
    """
    # TODO: Implémenter l'appel réel à l'API Mistral
    # Pour l'instant, on retourne une réponse simulée
    return json.dumps({
        "reply": "Bonjour ! Je suis JCODE Assistant. Pouvez-vous me dire dans quel secteur votre entreprise évolue ?",
        "lead_name": None,
        "lead_email": None,
        "lead_phone": None,
        "lead_sector": None,
        "propose_meeting": False,
        "conversation_status": "collecting_info"
    })


def parse_mistral_response(response_text):
    """
    Parse la réponse de Mistral de manière défensive.
    """
    try:
        # Nettoyer les backticks et le mot "json" au début
        cleaned = re.sub(r'^```json\s*|```|\s*json\s*', '', response_text).strip()
        
        # Extraire le premier bloc JSON
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            json_str = match.group(0)
            parsed = json.loads(json_str)
            return parsed
        else:
            # Si pas de JSON valide, retourner une réponse par défaut
            return {
                "reply": cleaned,
                "lead_name": None,
                "lead_email": None,
                "lead_phone": None,
                "lead_sector": None,
                "propose_meeting": False,
                "conversation_status": "general"
            }
    except Exception as e:
        print(f"Erreur de parsing : {e}")
        return {
            "reply": "Désolé, je n'ai pas pu traiter votre demande.",
            "lead_name": None,
            "lead_email": None,
            "lead_phone": None,
            "lead_sector": None,
            "propose_meeting": False,
            "conversation_status": "general"
        }


def send_lead_email(lead_name, lead_email, lead_phone, lead_sector, message):
    """
    Envoie un email SMTP avec les informations du lead.
    """
    try:
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        sender_email = os.getenv("SMTP_USER")
        recipient_email = "matovuruky@gmail.com"

        if not all([smtp_server, smtp_port, smtp_user, smtp_password, sender_email]):
            print("Variables SMTP manquantes. Email non envoyé.")
            return

        # Construction du corps de l'email
        body = f"""Nouveau lead capturé par le chatbot:
Nom: {lead_name}
Email: {lead_email}
Téléphone: {lead_phone}
Secteur: {lead_sector}
Message: {message}"""

        msg = MIMEText(body)
        msg['Subject'] = "[JCODE LEAD] Nouveau prospect complet"
        msg['From'] = sender_email
        msg['To'] = recipient_email

        # Envoi de l'email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        print(f"✅ Email envoyé pour le lead : {lead_name} ({lead_email})")

    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email : {e}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)