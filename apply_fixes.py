#!/usr/bin/env python3
"""Applique les 4 fixes (CORS, multi-clients, parsing leads) au backend JCODE.
Chaque étape vérifie que le texte cible existe exactement avant de remplacer.
Refuse si le fichier a déjà été corrigé ou si une cible est introuvable.
À exécuter depuis ~/jcode-agency :
    python3 apply_fixes.py
"""
import io
import sys

PATH = "jcode-site-generator/jcode_site_generator.py"

CLIENT_PROMPTS = """ALLOWED_ORIGINS = ["https://cs268.github.io", "https://jcode.store", "https://www.jcode.store"]

# Contrat de sortie JSON exigé de Mistral (indispensable au parsing des leads)
JSON_OUTPUT_CONTRACT = \"\"\"Tu réponds UNIQUEMENT en JSON valide, sans texte avant ou après, avec cette structure exacte:
{
  "reply": "ta réponse, dans la langue du visiteur (français, néerlandais ou anglais)",
  "lead_name": "nom du client si mentionné, sinon null",
  "lead_email": "email si mentionné, sinon null",
  "lead_phone": "téléphone si mentionné, sinon null",
  "lead_sector": "secteur d'activité si mentionné, sinon null",
  "propose_meeting": true/false,
  "conversation_status": "collecting_info" | "presenting_offer" | "closing" | "general"
}\"\"\"

# Prompts système personnalisés par client (connaissances spécifiques)
CLIENT_PROMPTS = {
    "ali-baba-snack": \"\"\"Tu es l'assistant virtuel du Snack Ali Baba à Bruxelles. Tu connais :
- Horaires : ouvert tous les jours 11h-23h, fermé le mardi
- Menu : kebabs 8€, burgers 9€, frites 4€, boissons 2-3€
- Livraison : gratuite dès 20€, zones Schaerbeek et Evere
- Allergènes : halal, options végétariennes sur demande
- Téléphone : 02/XXX.XX.XX
Sois chaleureux, direct et utile.\"\"\",

    "coiffeur-marie": \"\"\"Tu es l'assistant virtuel du salon de coiffure de Marie. Tu connais :
- Horaires : mardi-samedi 9h-18h, fermé lundi et dimanche
- Prestations : coupe femme 35€, coupe homme 25€, coloration 60€, brushing 20€
- Réservation : par téléphone ou en ligne
- Adresse : [à compléter]
Sois chaleureuse et professionnelle.\"\"\",

    "demo-client": \"\"\"Tu es un assistant commercial pour une petite entreprise. Sois concis, utile et chaleureux.\"\"\"
}"""

CORS_HEADERS_NEW = '''def _get_cors_headers():
    """Return CORS headers if the request origin is allowed."""
    origin = request.headers.get('Origin')
    if origin in ALLOWED_ORIGINS:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    return {}

@app.after_request
def after_request(response):
    """Apply CORS headers to every response, including OPTIONS preflight."""
    response.headers.update(_get_cors_headers())
    return response'''

PARSE_JSON_HELPER = '''def _parse_mistral_json(response_text):
    """Extract the first JSON object from the Mistral reply, if present."""
    try:
        cleaned = re.sub(r'^```json\\s*|```|\\s*json\\s*', '', response_text).strip()
        match = re.search(r'\\{.*\\}', cleaned, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
    except Exception as e:
        print(f"Erreur parsing Mistral JSON: {e}")
    return None

SYSTEM_PROMPT = """'''

# (name, old, new, skip_if_contains)
STEPS = [
    ("1-import json",
     "import hashlib\nimport os",
     "import hashlib\nimport json\nimport os",
     "import json"),
    ("2-CORS + CLIENT_PROMPTS",
     'CORS_ALLOWED_ORIGIN = "https://cs268.github.io"',
     CLIENT_PROMPTS,
     "ALLOWED_ORIGINS = ["),
    ("3-cors_headers dynamique + after_request",
     '''def _get_cors_headers():
    """Return CORS headers for the allowed origin."""
    return {
        "Access-Control-Allow-Origin": CORS_ALLOWED_ORIGIN,
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }''',
     CORS_HEADERS_NEW,
     "@app.after_request"),
    ("4-signature _call_mistral_api",
     "def _call_mistral_api(messages, max_tokens=512, temperature=0.7):",
     'def _call_mistral_api(messages, client_id="jcode-default", max_tokens=512, temperature=0.7):',
     'client_id="jcode-default"'),
    ("5-prompt client vs langage",
     """    # Get the appropriate system prompt for the detected language
    if detected_language == 'en':
        updated_system_prompt = SYSTEM_PROMPT_EN
    elif detected_language == 'nl':
        updated_system_prompt = SYSTEM_PROMPT_NL
    else:
        updated_system_prompt = SYSTEM_PROMPT_FR""",
     """    # Get the appropriate system prompt for the detected language
    if client_id in CLIENT_PROMPTS:
        # Multi-client : connaissance spécifique + contrat JSON (langue du visiteur)
        updated_system_prompt = CLIENT_PROMPTS[client_id] + "\\n\\n" + JSON_OUTPUT_CONTRACT
    elif detected_language == 'en':
        updated_system_prompt = SYSTEM_PROMPT_EN
    elif detected_language == 'nl':
        updated_system_prompt = SYSTEM_PROMPT_NL
    else:
        updated_system_prompt = SYSTEM_PROMPT_FR""",
     "client_id in CLIENT_PROMPTS"),
    ("6-parsing de la réponse",
     '''        if "choices" in result and len(result["choices"]) > 0:
            assistant_reply = result["choices"][0]["message"]["content"]
            return {
                "reply": assistant_reply,''',
     '''        if "choices" in result and len(result["choices"]) > 0:
            assistant_reply = result["choices"][0]["message"]["content"]
            parsed = _parse_mistral_json(assistant_reply)
            if parsed:
                return parsed
            return {
                "reply": assistant_reply,''',
     "parsed = _parse_mistral_json(assistant_reply)"),
    ("7-helper _parse_mistral_json",
     'SYSTEM_PROMPT = """',
     PARSE_JSON_HELPER,
     "def _parse_mistral_json"),
    ("8-client_id dans chatbot()",
     """        message = data.get('message')
        history = data.get('history', [])

        # Check message length""",
     """        message = data.get('message')
        history = data.get('history', [])

        client_id = data.get('client', 'jcode-default')

        # Check message length""",
     "client_id = data.get('client'"),
    ("9-passer client_id à l'appel",
     "mistral_response = _call_mistral_api(mistral_messages)",
     "mistral_response = _call_mistral_api(mistral_messages, client_id=client_id)",
     "_call_mistral_api(mistral_messages, client_id=client_id)"),
]


def main():
    try:
        with io.open(PATH, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print("ERREUR: fichier introuvable. Lance depuis ~/jcode-agency")
        sys.exit(1)

    applied = 0
    for name, old, new, skip_if in STEPS:
        if skip_if and skip_if in content:
            print("SKIP (déjà en place):", name)
            continue
        count = content.count(old)
        if count == 0:
            print("ERREUR: cible introuvable, abandon:", name)
            sys.exit(2)
        if count > 1:
            print("ERREUR: cible non unique, abandon:", name)
            sys.exit(2)
        content = content.replace(old, new, 1)
        applied += 1
        print("OK:", name)

    if applied == 0:
        print("Rien à faire : les 9 modifs sont déjà en place.")
        return

    with io.open(PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"{applied}/9 modifs appliquées avec succès.")


if __name__ == "__main__":
    main()
