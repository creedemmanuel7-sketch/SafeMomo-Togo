from PIL import Image, ImageDraw, ImageFont
import os

os.makedirs("samples", exist_ok=True)

# Création d'une image simulant un faux SMS T-Money togolais
img = Image.new("RGB", (600, 400), color="#1E293B")
draw = ImageDraw.Draw(img)

# En-tête de message
draw.rectangle([(20, 20), (580, 80)], fill="#334155")
draw.text((40, 35), "De : +228 90 45 67 89  (SMS reçu)", fill="#F8FAFC")

# Bulle de SMS suspect
draw.rectangle([(40, 100), (560, 260)], fill="#0F172A", outline="#EF4444", width=2)
sms_text = (
    "TMONEY INFO: Vous avez recu 35.000 FCFA de KOFFI A.\n"
    "Nouveau solde: 35.250 FCFA. Ref: TX998234.\n\n"
    "Pardonnez-moi maman j'ai fait une erreur de numero !\n"
    "C'est pour les frais d'hopital, renvoyez-moi ca vite !"
)
draw.text((60, 120), sms_text, fill="#F1F5F9")

# Note en bas
draw.text((40, 320), "Capture de test pour SafeMomo Togo 🇹🇬", fill="#94A3B8")

output_path = os.path.join("samples", "fake_tmoney_sample.png")
img.save(output_path)
print(f"Sample créé avec succès : {output_path}")
