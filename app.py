import streamlit as st
import time
import json
import os

# ==========================================
# 1. STREAMLIT PAGINA CONFIGURATIE & DATABASE
# ==========================================
st.set_page_config(
    page_title="BrewPrint — Specialty Coffee Companion",
    page_icon="☕",
    layout="centered"
)

DB_FILE = "brew_data.json"

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {
        "grinder": "Comandante C40 Tigershark",
        "last_feedback": None,
        "advice": "Welkom! Brouw je eerste kopje om persoonlijk advies te krijgen."
    }

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

if "data" not in st.session_state:
    st.session_state.data = load_data()

# ==========================================
# 2. CUSTOM CSS & BRANDING
# ==========================================
st.markdown("""
    <style>
    .stApp {
        background-color: #FBF8F5;
        color: #2B1E1A;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    .brand-header {
        text-align: center;
        padding: 5px 0 15px 0;
    }
    .brand-title {
        font-family: 'Georgia', serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: #2B1E1A;
        margin-top: 5px;
        margin-bottom: 0px;
        letter-spacing: -1px;
    }
    .brand-title span {
        color: #C06C4C;
        font-weight: 400;
    }
    .brand-tagline {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #8C7A6B;
        margin-top: 2px;
    }
    .splash-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 60vh;
        text-align: center;
    }
    .splash-title {
        font-family: 'Georgia', serif;
        font-size: 3.5rem;
        font-weight: 700;
        color: #2B1E1A;
        margin-top: 15px;
        margin-bottom: 0px;
    }
    .splash-title span {
        color: #C06C4C;
        font-weight: 400;
    }
    .splash-tagline {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 3px;
        color: #8C7A6B;
        margin-top: 10px;
    }
    h1, h2, h3 {
        color: #2B1E1A !important;
        font-family: 'Georgia', serif !important;
        font-weight: 600 !important;
    }
    div.stButton > button {
        background-color: #C06C4C !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #A05235 !important;
        box-shadow: 0 4px 12px rgba(192, 108, 76, 0.2) !important;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Georgia', serif !important;
        color: #C06C4C !important;
        font-size: 2.5rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SESSION STATE INITIALISATIE
# ==========================================
if "splash_done" not in st.session_state:
    st.session_state.splash_done = False
if "page" not in st.session_state:
    st.session_state.page = "home"
if "brew_ratio" not in st.session_state:
    st.session_state.brew_ratio = 16.6
if "brewing" not in st.session_state:
    st.session_state.brewing = False

# ==========================================
# 4. SPLASH SCREEN (4 SECONDEN)
# ==========================================
if not st.session_state.splash_done:
    splash_placeholder = st.empty()
    with splash_placeholder.container():
        st.markdown("""
            <div class="splash-container">
                <svg width="110" height="110" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M50 4 C24 4 6 24 6 50 C6 76 24 96 50 96 C76 96 94 76 94 50 C94 24 76 4 50 4 Z" stroke="#C06C4C" stroke-width="3" fill="#FFFFFF"/>
                    <path d="M50 10 C42 35 58 65 50 90" stroke="#2B1E1A" stroke-width="3.5" stroke-linecap="round"/>
                    <path d="M43 20 C28 24 18 38 22 55 C24 65 32 75 44 82" stroke="#C06C4C" stroke-width="2.2" stroke-linecap="round"/>
                    <path d="M57 20 C72 24 82 38 78 55 C76 65 68 75 56 82" stroke="#C06C4C" stroke-width="2.2" stroke-linecap="round"/>
                </svg>
                <div class="splash-title">Brew<span>Print</span></div>
                <div class="splash-tagline">Your Unique Coffee Identity</div>
            </div>
        """, unsafe_allow_html=True)
    time.sleep(4)
    splash_placeholder.empty()
    st.session_state.splash_done = True
    st.rerun()

# ==========================================
# 5. SIDEBAR INSTELLINGEN (MOLEN)
# ==========================================
with st.sidebar:
    st.header("⚙️ App Instellingen")
    current_grinder = st.selectbox(
        "Selecteer je molen:", 
        ["Comandante C40 Tigershark", "Fellow Ode Gen 2", "Baratza Encore"], 
        index=["Comandante C40 Tigershark", "Fellow Ode Gen 2", "Baratza Encore"].index(st.session_state.data["grinder"])
    )
    if st.button("Molen Opslaan"):
        st.session_state.data["grinder"] = current_grinder
        save_data(st.session_state.data)
        st.success("Molen bijgewerkt!")

# ==========================================
# 6. RECEPTEN DATABASE (MET SVG AFBEELDINGEN)
# ==========================================
RECIPES = {
    "V60 Single Cup (Lichte Branding)": {
        "method": "Hario V60",
        "svg_icon": """
            <svg width="120" height="120" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 25 L80 25 L62 75 C60 80 55 82 50 82 C45 82 40 80 38 75 Z" stroke="#C06C4C" stroke-width="3" fill="#FFF8F5"/>
                <line x1="20" y1="25" x2="80" y2="25" stroke="#2B1E1A" stroke-width="3" stroke-linecap="round"/>
                <path d="M32 25 L43 75" stroke="#2B1E1A" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
                <path d="M50 25 L50 78" stroke="#2B1E1A" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
                <path d="M68 25 L57 75" stroke="#2B1E1A" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
                <path d="M35 85 L65 85 C68 85 70 88 68 92 C65 96 35 96 32 92 C30 88 32 85 35 85 Z" stroke="#2B1E1A" stroke-width="2.5" fill="#FFFFFF"/>
            </svg>
        """,
        "coffee_g": 15.0,
        "water_g": 250,
        "temp_c": 93,
        "target_total_time": 165,
        "steps": [
            {"time_start": 0, "duration": 45, "target_water": 50, "title": "Bloom (Ontgassen)", "action": "Schenk 50g water & geef 1 zachte swirl"},
            {"time_start": 45, "duration": 30, "target_water": 150, "title": "Eerste Hoofd-Pour", "action": "Schenk spiraalvormig bij tot 150g"},
            {"time_start": 75, "duration": 30, "target_water": 250, "title": "Tweede Hoofd-Pour", "action": "Schenk in het midden tot 250g"},
            {"time_start": 105, "duration": 60, "target_water": 250, "title": "Drawdown & Finish", "action": "Laat volledig doordruppelen"}
        ]
    }
}

# ==========================================
# 7. HOOFDSCHERM
# ==========================================
if st.session_state.page == "home":
    st.markdown("""
        <div class="brand-header">
            <div class="brand-title">Brew<span>Print</span></div>
            <div class="brand-tagline">Your Unique Coffee Identity</div>
        </div>
    """, unsafe_allow_html=True)

    # Intelligent Adviesvak op basis van vorige feedback
    if st.session_state.data.get("advice"):
        st.info(f"💡 **AI Barista Advies:** {st.session_state.data['advice']}")

    st.subheader("📸 Scan je boon")
    uploaded_file = st.camera_input("Maak een foto van het etiket")
    if uploaded_file:
        st.info("AI-Vision scant etiket... Recept herkend: V60 Light Roast!")

    st.divider()

    st.subheader("☕ Kies je zetmethode & Dosering")
    coffee_amount = st.slider("Hoeveelheid koffie (gram):", 10, 30, 15)
    water_amount = int(coffee_amount * st.session_state.brew_ratio)
    st.write(f"**Totaal water nodig:** {water_amount} gram *(Ratio 1:16.6)*")

    st.markdown("<br>", unsafe_allow_html=True)

    for recipe_name, data in RECIPES.items():
        col_img, col_btn = st.columns([1, 2], vertical_alignment="center")
        with col_img:
            st.markdown(f"<div style='text-align: center;'>{data['svg_icon']}</div>", unsafe_allow_html=True)
        with col_btn:
            if st.button(f"Zet {recipe_name}", key=f"btn_{recipe_name}"):
                st.session_state.selected_recipe = recipe_name
                st.session_state.coffee_amount = coffee_amount
                st.session_state.water_amount = water_amount
                st.session_state.page = "brew_screen"
                st.rerun()
        st.markdown("<hr style='margin: 15px 0; border-color: #EAE1D9;'>", unsafe_allow_html=True)

# ==========================================
# 8. BROUW- EN EVALUATIESCHERM MET SLIMME FEEDBACK
# ==========================================
elif st.session_state.page == "brew_screen":
    recipe = RECIPES[st.session_state.selected_recipe]
    
    if st.button("⬅️ Terug naar overzicht"):
        st.session_state.brewing = False
        st.session_state.page = "home"
        st.rerun()

    st.divider()
    st.subheader(f"📖 Brouwen met {st.session_state.data['grinder']}")
    st.write(f"**Koffie:** {st.session_state.coffee_amount}g | **Water:** {st.session_state.water_amount}g")

    tab_timer, tab_eval = st.tabs(["⏱️ Live Timer & Stappen", "📊 Smaak-Feedback & Analyse"])

    with tab_timer:
        for step in recipe["steps"]:
            with st.expander(f"**{step['title']}** (Tot {int(step['target_water'] * (st.session_state.coffee_amount/15))}g)", expanded=True):
                st.write(f"👉 {step['action']}")

        col_start, col_stop = st.columns(2)
        with col_start:
            if st.button("▶️ Start Brew"):
                st.session_state.brewing = True
        with col_stop:
            if st.button("⏹️ Stop Brew"):
                st.session_state.brewing = False

        if st.session_state.brewing:
            total_time = recipe["target_total_time"]
            timer_ph = st.empty()
            prog_bar = st.progress(0)
            start_ts = time.time()

            while st.session_state.brewing:
                elapsed = int(time.time() - start_ts)
                mins, secs = divmod(elapsed, 60)
                
                with timer_ph.container():
                    st.metric(label="Brouwtijd", value=f"{mins:02d}:{secs:02d}")
                
                prog_bar.progress(min(elapsed / total_time, 1.0))
                time.sleep(1)
                if elapsed >= total_time:
                    st.session_state.brewing = False
                    st.rerun()

    with tab_eval:
        st.subheader("🔍 Hoe smaakte je koffie?")
        st.write("Kies hieronder het belangrijkste smaakkenmerk om je recept direct intelligent bij te stellen:")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🍋 Te zuur (Onderextractie)"):
                st.session_state.data["advice"] = f"Vorige kop was te zuur. Advies voor {st.session_state.data['grinder']}: Stel de molen **1-2 kliks fijner** in of verhoog de watertemperatuur."
                save_data(st.session_state.data)
                st.success("Feedback opgeslagen! Je vindt het nieuwe advies op het hoofdscherm.")

            if st.button("🌾 Droog / Samentrekkend (Astringent)"):
                st.session_state.data["advice"] = f"Vorige kop was te droog in de mond. Advies: Veel koffiestof (fines). Stel de molen **grover** in."
                save_data(st.session_state.data)
                st.success("Feedback opgeslagen!")

        with col2:
            if st.button("☕ Te bitter (Overextractie)"):
                st.session_state.data["advice"] = f"Vorige kop was te bitter. Advies voor {st.session_state.data['grinder']}: Stel de molen **1-2 kliks grover** in."
                save_data(st.session_state.data)
                st.success("Feedback opgeslagen! Je vindt het nieuwe advies op het hoofdscherm.")

            if st.button("💧 Te waterig / Dun"):
                st.session_state.data["advice"] = "Vorige kop miste body. Advies: Verhoog de koffiedosering met 1 gram of giet langzamer."
                save_data(st.session_state.data)
                st.success("Feedback opgeslagen!")