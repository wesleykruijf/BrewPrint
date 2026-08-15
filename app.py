import json
import os
import re
import time
from datetime import date
from PIL import Image
import streamlit as st

# Probeer de nieuwste SDK, val zo nodig terug op de legacy SDK
try:
    from google import genai
    USING_NEW_SDK = True
except ImportError:
    import google.generativeai as legacy_genai
    USING_NEW_SDK = False

# ==========================================
# 1. PAGINA CONFIGURATIE
# ==========================================
st.set_page_config(
    page_title="BrewPrint • Ultimate Specialty Coffee Station",
    page_icon="☕",
    layout="centered"
)

st.title("BrewPrint ☕")
st.caption("Ultimate Specialty Coffee Station")
st.markdown("---")

api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input("Voer je Gemini API Key in:", type="password")

# ==========================================
# 2. BESTANDEN & OPSLAG HULPFUNCTIES
# ==========================================
MAINTENANCE_FILE = "grinder_maintenance.json"

def load_data(file_path, default_val):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_val
    return default_val

def save_data(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

maint_data = load_data(MAINTENANCE_FILE, {"ode_brew_count": 0, "comandante_brew_count": 0})

# ==========================================
# 3. HOOFD LOGICA & INPUTS
# ==========================================
if api_key:
    # Aangepast: Camera input vervangen door file uploader
    uploaded_file = st.file_uploader("Upload een foto van het etiket:", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Geüploade foto", use_container_width=True)

        st.markdown("---")
        st.subheader("⚙️ Instellingen voor je Zetbeurt")

        branddatum = st.date_input("Selecteer de branddatum:", value=date.today())
        dagen_oud = (date.today() - branddatum).days
        st.info(f"Bonen zijn {dagen_oud} dagen oud.")

        molen_keuze = st.selectbox("Welke koffiemolen gebruik je?", ["Fellow Ode Gen 2", "Comandante C40", "Beiden"])

        st.markdown("### ☕ Kies je Zetmethode")
        if "zetmethode" not in st.session_state: st.session_state["zetmethode"] = "V60"
        
        zetmethode = st.radio("Zetmethode", ["V60", "AeroPress", "Chemex", "Clever Dripper"], horizontal=True)
        st.session_state["zetmethode"] = zetmethode

        totaal_water = st.select_slider("Totaal water (ml):", options=[160, 300, 500, 750], value=300)

        if st.button("🚀 Genereer Recept"):
            with st.spinner("AI berekent recept..."):
                prompt = f"Analyseer dit koffiezakje en maak een recept voor {zetmethode} met {totaal_water}ml water. Geef JSON terug met keys: roaster, coffee_name, markdown_recept, stappen (lijst met start_sec, duur_sec, titel, actie, doel_water_g)."

                try:
                    # Aangepast: Modelnaam gewijzigd naar gemini-1.5-flash
                    if USING_NEW_SDK:
                        client = genai.Client(api_key=api_key)
                        response = client.models.generate_content(
                            model="gemini-1.5-flash", 
                            contents=[prompt, image]
                        )
                    else:
                        legacy_genai.configure(api_key=api_key)
                        model = legacy_genai.GenerativeModel("gemini-1.5-flash")
                        response = model.generate_content([prompt, image])

                    st.session_state["recipe_raw"] = response.text
                except Exception as e:
                    st.error(f"Fout bij API: {e}")

# ==========================================
# 4. WEERGAVE RECEPT
# ==========================================
if "recipe_raw" in st.session_state:
    raw_text = st.session_state["recipe_raw"]
    json_match = re.search(r"(\{.*\})", raw_text, re.DOTALL)
    if json_match:
        recipe = json.loads(json_match.group(1))
        st.markdown(recipe.get("markdown_recept", "Geen recept gevonden."))
        st.success("Recept gegenereerd!")

# ==========================================
# 5. ONDERHOUD
# ==========================================
st.markdown("---")
st.subheader("🧹 Molen Dashboard")
st.write(f"Ode: {maint_data['ode_brew_count']} | Comandante: {maint_data['comandante_brew_count']}")