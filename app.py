import json
import os
import time
from datetime import date
from PIL import Image
import streamlit as st
from google import genai

# ==========================================
# 1. PAGINA CONFIGURATIE
# ==========================================
st.set_page_config(
    page_title="Ultimate Barista AI Station", page_icon="☕", layout="centered"
)

st.title("☕ Ultimate Specialty Coffee Station")
st.write(
    "AI Label Herkenning • Visuele Zetmethode Picker • Geschiktheid & Advies • "
    "Water Blend & Iced Brew • Live Voice Timer • Doorlooptijd Auto-Tuner • Molen Tracker"
)

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
maint_data = load_data(
    MAINTENANCE_FILE, {"ode_brew_count": 0, "comandante_brew_count": 0}
)

# ==========================================
# 3. API KEY & INPUT SECTIE
# ==========================================
api_key = st.text_input("Voer je Gemini API Key in:", type="password")

if api_key:
    client = genai.Client(api_key=api_key)

    uploaded_file = st.camera_input(
        "Maak een foto van het etiket"
    ) or st.file_uploader("Of kies een afbeelding...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Geüploade foto", use_container_width=True)

        st.markdown("---")
        st.subheader("⚙️ Instellingen voor je Zetbeurt")

        branddatum = st.date_input(
            "Selecteer de branddatum van de koffie:", value=date.today()
        )
        vandaag = date.today()
        dagen_oud = (vandaag - branddatum).days

        if dagen_oud < 0:
            st.warning("⚠️ De gekozen branddatum ligt in de toekomst!")
        elif dagen_oud <= 7:
            st.info(
                f"🌿 **Status:** Heel vers ({dagen_oud} dagen oud). Langere bloom en lagere temp."
            )
        elif dagen_oud <= 42:
            st.success(
                f"🔥 **Status:** Perfecte Sweet Spot ({dagen_oud} dagen oud)!"
            )
        else:
            st.warning(
                f"⏳ **Status:** Ouder dan 6 weken ({dagen_oud} dagen oud). Fine-tune maalgraad/temp."
            )

        molen_keuze = st.selectbox(
            "Welke koffiemolen gebruik je?",
            [
                "Fellow Ode Gen 2",
                "Comandante C40",
                "Toon beiden (Comandante C40 & Fellow Ode Gen 2)",
            ],
        )

        # Visuele Zetmethode Selectie
        st.markdown("### ☕ Kies je Zetmethode")

        IMG_V60 = "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400&auto=format&fit=crop&q=80"
        IMG_AEROPRESS = "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?w=400&auto=format&fit=crop&q=80"
        IMG_CHEMEX = "https://images.unsplash.com/photo-1541167760496-1628856ab772?w=400&auto=format&fit=crop&q=80"
        IMG_SHIZUKU = "https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=400&auto=format&fit=crop&q=80"

        if "zetmethode" not in st.session_state:
            st.session_state["zetmethode"] = "V60"

        col_v60, col_aero, col_chem, col_shiz = st.columns(4)

        with col_v60:
            st.image(IMG_V60, caption="Hario V60", use_container_width=True)
            if st.button(
                "Kies V60",
                type=(
                    "primary"
                    if st.session_state["zetmethode"] == "V60"
                    else "secondary"
                ),
                use_container_width=True,
            ):
                st.session_state["zetmethode"] = "V60"
                st.rerun()

        with col_aero:
            st.image(
                IMG_AEROPRESS, caption="AeroPress", use_container_width=True
            )
            if st.button(
                "Kies AeroPress",
                type=(
                    "primary"
                    if st.session_state["zetmethode"] == "AeroPress"
                    else "secondary"
                ),
                use_container_width=True,
            ):
                st.session_state["zetmethode"] = "AeroPress"
                st.rerun()

        with col_chem:
            st.image(IMG_CHEMEX, caption="Chemex", use_container_width=True)
            if st.button(
                "Kies Chemex",
                type=(
                    "primary"
                    if st.session_state["zetmethode"] == "Chemex"
                    else "secondary"
                ),
                use_container_width=True,
            ):
                st.session_state["zetmethode"] = "Chemex"
                st.rerun()

        with col_shiz:
            st.image(
                IMG_SHIZUKU,
                caption="Hario Shizuku",
                use_container_width=True,
            )
            if st.button(
                "Kies Shizuku",
                type=(
                    "primary"
                    if st.session_state["zetmethode"]
                    == "Hario Shizuku (Slow Drip)"
                    else "secondary"
                ),
                use_container_width=True,
            ):
                st.session_state["zetmethode"] = "Hario Shizuku (Slow Drip)"
                st.rerun()

        zetmethode = st.session_state["zetmethode"]

        # Dynamische filteropties
        if zetmethode == "AeroPress":
            filter_keuze = "AeroPress (AI kiest de optimale filtercombinatie)"
            st.info(
                "💡 **AeroPress Modus:** De AI analyseert de koffieboon en adviseert direct de ideale combinatie (1x Papier, 2x Papier of Papier + RVS Metaal)."
            )
        elif zetmethode == "Hario Shizuku (Slow Drip)":
            filter_keuze = "Hario Shizuku Ingebouwd RVS Dripper Filter"
            st.info(
                "💧 **Hario Shizuku Modus:** Slow drip koudwater extractie (druppeltijd ~1-2 uur)."
            )
        else:
            filter_keuze = st.selectbox(
                "Welk filterpapier gebruik je?",
                [
                    "Cafec Abaca+ (Snelle, hele schone flow)",
                    "Hario V60 Japan (Standaard / Tabbed)",
                    "Hario V60 Europa / Filtropa (Tragere flow)",
                    "Ander / Standaard papier",
                ],
            )

        # Iced Flash Brew Toggle
        iced_brew = False
        if zetmethode != "Hario Shizuku (Slow Drip)":
            iced_brew = st.checkbox(
                "🧊 Maak als Iced Flash Brew (met ijsklontjes in de server)"
            )

        water_opties = (
            [160, 300, 500]
            if zetmethode not in ["Chemex", "Hario Shizuku (Slow Drip)"]
            else [300, 500, 600, 750]
        )
        standaard_water = (
            500
            if zetmethode == "Hario Shizuku (Slow Drip)"
            else (300 if zetmethode == "Chemex" else 160)
        )

        totaal_water = st.select_slider(
            "Totaal hoeveelheid vloeistof / water (ml/gram):",
            options=water_opties,
            value=standaard_water,
        )

        if st.button("🚀 Genereer Recept & AI Advies", type="primary"):
            with st.spinner(
                "Koffiezakje analyseren, geschiktheid bepalen & recept berekenen..."
            ):
                prompt = f"""
                Jij bent een meesterbarista. Analyseer de afbeelding van het koffiezakje.
                Extract: 
                1. Branderij / Roaster
                2. Koffienaam / Herkomst
                3. Smaaknotities & Branding (Licht/Medium/Donker)

                BEOORDEEL DE GEKOZEN ZETMETHODE ({zetmethode}):
                1. Bepaal of deze specifieke koffieboon geschikte eigenschappen heeft voor {zetmethode}.
                2. Bepaal wat op basis van de boon (herkomst, verwerking, branding, smaaknotities) de ABSOLUUT MEEST GESCHIKTE ZETMETHODE zou zijn (kies uit: V60, AeroPress, Chemex, of Hario Shizuku).

                Genereer een recept voor {zetmethode} met totaal {totaal_water}g vloeistof.
                - Molen: {molen_keuze}
                - Filter: {filter_keuze}
                - Leeftijd: {dagen_oud} dagen oud.
                - Iced Flash Brew modus: {"JA" if iced_brew else "NEE"}

                SPECIFIEK VOOR HARIO SHIZUKU:
                Als zetmethode = "Hario Shizuku (Slow Drip)":
                - Gebruik ijskoud water (0-5°C).
                - Adviseer een gemiddeld fijne maalgraad.
                - Geef stappen voor het bevochtigen van de koffie puck en instellen van de druppelsnelheid.

                STRIKT FORMAT: Geef eerst een JSON blok terug met exact de structuur, daarna de uitgeschreven markdown samenvatting.

                JSON Structuur vereist:
                ```json
                {{
                  "roaster": "Naam Branderij",
                  "coffee_name": "Naam Koffie",
                  "is_geschikt_voor_gekozen_methode": true,
                  "geschiktheids_toelichting": "Deze fruitige Ethiopische koffie komt fantastisch tot zijn recht op {zetmethode}.",
                  "meest_geschikte_zetmethode": "V60",
                  "reden_meest_geschikt": "De hoge aciditeit en florale tonen schitteren het beste bij een heldere V60 opgieting.",
                  "filter_advies": "1x Papier",
                  "is_iced": {str(iced_brew).lower()},
                  "ice_gram": {int(totaal_water * 0.4) if iced_brew else 0},
                  "hot_water_gram": {int(totaal_water * 0.6) if iced_brew else totaal_water},
                  "water_blend": {{
                    "spa_gram": {int(totaal_water * 0.7)},
                    "bar_gram": {int(totaal_water * 0.3)},
                    "ratio": "70% Spa / 30% Bar-le-Duc"
                  }},
                  "dosering": "18g",
                  "maalgraad": "Stand 4.1 op Ode Gen 2 / 12 clicks Comandante",
                  "temperatuur": "93°C",
                  "stappen": [
                    {{"start_sec": 0, "duur_sec": 45, "titel": "Bloom Phase", "actie": "Giet 50g heet water in spiraal.", "doel_water_g": 50}},
                    {{"start_sec": 45, "duur_sec": 30, "titel": "Schenking 1", "actie": "Giet rustig door tot 150g.", "doel_water_g": 150}},
                    {{"start_sec": 75, "duur_sec": 45, "titel": "Drawdown", "actie": "Laat doorlopen.", "doel_water_g": 180}}
                  ]
                }}
                ```
                Geef daarna de mooie markdown samenvatting inclusief AI Geschiktheidsadvies, Water Blend, Maalgraad en Recept.
                """

                # API Call met de nieuwe Google GenAI SDK
                response = client.models.generate_content(
                    model="gemini-1.5-flash", contents=[prompt, image]
                )

                st.session_state["recipe_raw"] = response.text
                st.session_state["timer_active"] = False

                if "Fellow Ode" in molen_keuze or "beiden" in molen_keuze:
                    maint_data["ode_brew_count"] += 1
                if "Comandante" in molen_keuze or "beiden" in molen_keuze:
                    maint_data["comandante_brew_count"] += 1
                save_data(MAINTENANCE_FILE, maint_data)

    if "recipe_raw" in st.session_state:
        st.markdown("---")
        raw_text = st.session_state["recipe_raw"]

        try:
            json_str = raw_text.split("```json")[1].split("```")[0].strip()
            recipe_data = json.loads(json_str)
            markdown_text = raw_text.split("```")[-1].strip()

            roaster = recipe_data.get("roaster", "Onbekend")
            coffee_name = recipe_data.get("coffee_name", "Onbekend")

            # AI Geschiktheidsadvies Kaart
            st.subheader("💡 Barista AI Geschiktheids-Analyse")
            is_geschikt = recipe_data.get(
                "is_geschikt_voor_gekozen_methode", True
            )
            meest_geschikt = recipe_data.get(
                "meest_geschikte_zetmethode", "V60"
            )

            if is_geschikt:
                st.success(
                    f"✅ **Geschikt voor {zetmethode}!** {recipe_data.get('geschiktheids_toelichting', '')}"
                )
            else:
                st.warning(
                    f"⚠️ **Let op:** {recipe_data.get('geschiktheids_toelichting', '')}"
                )

            if meest_geschikt.lower() != zetmethode.lower():
                st.info(
                    f"🌟 **Meest optimale zetmethode voor deze boon:** **{meest_geschikt}**\n\n_{recipe_data.get('reden_meest_geschikt', '')}_"
                )

            st.markdown("---")
            st.markdown(markdown_text)

            # Real-Time Timer
            st.markdown("---")
            st.subheader(
                "⏱️ Real-Time Timer met Live Gesproken Begeleiding"
            )

            stappen = recipe_data.get("stappen", [])

            if stappen:
                totaal_tijd = (
                    stappen[-1]["start_sec"] + stappen[-1]["duur_sec"]
                )

                col1, col2 = st.columns(2)
                with col1:
                    start_btn = st.button(
                        "▶️ Start Live Timer & Spraak", type="primary"
                    )
                with col2:
                    stop_btn = st.button("⏹️ Reset Timer")

                if start_btn:
                    st.session_state["timer_active"] = True

                if stop_btn:
                    st.session_state["timer_active"] = False

                timer_container = st.empty()

                if st.session_state.get("timer_active", False):
                    laatste_gesproken_stap = -1
                    for huidig_sec in range(0, totaal_tijd + 1):
                        if not st.session_state.get("timer_active", False):
                            break

                        huidige_stap_idx = 0
                        huidige_stap = stappen[0]
                        for idx, s in enumerate(stappen):
                            if (
                                s["start_sec"]
                                <= huidig_sec
                                < (s["start_sec"] + s["duur_sec"])
                            ):
                                huidige_stap = s
                                huidige_stap_idx = idx
                                break

                        if huidige_stap_idx != laatste_gesproken_stap:
                            tekst_om_te_spreken = f"{huidige_stap['titel']}. {huidige_stap['actie']}"
                            tts_html = f"""
                            <script>
                            var msg = new SpeechSynthesisUtterance("{tekst_om_te_spreken}");
                            msg.lang = 'nl-NL';
                            window.speechSynthesis.speak(msg);
                            </script>
                            """
                            st.components.v1.html(tts_html, height=0)
                            laatste_gesproken_stap = huidige_stap_idx

                        minuten = huidig_sec // 60
                        seconden = huidig_sec % 60
                        tijd_str = f"{minuten:02d}:{seconden:02d}"
                        voortgang = min(1.0, huidig_sec / totaal_tijd)

                        with timer_container.container():
                            st.metric(
                                label="⏱️ Totale Tijd", value=tijd_str
                            )
                            st.progress(voortgang)

                            st.markdown(
                                f"### 🎯 Stap: **{huidige_stap['titel']}**"
                            )
                            st.info(
                                f"👉 **ACTIE NU:** {huidige_stap['actie']}"
                            )
                            st.success(
                                f"⚖️ **Doelgewicht op weegschaal:** **{huidige_stap['doel_water_g']} gram**"
                            )

                        time.sleep(1)

                    if st.session_state.get("timer_active", False):
                        st.balloons()
                        st.success(
                            "🎉 Zetsessie voltooid! Vul hieronder je daadwerkelijke doorlooptijd in."
                        )
                        st.session_state["timer_active"] = False

            # Daadwerkelijke Doorlooptijd & Auto-Tuner
            st.markdown("---")
            st.subheader(
                "⏱️ Daadwerkelijke Doorlooptijd & Recept Auto-Tuner"
            )
            st.write(
                "Hoe lang duurde de totale zetbeurt van het eerste drupje tot het laatste drupje / sissen?"
            )

            doel_minuten = totaal_tijd // 60
            doel_seconden = totaal_tijd % 60
            st.info(
                f"🎯 **Streef/Doel doorlooptijd uit recept:** `{doel_minuten:02d}:{doel_seconden:02d}` ({totaal_tijd} seconden)"
            )

            col_m, col_s = st.columns(2)
            with col_m:
                actueel_min = st.number_input(
                    "Daadwerkelijke minuten:",
                    min_value=0,
                    max_value=120,
                    value=doel_minuten,
                )
            with col_s:
                actueel_sec = st.number_input(
                    "Daadwerkelijke seconden:",
                    min_value=0,
                    max_value=59,
                    value=doel_seconden,
                )

            daadwerkelijke_totaal_sec = (actueel_min * 60) + actueel_sec
            verschil_sec = daadwerkelijke_totaal_sec - totaal_tijd

            # Smaak-Tuner & Rating Opslaan
            st.markdown("---")
            st.subheader("🧪 AI Smaak-Tuner & Beoordeling")

            rating = st.slider("Beoordeel dit kopje (1-5 sterren):", 1, 5, 5)
            smaak_feedback = st.radio(
                "Hoe was de balans van de extractie?",
                [
                    "✨ Perfect gebalanceerd & heerlijk zoet",
                    "🍋 Te zuur / Flauw / Te snel doorgelopen (Onder-extractie)",
                    "🍫 Te bitter / Droog / Zwaar (Over-extractie)",
                ],
            )

            if st.button(
                "💾 Opslaan & Recept Aanpassen voor Volgende Keer"
            ):
                log_entry = {
                    "datum": str(date.today()),
                    "roaster": roaster,
                    "coffee_name": coffee_name,
                    "target_time_sec": totaal_tijd,
                    "actual_time_sec": daadwerkelijke_totaal_sec,