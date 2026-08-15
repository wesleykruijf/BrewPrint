import streamlit as st
import json
import os
from PIL import Image
from google import genai

# ==========================================
# 1. PAGINA CONFIGURATIE
# ==========================================
st.set_page_config(page_title="BrewPrint Pro", page_icon="☕", layout="centered")

# ==========================================
# 2. GEMINI API FUNCTIE
# ==========================================
def get_ai_advice(image):
    """Stuurt de foto naar Gemini voor analyse."""
    # We laden de API key vanuit de Streamlit secrets
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    prompt = (
        "Analyseer dit koffie-etiket. Bepaal de volgende parameters en geef STRIKT terug als JSON. "
        "Geen extra tekst, alleen de JSON: "
        "{'ratio': 16.5, 'bean_name': 'Naam', 'process': 'Washed/Natural/etc', 'grind_adjustment': 'Grover/Fijner', 'temp_c': 93}"
    )
    
    response = client.models.generate_content(
        model='gemini-3.7-flash',  # Bijgewerkt naar het actuele model
        contents=[prompt, image]
    )
    
    # Opschonen van de respons (verwijder eventuele markdown tekens)
    clean_json = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_json)

# ==========================================
# 3. SESSION STATE INITIALISATIE
# ==========================================
if "data" not in st.session_state:
    st.session_state.data = {
        "ratio": 16.6,
        "bean_name": "Scan je bonen",
        "process": "-",
        "grind_adj": "Scan nodig",
        "temp": 93
    }

# ==========================================
# 4. UI INTERFACE
# ==========================================
st.title("☕ BrewPrint Pro")
st.markdown("Scan je koffiezak voor een gepersonaliseerd recept.")

# Camera Sectie
uploaded_file = st.camera_input("Maak een foto van het etiket")

if uploaded_file:
    img = Image.open(uploaded_file)
    with st.spinner("AI Barista analyseert bonen..."):
        try:
            advice = get_ai_advice(img)
            st.session_state.data = {
                "ratio": advice['ratio'],
                "bean_name": advice['bean_name'],
                "process": advice['process'],
                "grind_adj": advice['grind_adjustment'],
                "temp": advice['temp_c']
            }
            st.success(f"Gedetecteerd: {st.session_state.data['bean_name']}")
        except Exception as e:
            st.error(f"Fout bij het lezen: {e}")

# Dashboard Sectie
st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader("📊 Recept Details")
    st.write(f"**Methode:** {st.session_state.data['process']}")
    st.write(f"**Maaladvies:** {st.session_state.data['grind_adj']}")
    st.write(f"**Temperatuur:** {st.session_state.data['temp']}°C")

with col2:
    st.subheader("⚖️ Dosering")
    water = st.slider("Water (gram)", 100, 1000, 250)
    coffee_needed = round(water / st.session_state.data['ratio'], 1)
    st.metric("Koffiebonen", f"{coffee_needed}g")

st.info(f"Gebruikte verhouding: 1:{st.session_state.data['ratio']}")

# ==========================================
# 5. CUSTOM STYLING
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #FBF8F5; }
    h1 { color: #C06C4C !important; }
    div[data-testid="stMetricValue"] { color: #2B1E1A !important; }
    </style>
""", unsafe_allow_html=True)