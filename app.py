import json
import os
import re
import time
from datetime import date
from PIL import Image
import streamlit as st
from google import genai

# ==========================================
# 1. PAGINA CONFIGURATIE & BREWPRINT SETUP
# ==========================================
st.set_page_config(
    page_title="BrewPrint • Ultimate Specialty Coffee Station",
    page_icon="☕",
    layout="centered"
)

# Header met Logo en Titel
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
    "AI Label Herkenning • Visuele Zetmethode Picker • Geschiktheid & Advies • "
    "Spa/Bar-le-Duc Water Blend • Live Voice Timer • Doorlooptijd Auto-Tuner • Molen Tracker"
)
st.markdown("---")

# API Key ophalen
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


def extract_icons(image_path="assets/coffee_methods.png"):
    """Snijdt het 3x3 grid automatisch op in losse iconen."""
    if not os.path.exists(image_path):
        return

    os.makedirs("assets/icons", exist_ok=True)
    img = Image.open(image_path)
    w, h = img.size
    cw, ch = w / 3, h / 3

    crops = {
        "v60.png": (0, ch, cw, ch * 2),          # Midden-links (V60 / Pour-over)
        "french_press.png": (cw, 0, cw * 2, ch), # Boven-midden (French Press)
        "chemex.png": (cw, ch * 2, cw * 2, h),   # Onder-midden (Chemex)
        "aeropress.png": (cw * 2, ch * 2, w, h), # Rechtsonder (AeroPress)
    }

    for filename, box in crops.items():
        out_path = os.path.join("assets/icons", filename)
        if not os.path.exists(out_path):
            img.crop(box).save(out_path)


# Voer de uitsnijding direct uit bij het opstarten
extract_icons("assets/coffee_methods.png")

brew_history = load_data(LOG_FILE, [])
maint_data = load_data(
    MAINTENANCE_FILE, {"ode_brew_count": 0, "comandante_brew_count": 0}
)

# ==========================================
# 3. HOOFD LOGICA & INPUTS
# ==========================================
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

        # 3.1 Branddatum & Versheid Status
        branddatum = st.date_input(
            "Selecteer de branddatum van de koffie:", value=date.today()
        )
        vandaag = date.today()
        dagen_oud = (vandaag - branddatum).days

        if dagen_oud < 0:
            st.warning("⚠️ De gekozen branddatum ligt in de toekomst!")
        elif dagen_oud <= 7:
            st.info(
                f"🌿 **Status:** Heel vers ({dagen_oud} dagen oud). Langere bloom en lagere temp aanbevolen."
            )
        elif dagen_oud <= 42:
            st.success(
                f"🔥 **Status:** Perfecte Sweet Spot ({dagen_oud} dagen oud)!"
            )
        else:
            st.warning(
                f"⏳ **Status:** Ouder dan 6 weken ({dagen_oud} dagen oud). Fine-tune maalgraad/temp."
            )

        # 3.2 Molen Keuze
        molen_keuze = st.selectbox(
            "Welke koffiemolen gebruik je?",
            [
                "Fellow Ode Gen 2",
                "Comandante C40",
                "Toon beiden (Comandante C40 & Fellow Ode Gen 2)",
            ],
        )

        # 3.3 Visuele Zetmethode Picker (Automatisch uitgesneden iconen)
        st.markdown("### ☕ Kies je Zetmethode")

        IMG_V60 = "assets/icons/v60.png"
        IMG_FRENCH = "assets/icons/french_press.png"
        IMG_CHEMEX = "assets/icons/chemex.png"
        IMG_AEROPRESS = "assets/icons/aeropress.png"

        if "zetmethode" not in st.session_state:
            st.session_state["zetmethode"] = "V60"

        col_v60, col_aero, col_chem, col_french = st.columns(4)

        with col_v60:
            if os.path.exists(IMG_V60):
                st.image(IMG_V60, caption="Hario V60", use_container_width=True)
            if st.button(
                "Kies V60",
                type="primary" if st.session_state["zetmethode"] == "V60" else "secondary",
                use_container_width=True,
            ):
                st.session_state["zetmethode"] = "V60"
                st.rerun()

        with col_aero:
            if os.path.exists(IMG_AEROPRESS):
                st.image(IMG_AEROPRESS, caption="AeroPress", use_container_width=True)
            if st.button(
                "Kies AeroPress",
                type="primary" if st.session_state["zetmethode"] == "AeroPress" else "secondary",
                use_container_width=True,
            ):
                st.session_state["zetmethode"] = "AeroPress"
                st.rerun()

        with col_chem:
            if os.path.exists(IMG_CHEMEX):
                st.image(IMG_CHEMEX, caption="Chemex", use_container_width=True)
            if st.button(
                "Kies Chemex",
                type="primary" if st.session_state["zetmethode"] == "Chemex" else "secondary",
                use_container_width=True,
            ):
                st.session_state["zetmethode"] = "Chemex"
                st.rerun()

        with col_french:
            if os.path.exists(IMG_FRENCH):
                st.image(IMG_FRENCH, caption="French Press", use_container_width=True)
            if st.button(
                "Kies French Press",
                type="primary" if st.session_state["zetmethode"] == "French Press" else "secondary",
                use_container_width=True,
            ):
                st.session_state["zetmethode"] = "French Press"
                st.rerun()

        zetmethode = st.session_state["zetmethode"]

        # 3.4 Dynamische Filterkeuze per methode
        if zetmethode == "AeroPress":
            filter_keuze = "AeroPress (AI kiest papier, metaal of dubbel)"
            st.info("💡 **AeroPress Modus:** De AI kiest de optimale filtercombinatie.")
        elif zetmethode == "French Press":
            filter_keuze = "Ingebouwd RVS Filter"
            st.info("☕ **French Press Modus:** Volle body immersie-extractie.")
        elif zetmethode == "Chemex":
            filter_keuze = "Chemex Dik Filterpapier"
            st.info("☕ **Chemex Modus:** Zeer heldere kop koffie met dikke filters.")
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

        # 3.5 Iced Brew & Water Volume Logica
        iced_brew = False
        if zetmethode != "French Press":
            iced_brew = st.checkbox("🧊 Maak als Iced Flash Brew")

        if zetmethode in ["Chemex", "French Press"]:
            water_opties = [300, 500, 600, 750]
            standaard_water = 500 if zetmethode == "French Press" else 300
        else:
            water_opties = [160, 300, 500]
            standaard_water = 160

        totaal_water = st.select_slider(
            "Totaal hoeveelheid vloeistof / water (ml/gram):",
            options=water_opties,
            value=standaard_water,
        )

        st.info("💧 **Water Receptuur:** Er wordt gewerkt met een mengsel van **Spa Reine** (zacht/lage mineralen) en **Bar-le-Duc** (hogere mineralisatie) op basis van de geanalyseerde bonen.")

        # 3.6 Recept Generatie Knop
        if st.button("🚀 Genereer Recept & AI Advies", type="primary"):
            with st.spinner("Koffiezakje analyseren & recept berekenen..."):
                prompt = f"""
                Analyseer de afbeelding van het koffiezakje.
                Genereer een specifiek recept voor de zetmethode: {zetmethode}.
                Totaal beoogde vloeistof: {totaal_water}g.
                Iced Brew ingeschakeld: {iced_brew}.
                Gekozen molen(s): {molen_keuze}.
                Gekozen filterpapier: {filter_keuze}.
                Leeftijd van de bonen: {dagen_oud} dagen.

                Waterrecept instructie:
                Bereken op basis van de bonen (herkomst, verwerkingsmethode en verwachte zuren/mineralen) de ideale water-mix van Spa Reine (zeer zacht, 30 PPM) en Bar-le-Duc (rijker aan bicarbonaat/calcium, ~200 PPM) voor exact {totaal_water}g water.
                Lichte, heel fruitige/florale koffie heeft meer Spa Reine nodig (bijv. 70-80%). Vollere, gewassen of donkerder gebrande koffie verdraagt meer Bar-le-Duc (bijv. 40-50%).

                Geef EEN ENKEL JSON-object terug ingesloten in ```json ``` met exact de volgende structuur:
                ```json
                {{
                  "roaster": "Naam Branderij",
                  "coffee_name": "Naam Koffie / Herkomst",
                  "is_geschikt_voor_gekozen_methode": true,
                  "geschiktheids_toelichting": "Lichte toelichting waarom wel of niet geschikt.",
                  "meest_geschikte_zetmethode": "V60",
                  "reden_meest_geschikt": "Lichte toelichting waarom deze methode het beste smaakprofiel haalt.",
                  "water_blend": {{
                    "spa_reine_g": 210,
                    "bar_le_duc_g": 90,
                    "toelichting": "70% Spa Reine / 30% Bar-le-Duc gekozen om de frisse aciditeit en florale tonen te accentueren."
                  }},
                  "markdown_recept": "## Recept Samenvatting\\n- **Dosering:** XXg\\n- **Maalgraad:** XX (Ode / Comandante)\\n- **Watertemperatuur:** XX°C\\n- **Ratio:** 1:XX",
                  "stappen": [
                    {{"start_sec": 0, "duur_sec": 45, "titel": "Bloom", "actie": "Giet XXg water met ronddraaiende beweging", "doel_water_g": 50}},
                    {{"start_sec": 45, "duur_sec": 45, "titel": "Eerste Schenking", "actie": "Giet rustig door tot XXg", "doel_water_g": 160}}
                  ]
                }}
                ```
                """

                try:
                    # Interactions API aanroep met gemini-2.5-flash
                    response = client.interactions.create(
                        model="gemini-2.5-flash",
                        contents=[prompt, image]
                    )

                    st.session_state["recipe_raw"] = response.text
                    st.session_state["timer_active"] = False

                    # Molen Teller Update
                    if "Fellow Ode" in molen_keuze or "beiden" in molen_keuze:
                        maint_data["ode_brew_count"] += 1
                    if "Comandante" in molen_keuze or "beiden" in molen_keuze:
                        maint_data["comandante_brew_count"] += 1
                    save_data(MAINTENANCE_FILE, maint_data)

                except Exception as api_err:
                    st.error(f"❌ Er is een fout opgetreden bij de API-aanroep: {api_err}")

# ==========================================
# 4. WEERGAVE RECEPT & LIVE TIMER
# ==========================================
if "recipe_raw" in st.session_state:
    st.markdown("---")
    raw_text = st.session_state["recipe_raw"]

    json_match = re.search(r"```json\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
    if not json_match:
        json_match = re.search(r"(\{.*\})", raw_text, re.DOTALL)

    if json_match:
        try:
            recipe_data = json.loads(json_match.group(1))

            roaster = recipe_data.get("roaster", "Onbekend")
            coffee_name = recipe_data.get("coffee_name", "Onbekend")

            # Geschiktheids-analyse
            st.subheader("💡 Barista AI Geschiktheids-Analyse")
            is_geschikt = recipe_data.get("is_geschikt_voor_gekozen_methode", True)
            meest_geschikt = recipe_data.get("meest_geschikte_zetmethode", "V60")

            if is_geschikt:
                st.success(f"✅ **Geschikt voor {st.session_state.get('zetmethode', 'deze methode')}!** {recipe_data.get('geschiktheids_toelichting', '')}")
            else:
                st.warning(f"⚠️ **Let op:** {recipe_data.get('geschiktheids_toelichting', '')}")

            if meest_geschikt.lower() != st.session_state.get('zetmethode', '').lower():
                st.info(f"🌟 **Meest optimale zetmethode voor deze boon:** **{meest_geschikt}**\n\n_{recipe_data.get('reden_meest_geschikt', '')}_")

            st.markdown("---")

            # Water Blend Weergave
            water_blend = recipe_data.get("water_blend", {})
            if water_blend:
                st.subheader("💧 Exacte Water Blend (Spa Reine & Bar-le-Duc)")
                col_spa, col_bld = st.columns(2)
                with col_spa:
                    st.metric("🟦 Spa Reine", f"{water_blend.get('spa_reine_g', 0)} gram")
                with col_bld:
                    st.metric("🟩 Bar-le-Duc", f"{water_blend.get('bar_le_duc_g', 0)} gram")
                st.caption(f"💡 _{water_blend.get('toelichting', '')}_")
                st.markdown("---")

            st.markdown(recipe_data.get("markdown_recept", "Geen recept details beschikbaar."))

            # 4.1 Real-Time Live Voice Timer
            st.markdown("---")
            st.subheader("⏱️ Real-Time Timer met Live Gesproken Begeleiding")
            stappen = recipe_data.get("stappen", [])

            if stappen:
                totaal_tijd = stappen[-1]["start_sec"] + stappen[-1]["duur_sec"]

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("▶️ Start Live Timer & Spraak", type="primary"):
                        st.session_state["timer_active"] = True
                with col2:
                    if st.button("⏹️ Reset Timer"):
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
                            if s["start_sec"] <= huidig_sec < (s["start_sec"] + s["duur_sec"]):
                                huidige_stap = s
                                huidige_stap_idx = idx
                                break

                        # Spraak via Browser SpeechSynthesis API
                        if huidige_stap_idx != laatste_gesproken_stap:
                            tekst = f"{huidige_stap['titel']}. {huidige_stap['actie']}"
                            tts_html = f"""
                            <script>
                            var msg = new SpeechSynthesisUtterance("{tekst}");
                            msg.lang = 'nl-NL';
                            window.speechSynthesis.speak(msg);
                            </script>
                            """
                            st.components.v1.html(tts_html, height=0)
                            laatste_gesproken_stap = huidige_stap_idx

                        minuten = huidig_sec // 60
                        seconden = huidig_sec % 60
                        tijd_str = f"{minuten:02d}:{seconden:02d}"

                        with timer_container.container():
                            st.metric(label="⏱️ Totale Tijd", value=tijd_str)
                            st.progress(min(1.0, huidig_sec / totaal_tijd))
                            st.markdown(f"### 🎯 Stap: **{huidige_stap['titel']}**")
                            st.info(f"👉 **ACTIE NU:** {huidige_stap['actie']}")
                            st.success(f"⚖️ **Doelgewicht op de weegschaal:** **{huidige_stap['doel_water_g']} gram**")

                        time.sleep(1)

                    if st.session_state.get("timer_active", False):
                        st.balloons()
                        st.success("🎉 Zetsessie voltooid! Geniet van je koffie.")
                        st.session_state["timer_active"] = False

                # 4.2 Doorlooptijd & Auto-Tuner
                st.markdown("---")
                st.subheader("⏱️ Doorlooptijd & Auto-Tuner")
                doel_min = totaal_tijd // 60
                doel_sec = totaal_tijd % 60
                st.info(f"🎯 **Doeltijd volgens recept:** `{doel_min:02d}:{doel_sec:02d}` ({totaal_tijd} seconden)")

                col_m, col_s = st.columns(2)
                with col_m:
                    actueel_min = st.number_input("Daadwerkelijke minuten:", 0, 120, doel_min)
                with col_s:
                    actueel_sec = st.number_input("Daadwerkelijke seconden:", 0, 59, doel_sec)

                daadwerkelijk_totaal = (actueel_min * 60) + actueel_sec
                verschil = daadwerkelijk_totaal - totaal_tijd

                rating = st.slider("Beoordeel dit kopje (1-5 sterren):", 1, 5, 5)
                smaak_feedback = st.radio(
                    "Hoe was de smaakbalans?",
                    [
                        "✨ Perfect gebalanceerd & heerlijk zoet",
                        "🍋 Te zuur / Flauw (Onder-extractie)",
                        "🍫 Te bitter / Droog (Over-extractie)",
                    ],
                )

                if st.button("💾 Opslaan & Recept Aanpassen"):
                    save_data(
                        LOG_FILE,
                        brew_history + [{
                            "datum": str(date.today()),
                            "roaster": roaster,
                            "coffee_name": coffee_name,
                            "target_sec": totaal_tijd,
                            "actual_sec": daadwerkelijk_totaal,
                            "rating": rating,
                        }],
                    )
                    st.success("Zetsessie opgeslagen in de historie!")

                    if abs(verschil) <= 10 and "Perfect" in smaak_feedback:
                        st.success("🎯 **Goudschot!** Behoud deze instellingen voor de volgende keer.")
                    elif verschil > 10 or "Te bitter" in smaak_feedback:
                        st.warning("🐢 **Te tragere doorloop of over-extractie:** Maal **0.2-0.4 GROVER** op Ode Gen 2 of **1-2 kliks GROVER** op Comandante C40.")
                    else:
                        st.warning("🐇 **Te snelle doorloop of onder-extractie:** Maal **0.2-0.4 FIJNER** op Ode Gen 2 of **1-2 kliks FIJNER** op Comandante C40.")

        except Exception as e:
            st.error(f"Fout bij het verwerken van de gegevens: {e}")
            st.text(raw_text)

# ==========================================
# 5. ONDERHOUDSDASHBOARD MOLENS
# ==========================================
st.markdown("---")
st.subheader("🧹 Koffiemolen Onderhouds Dashboard")
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### ⚙️ Fellow Ode Gen 2")
    ode_count = maint_data.get("ode_brew_count", 0)
    st.write(f"Zetbeurten sinds Schoonmaak: **{ode_count}**")
    if ode_count >= 50:
        st.error("⚠️ **Onderhoud nodig!** Tijd om de maalschijven te reinigen.")
    else:
        st.success("✅ Molen in topconditie.")
    if st.button("Reset Ode Teller"):
        maint_data["ode_brew_count"] = 0
        save_data(MAINTENANCE_FILE, maint_data)
        st.rerun()

with col_b:
    st.markdown("### 🪵 Comandante C40")
    com_count = maint_data.get("comandante_brew_count", 0)
    st.write(f"Zetbeurten sinds Schoonmaak: **{com_count}**")
    if com_count >= 50:
        st.error("⚠️ **Onderhoud nodig!** Tijd om het binnenwerk schoon te borstelen.")
    else:
        st.success("✅ Molen in topconditie.")
    if st.button("Reset Comandante Teller"):
        maint_data["comandante_brew_count"] = 0
        save_data(MAINTENANCE_FILE, maint_data)
        st.rerun()