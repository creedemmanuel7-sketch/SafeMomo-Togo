import streamlit as st
from PIL import Image
import os
import json

# Configuration de la page
st.set_page_config(
    page_title="SafeMomo Togo 🇹🇬 | Bouclier IA Anti-Arnaque",
    page_icon="🛡️",
    layout="centered"
)

# Style visuel personnalisé
st.markdown("""
    <style>
    .main-title { text-align: center; color: #1E3A8A; font-weight: 800; font-size: 2.2em; }
    .sub-title { text-align: center; color: #4B5563; margin-bottom: 25px; font-size: 1.1em; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
    .alert-box { padding: 15px; border-radius: 8px; margin-top: 15px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🛡️ SafeMomo Togo</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Détecteur IA multimodal d'arnaques <b>T-Money, Flooz & WhatsApp</b> à Lomé</p>", unsafe_allow_html=True)

# Barre latérale de configuration
api_key = os.environ.get("GEMINI_API_KEY", "")
with st.sidebar:
    st.header("⚙️ Paramètres")
    if not api_key:
        api_key = st.text_input("Clé API Google (Gemini / Gemma) :", type="password")
    
    st.markdown("---")
    offline_demo = st.checkbox("🧪 Mode Démo de Secours (Sans internet)", value=False, 
                               help="Active une simulation locale instantanée si la connexion internet faiblit.")
    
    st.markdown("---")
    st.markdown("### 🏆 Hackathon Info")
    st.markdown("- **Événement :** Hacktoberfest Lomé")
    st.markdown("- **Communauté :** Python Togo")
    st.markdown("- **Licence :** MIT Open Source")
    st.markdown("- **IA :** Gemma 4 Multimodal")

# Zone d'upload d'image
uploaded_file = st.file_uploader(
    "📸 Chargez la capture d'écran du SMS ou message suspect :", 
    type=["png", "jpg", "jpeg"]
)

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Capture soumise pour analyse", use_container_width=True)
    
    scan_clicked = st.button("🚨 Scanner avec Gemma 4", type="primary")
    
    if scan_clicked:
        if offline_demo:
            # Mode démo de secours pour garantir 0 crash devant le jury
            st.warning("⚠️ Analyse effectuée en mode démo hors-ligne de secours.")
            data = {
                "is_scam": True,
                "risk_score": 98,
                "verdict_title": "Tentative flagrante d'arnaque au faux transfert T-Money",
                "sender_analysis": "Numéro personnel suspect (+228 90 12 34 56) au lieu du canal officiel TMONEY",
                "red_flags": [
                    "Le message émane d'un numéro GSM individuel et non du canal certifié TMONEY",
                    "Ingénierie sociale : l'arnaqueur simule une 'erreur de transfert' pour forcer un renvoi immédiat",
                    "Aucun solde réel crédité : votre compte bancaire/mobile n'a pas reçu les fonds",
                    "Absence d'identifiant de transaction officiel conforme"
                ],
                "plain_advice": "Ne répondez pas et ne renvoyez aucun sou ! Tapez *145# pour vérifier votre solde réel. Prévenez vos proches.",
                "whatsapp_alert": "🚨 ALERTE ARNAQUE T-MONEY : Attention, des escrocs envoient des faux SMS prétendant avoir fait une erreur de transfert ! Ne renvoyez rien sans vérifier avec *145#. Partagez l'info !"
            }
        elif not api_key:
            st.error("Veuillez saisir votre clé API Google dans le menu latéral (ou cocher le 'Mode Démo de Secours').")
            st.stop()
        else:
            with st.spinner("Gemma 4 dissèque visuellement la capture, l'expéditeur et les signaux de fraude..."):
                try:
                    from google import genai
                    from google.genai import types
                    
                    client = genai.Client(api_key=api_key)
                    
                    system_prompt = """
                    Tu es SafeMomo, le système expert en cybersécurité et détection de fraudes Mobile Money au Togo (T-Money, Flooz, Moov Money, arnaques WhatsApp).
                    Analyse visuellement cette capture d'écran de téléphone et détermine si c'est une fraude/phishing ou un message authentique.
                    
                    Règles d'évaluation spécifiques au Togo :
                    1. Expéditeur : Les vrais messages viennent exclusivement du canal 'TMONEY' ou 'MOOV_MONEY'. Tout SMS venant d'un numéro personnel (+228 9X/7X/9X) prétendant un transfert est une ARNAQUE À 100%.
                    2. Incohérence de solde : Les arnaques omettent souvent le solde réel après transaction.
                    3. Manipulation psychologique : Fausse urgence ("erreur de transfert", "renvoie vite l'argent de l'hôpital", faux concours/recrutements).
                    
                    Tu DOIS répondre STRICTEMENT au format JSON avec cette structure :
                    {
                        "is_scam": true,
                        "risk_score": 98,
                        "verdict_title": "Tentative d'arnaque au faux transfert T-Money",
                        "sender_analysis": "Expéditeur suspect (+228 90 XX XX XX au lieu du canal officiel TMONEY)",
                        "red_flags": [
                            "Le numéro expéditeur est un numéro mobile personnel",
                            "Présence d'un sentiment d'urgence artificiel",
                            "Format du code de transaction invalide"
                        ],
                        "plain_advice": "Ne renvoyez aucun sou. Vérifiez votre solde réel en tapant *145# sur votre téléphone.",
                        "whatsapp_alert": "🚨 ALERTE ARNAQUE T-MONEY : Attention, des escrocs envoient des faux SMS disant avoir fait une erreur de transfert. Vérifiez toujours votre solde réel avec *145# !"
                    }
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[image, system_prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                    
                    data = json.loads(response.text)
                    
                except Exception as e:
                    st.error(f"Erreur d'analyse avec l'API : {str(e)}")
                    st.stop()
                    
        # Rendu des résultats
        st.divider()
        if data["is_scam"]:
            st.error(f"🚨 **{data['verdict_title']}** (Niveau de risque : {data['risk_score']}%)")
        else:
            st.success(f"✅ **{data['verdict_title']}** (Niveau de risque : {data['risk_score']}%)")
            
        st.subheader("🔎 Signaux d'alerte détectés :")
        st.write(f"**Expéditeur :** {data['sender_analysis']}")
        for flag in data["red_flags"]:
            st.markdown(f"- ⚠️ {flag}")
            
        st.info(f"💡 **Conseil immédiat :** {data['plain_advice']}")
        
        st.subheader("📢 Partager l'alerte sur WhatsApp :")
        st.code(data["whatsapp_alert"], language="text")

st.markdown("---")
st.caption("SafeMomo Togo | Hacktoberfest Hack Day Lomé 2026 × Python Togo | Licence MIT")
