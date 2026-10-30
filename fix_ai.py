import re
with open("ai-concierge.html", "r", encoding="utf-8") as f: content = f.read()
video = "<div style=\"margin: 2rem auto; border-radius: 16px; overflow: hidden; box-shadow: 0 15px 30px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); max-width: 800px;\"><iframe width=\"100%\" height=\"400\" src=\"https://www.youtube.com/embed/gIXu6K0IFNY\" title=\"Demo\" frameborder=\"0\" allowfullscreen></iframe></div>"
if "Ce que vous obtenez" in content:
    content = content.replace("Ce que vous obtenez", video + "
Ce que vous obtenez")
    with open("ai-concierge.html", "w", encoding="utf-8") as f: f.write(content)
    print("✅ Vidéo insérée avec succès dans ai-concierge.html")
else:
    print("⚠️ Texte non trouvé")
