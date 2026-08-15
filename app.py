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
# 1. PAGINA CONFIGURATIE & BREWPRINT SETUP
# ==========================================
st.set_page_config(
    page_title="BrewPrint • Ultimate Specialty Coffee Station",
    page_icon="☕",
    layout="centered"
)

col_logo, col_title = st.columns([1, 4])
with col_logo:
    if os.path.exists("assets/brewprint_logo.png"):
        st.image("assets/brewprint_logo.png", use_container_width=True)
    else:
        st.write("☕")

with col_title:
    st.title("BrewPrint")
    st.caption("Ultimate Specialty Coffee Station")

st.write(
    "AI Label Herkenning • Visuele Zetmethode Picker • Top 3 Advies & Geschiktheid • "
    "Spa/Bar-le-Duc Water Blend • Live Voice Timer • Doorlooptijd Auto-Tuner • Molen Tracker"
)
st.markdown("---")

api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input("Voer je Gemini API Key in:", type="password")

# ==========================================
# 2. BESTANDEN & OPSLAG HULPFUNCTIES
# ==========================================
LOG_FILE = "brew_history.json"
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

brew_history = load_data(LOG_FILE, [])
maint_data = load_data(MAINTENANCE_FILE, {"ode_brew_count": 0, "comandante_brew_count": 0})

# ==========================================
# 3. HOOFD LOGICA & INPUTS
# ==========================================
if api_key:
    # GEBRUIK HIER FILE UPLOADER IN PLAATS VAN CAMERA INPUT
    uploaded_file = st.file_uploader("📷 Upload een foto van het etikett of maak er een met je telefoon", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Geüploade foto", use_container_width=True)

        st.markdown("---")
        st.subheader("⚙️ Instellingen voor je Zetbeurt")

        branddatum = st.date_input("Selecteer de branddatum van de koffie:", value=date.today())
        vandaag = date.today()
        dagen_oud = (vandaag - branddatum).days

        if dagen_oud < 0:
            st.warning("⚠️ De gekozen branddatum ligt in de toekomst!")
        elif dagen_oud <= 7:
            st.info(f"🌿 **Status:** Heel vers ({dagen_oud} dagen oud). Langere bloom en lagere temp aanbevolen.")
        elif dagen_oud <= 42:
            st.success(f"🔥 **Status:** Perfecte Sweet Spot ({dagen_oud} dagen oud)!")
        else:
            st.warning(f"⏳ **Status:** Ouder dan 6 weken ({dagen_oud} dagen oud). Fine-tune maalgraad/temp.")

        molen_keuze = st.selectbox(
            "Welke koffiemolen gebruik je?",
            ["Fellow Ode Gen 2", "Comandante C40", "Toon beiden (Comandante C40 & Fellow Ode Gen 2)"]
        )

        st.markdown("### ☕ Kies je Zetmethode")
        if "zetmethode" not in st.session_state:
            st.session_state["zetmethode"] = "V60"

        cols = st.columns(6)
        methodes = [
            ("V60", "https://img.icons8.com/isometric-line/400/v60-coffee-maker.png", "V60"),
            ("AeroPress", "https://img.icons8.com/isometric-line/400/french-press.png", "AeroPress"),
            ("Chemex", "https://img.icons8.com/isometric-line/400/chemex.png", "Chemex"),
            ("Shizuku", "https://img.icons8.com/isometric-line/400/cold-brew.png", "Hario Shizuku (Slow Drip)"),
            ("Clever", "https://img.icons8.com/isometric-line/400/pour-over.png", "Clever Dripper"),
            ("Syfon", "https://img.icons8.com/isometric-line/400/glass.png", "Syfon (Vacuum Pot)")
        ]

        for i, (label, img_url, full_name) in enumerate(methodes):
            with cols[i]:
                st.image(img_url, caption=label, use_container_width=True)
                if st.button(label, type="primary" if st.session_state["zetmethode"] == full_name else "secondary", use_container_width=True, key=f"btn_{label}"):
                    st.session_state["zetmethode"] = full_name
                    st.rerun()

        zetmethode = st.session_state["zetmethode"]

        if zetmethode == "AeroPress":
            filter_keuze = "AeroPress (AI kiest papier, metaal of dubbel)"
        elif zetmethode == "Hario Shizuku (Slow Drip)":
            filter_keuze = "Hario Shizuku Ingebouwd RVS Dripper Filter"
        elif zetmethode == "Clever Dripper":
            filter_keuze = st.selectbox("Welk filterpapier gebruik je?", ["Moccamaster Nr. 4 Papier", "Filtropa Nr. 4 Papier"])
        elif zetmethode == "Syfon (Vacuum Pot)":
            filter_keuze = st.selectbox("Welk filter gebruik je?", ["Katoenen Stoffen Filter", "Papieren Filter voor Syfon", "Metal Mesh Filter"])
        else:
            filter_keuze = st.selectbox("Welk filterpapier gebruik je?", ["Cafec Abaca+", "Hario V60 Japan", "Hario V60 Europa / Filtropa", "Ander / Standaard papier"])

        iced_brew = False
        if zetmethode not in ["Hario Shizuku (Slow Drip)", "Syfon (Vacuum Pot)"]:
            iced_brew = st.checkbox("🧊 Maak als Iced Flash Brew")

        water_opties = [300, 500, 600, 750] if zetmethode in ["Chemex", "Hario Shizuku (Slow Drip)", "Clever Dripper", "Syfon (Vacuum Pot)"] else [160, 300, 500]
        totaal_water = st.select_slider("Totaal hoeveelheid vloeistof / water (ml/gram):", options=water_opties, value=water_opties[0])

        if st.button("🚀 Genereer Recept & AI Advies", type="primary"):
            with st.spinner("Koffiezakje analyseren & recept berekenen..."):
                prompt = f"""
                Analyseer de afbeelding van het koffiezakje.
                Genereer een specifiek recept voor de zetmethode: {zetmethode}.
                Totaal beoogde vloeistof: {totaal_water}g.
                Iced Brew ingeschakeld: {iced_brew}.
                Gekozen molen(s): {molen_keuze}.
                Gekozen filter: {filter_keuze}.
                Leeftijd van de bonen: {dagen_oud} dagen.

                Geef EEN ENKEL JSON-object terug ingesloten in ```json ``` met exact deze structuur:
                ```json
                {{
                  "roaster": "Naam Branderij",
                  "coffee_name": "Naam Koffie / Herkomst",
                  "is_geschikt_voor_gekozen_methode": true,
                  "geschiktheids_toelichting": "Lichte toelichting.",
                  "top_3_zetmethodes": [
                    {{"rang": 1, "methode": "V60", "reden": "Toelichting"}},
                    {{"rang": 2, "methode": "Chemex", "reden": "Toelichting"}},
                    {{"rang": 3, "methode": "AeroPress", "reden": "Toelichting"}}
                  ],
                  "water_blend": {{
                    "spa_reine_g": 210,
                    "bar_le_duc_g": 90,
                    "toelichting": "70% Spa Reine / 30% Bar-le-Duc"
                  }},
                  "markdown_recept": "## Recept Samenvatting\\n- **Dosering:** XXg\\n- **Maalgraad:** XX",
                  "stappen": [
                    {{"start_sec": 0, "duur_sec": 45, "titel": "Bloom", "actie": "Giet 50g water", "doel_water_g": 50}},
                    {{"start_sec": 45, "duur_sec": 45, "titel": "Schenking", "actie": "Giet tot 160g", "doel_water_g": 160}}
                  ]
                }}
                ```
                """

                try:
                    if USING_NEW_SDK:
                        client = genai.Client(api_key=api_key)
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[prompt, image]
                        )
                    else:
                        legacy_genai.configure(api_key=api_key)
                        model = legacy_genai.GenerativeModel("gemini-1.5-flash")
                        response = model.generate_content([prompt, image])

                    st.session_state["recipe_raw"] = response.text
                    st.session_state["timer_active"] = False

                    if "Fellow Ode" in molen_keuze or "beiden" in molen_keuze:
                        maint_data["ode_brew_count"] += 1
                    if "Comandante" in molen_keuze or "beiden" in molen_keuze:
                        maint_data["comandante_brew_count"] += 1
                    save_data(MAINTENANCE_FILE, maint_data)

                except Exception as api_err:
                    st.error(f"❌ Er is een fout opgetreden bij de API-aanroep: {api_err}")

# ==========================================
# 4. WEERGAVE RECEPT & TIMER
# ==========================================
if "recipe_raw" in st.session_state:
    st.markdown("---")
    raw_text = st.session_state["recipe_raw"]
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", raw_text, re.DOTALL) or re.search(r"(\{.*\})", raw_text, re.DOTALL)

    if json_match:
        try:
            recipe_data = json.loads(json_match.group(1))

            top_3 = recipe_data.get("top_3_zetmethodes", [])
            if top_3:
                st.subheader("🏆 Top 3 AI Geadviseerde Zetmethodes")
                cols = st.columns(3)
                medailles = ["🥇 #1", "🥈 #2", "🥉 #3"]
                for idx, item in enumerate(top_3[:3]):
                    with cols[idx]:
                        st.markdown(f"#### {medailles[idx]} **{item.get('methode', '')}**")
                        st.caption(item.get("reden", ""))
                st.markdown("---")

            st.subheader("💡 Barista AI Geschiktheids-Analyse")
            if recipe_data.get("is_geschikt_voor_gekozen_methode", True):
                st.success(f"✅ {recipe_data.get('geschiktheids_toelichting', '')}")
            else:
                st.warning(f"⚠️ {recipe_data.get('geschiktheids_toelichting', '')}")

            water_blend = recipe_data.get("water_blend", {})
            if water_blend:
                st.subheader("💧 Water Blend (Spa Reine & Bar-le-Duc)")
                col_spa, col_bld = st.columns(2)
                col_spa.metric("🟦 Spa Reine", f"{water_blend.get('spa_reine_g', 0)} g")
                col_bld.metric("🟩 Bar-le-Duc", f"{water_blend.get('bar_le_duc_g', 0)} g")

            st.markdown("---")
            st.markdown(recipe_data.get("markdown_recept", ""))

            # Timer functionaliteit
            st.markdown("---")
            st.subheader("⏱️ Real-Time Timer met Live Gesproken Begeleiding")
            stappen = recipe_data.get("stappen", [])

            if stappen:
                totaal_tijd = stappen[-1]["start_sec"] + stappen[-1]["duur_sec"]
                col1, col2 = st.columns(2)
                if col1.button("▶️ Start Live Timer", type="primary"):
                    st.session_state["timer_active"] = True
                if col2.button("⏹️ Reset Timer"):
                    st.session_state["timer_active"] = False

                timer_container = st.empty()
                if st.session_state.get("timer_active", False):
                    laatste_gesproken = -1
                    for sec in range(0, totaal_tijd + 1):
                        if not st.session_state.get("timer_active", False):
                            break

                        huidige_idx = 0
                        huidige_stap = stappen[0]
                        for idx, s in enumerate(stappen):
                            if s["start_sec"] <= sec < (s["start_sec"] + s["duur_sec"]):
                                huidige_stap = s
                                huidige_idx = idx
                                break

                        if huidige_idx != laatste_gesproken:
                            tekst = f"{huidige_stap['titel']}. {huidige_stap['actie']}"
                            st.components.v1.html(f'<script>var msg=new SpeechSynthesisUtterance("{tekst}");msg.lang="nl-NL";window.speechSynthesis.speak(msg);</script>', height=0)
                            laatste_gesproken = huidige_idx

                        with timer_container.container():
                            st.metric(label="⏱️ Tijd", value=f"{sec // 60:02d}:{sec % 60:02d}")
                            st.progress(min(1.0, sec / totaal_tijd))
                            st.markdown(f"### 🎯 Stap: **{huidige_stap['titel']}**")
                            st.info(f"👉 **ACTIE:** {huidige_stap['actie']}")
                            st.success(f"⚖️ **Doel op schaal:** **{huidige_stap['doel_water_g']}g**")
                        time.sleep(1)

        except Exception as e:
            st.error(f"Fout bij het verwerken van gegevens: {e}")

# ==========================================
# 5. MOLEN DASHBOARD
# ==========================================
st.markdown("---")
st.subheader("🧹 Koffiemolen Onderhoud Dashboard")
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### ⚙️ Fellow Ode Gen 2")
    st.write(f"Zetbeurten: **{maint_data.get('ode_brew_count', 0)}**")
    if st.button("Reset Ode Teller"):
        maint_data["ode_brew_count"] = 0
        save_data(MAINTENANCE_FILE, maint_data)
        st.rerun()

with col_b:
    st.markdown("### 🪵 Comandante C40")
    st.write(f"Zetbeurten: **{maint_data.get('comandante_brew_count', 0)}**")
    if st.button("Reset Comandante Teller"):
        maint_data["comandante_brew_count"] = 0
        save_data(MAINTENANCE_FILE, maint_data)
        st.rerun()