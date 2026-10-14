"""
═══════════════════════════════════════════════════════════════════════════════
FORCASTA — Application Streamlit de Prévision des Ventes
Station Technique Haute Précision : Thèmes Sombre/Clair, Bilingue (FR/EN)
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import io
import json
import sqlite3
import datetime
import numpy as np
import pandas as pd
import streamlit as st
import base64
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────────────────────────────────────────────────────────
# IMPORT DES MODULES MÉTIER DU PROJET
# ─────────────────────────────────────────────────────────────────────────────
from database.db_manager import (
    init_db,
    verify_user,
    create_user,
    get_user_by_id,
    get_all_users,
    update_user_role,
    update_user_password,
    delete_user,
    create_project,
    get_user_projects,
    get_project_by_id,
    get_all_projects_admin,
    delete_project,
    get_db_stats,
    vacuum_database,
    DB_PATH
)
from modules.data_cleaner import load_data, clean_data
from modules.feature_engineering import engineer_all_features
from modules.models import evaluate_all_models, infer_freq
from modules.simulation import refit_and_forecast
from modules.recommendations import generate_recommendations
import importlib
import utils.i18n_helper
importlib.reload(utils.i18n_helper)
from utils.i18n_helper import t

# Initialisation de la BDD et des répertoires
init_db()
os.makedirs("data_storage", exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# GESTION DES PRÉFÉRENCES (LANGUE & THÈME)
# ─────────────────────────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state["lang"] = "fr"  # "fr" ou "en"
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"  # "dark" ou "light"
if "user" not in st.session_state:
    st.session_state["user"] = None
if "active_project_id" not in st.session_state:
    st.session_state["active_project_id"] = None
if "module_index" not in st.session_state:
    st.session_state["module_index"] = 0
if "view_mode" not in st.session_state:
    st.session_state["view_mode"] = "modules"

lang = st.session_state["lang"]
is_dark = st.session_state["theme"] == "dark"

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION DE LA PAGE STREAMLIT
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FORCASTA - Sales Forecasting & Time Series Intelligence",
    page_icon="logo_forcasta_thumb.png" if os.path.exists("logo_forcasta_thumb.png") else "📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Gestion de la navigation via le logo cliquable
if st.query_params.get("nav") == "home":
    st.session_state["view_mode"] = "home"
    try:
        del st.query_params["nav"]
    except Exception:
        pass

@st.cache_data
def get_logo_b64():
    """Charge le logo en base64 pour permettre un lien cliquable natif."""
    for p in ["logo_forcasta_thumb.png", "logo_forcasta.jpg"]:
        if os.path.exists(p):
            try:
                with open(p, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
            except Exception:
                pass
    return ""

# ─────────────────────────────────────────────────────────────────────────────
# MOTEUR DE STYLES DYNAMIQUES (DARK GRAPHITE & LIGHT SLATE)
# ─────────────────────────────────────────────────────────────────────────────
if is_dark:
    # Palette Authentique Sky Mint & Graphite
    THEME_CSS = """
    :root {
        --bg-app: #1A1C20;
        --bg-surface: #202227;
        --bg-card: #25272C;
        --bg-card-hover: #2E3137;
        --border-subtle: #31353D;
        --border-active: #B8F7E4;
        --text-pure: #FFFFFF;
        --text-main: #F1F5F9;
        --text-secondary: #94A3B8;
        --input-bg: #15171A;
        --input-border: #3A3F49;
        --mint-primary: #B8F7E4;
        --mint-deep: #0D9488;
        --mint-glow: rgba(184, 247, 228, 0.4);
        --btn-text: #0A1E18;
    }
    """
    PLOTLY_BG = "#1A1C20"
    PLOTLY_PLOT_BG = "#202227"
    PLOTLY_TEXT = "#F1F5F9"
    PLOTLY_GRID = "#31353D"
else:
    # Palette Mode Clair (Light Slate & Sky Mint Deep WCAG AAA)
    THEME_CSS = """
    :root {
        --bg-app: #F4F6F9;
        --bg-surface: #FFFFFF;
        --bg-card: #FFFFFF;
        --bg-card-hover: #F8FAFC;
        --border-subtle: #E2E8F0;
        --border-active: #0D9488;
        --text-pure: #0F172A;
        --text-main: #1E293B;
        --text-secondary: #64748B;
        --input-bg: #FFFFFF;
        --input-border: #CBD5E1;
        --mint-primary: #0D9488;
        --mint-deep: #0F766E;
        --mint-glow: rgba(13, 148, 136, 0.25);
        --btn-text: #064E3B;
    }
    """
    PLOTLY_BG = "#F4F6F9"
    PLOTLY_PLOT_BG = "#FFFFFF"
    PLOTLY_TEXT = "#1E293B"
    PLOTLY_GRID = "#E2E8F0"

st.markdown(f"<style>{THEME_CSS}</style>", unsafe_allow_html=True)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Arrière-plan global */
    .stApp {
        background-color: var(--bg-app);
        color: var(--text-main);
    }

    /* Typographie technique et en-têtes */
    .brand-title {
        font-size: 1.95rem;
        font-weight: 800;
        color: var(--mint-primary);
        letter-spacing: -0.5px;
        margin-bottom: 0.1rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .brand-subtitle {
        color: var(--text-secondary);
        font-size: 0.88rem;
        font-weight: 500;
        margin-bottom: 1.2rem;
    }

    /* Cartes Techniques */
    .forcasta-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 10px;
        padding: 1.15rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
    }
    .forcasta-card:hover {
        border-color: var(--border-active);
    }

    /* Bandeau Héro de Module */
    .module-hero-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-left: 4.5px solid var(--mint-primary);
        border-radius: 10px;
        padding: 1.1rem 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
    }

    /* Badges & Pills */
    .badge-pill-mint {
        background: rgba(184, 247, 228, 0.15);
        color: var(--mint-primary);
        border: 1px solid rgba(184, 247, 228, 0.4);
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        display: inline-block;
    }
    .badge-champion {
        background: linear-gradient(135deg, #B8F7E4 0%, #87E7CA 100%);
        color: #0A1E18;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.3px;
        display: inline-block;
    }
    .badge-admin {
        background: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.4);
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        display: inline-block;
    }

    /* Boutons Primaires Sky Mint */
    button[data-testid="baseButton-primary"],
    button[data-testid="stBaseButton-primary"],
    div.stButton > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #B8F7E4 0%, #87E7CA 100%) !important;
        color: #0A1E18 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 7px !important;
        box-shadow: 0 2px 8px rgba(184, 247, 228, 0.25) !important;
        transition: all 0.2s ease !important;
    }
    button[data-testid="baseButton-primary"]:hover,
    button[data-testid="stBaseButton-primary"]:hover,
    div.stButton > button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        background: linear-gradient(135deg, #CEFBEF 0%, #9DF2DA 100%) !important;
        box-shadow: 0 4px 16px rgba(184, 247, 228, 0.45) !important;
        transform: translateY(-1px);
        color: #0A1E18 !important;
    }

    /* Boutons Secondaires */
    button[data-testid="baseButton-secondary"],
    button[data-testid="stBaseButton-secondary"],
    div.stButton > button {
        background-color: var(--bg-card) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 7px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    button[data-testid="baseButton-secondary"]:hover,
    button[data-testid="stBaseButton-secondary"]:hover,
    div.stButton > button:hover {
        border-color: var(--border-active) !important;
        color: var(--mint-primary) !important;
    }

    /* Champs de saisie */
    .stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] {
        background-color: var(--input-bg) !important;
        border: 1px solid var(--input-border) !important;
        color: var(--text-main) !important;
        border-radius: 7px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--border-active) !important;
        box-shadow: 0 0 0 1px var(--border-active) !important;
    }

    /* Volet Latéral (Sidebar) Non Scrollable & Ultra Épuré */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-surface) !important;
        border-right: 1px solid var(--border-subtle) !important;
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
    }
    section[data-testid="stSidebar"]::-webkit-scrollbar {
        display: none !important;
        width: 0 !important;
        height: 0 !important;
    }
    section[data-testid="stSidebar"] > div:first-child,
    section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] {
        padding: 0.75rem 0.8rem !important;
        scrollbar-width: none !important;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
        gap: 2px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] label {
        padding: 3px 6px !important;
        font-size: 0.81rem !important;
        border-radius: 6px !important;
        margin: 0 !important;
        cursor: pointer !important;
    }
    section[data-testid="stSidebar"] hr {
        margin: 0.35rem 0 !important;
    }

    /* Onglets techniques */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: var(--bg-surface);
        padding: 5px;
        border-radius: 8px;
        border: 1px solid var(--border-subtle);
    }
    .stTabs [data-baseweb="tab"] {
        padding: 6px 14px;
        border-radius: 6px;
        color: var(--text-secondary);
        font-weight: 600;
        font-size: 0.88rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--bg-card) !important;
        color: var(--mint-primary) !important;
        border-bottom: 2px solid var(--mint-primary) !important;
    }

    /* Métriques avec typographie numérique */
    [data-testid="stMetricValue"] {
        color: var(--mint-primary) !important;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    paper_bgcolor=PLOTLY_BG,
    plot_bgcolor=PLOTLY_PLOT_BG,
    font=dict(family="Plus Jakarta Sans, sans-serif", color=PLOTLY_TEXT),
    xaxis=dict(gridcolor=PLOTLY_GRID, zerolinecolor=PLOTLY_GRID),
    yaxis=dict(gridcolor=PLOTLY_GRID, zerolinecolor=PLOTLY_GRID),
    hoverlabel=dict(bgcolor=PLOTLY_PLOT_BG, font_color=PLOTLY_TEXT, bordercolor="#B8F7E4")
)


# ─────────────────────────────────────────────────────────────────────────────
# UTILITAIRES DE STOCKAGE DE PROJET
# ─────────────────────────────────────────────────────────────────────────────
def get_project_file(project_id: int, suffix: str) -> str:
    return f"data_storage/project_{project_id}_{suffix}.csv"

def get_project_meta_path(project_id: int) -> str:
    return f"data_storage/project_{project_id}_meta.json"

def read_project_meta(project_id: int) -> dict:
    meta_path = get_project_meta_path(project_id)
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_project_meta(project_id: int, data: dict):
    meta_path = get_project_meta_path(project_id)
    existing = read_project_meta(project_id)
    existing.update(data)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

def logout():
    st.session_state["user"] = None
    st.session_state["active_project_id"] = None
    st.session_state["module_index"] = 0
    st.session_state["view_mode"] = "modules"
    st.rerun()

def go_to_module(idx: int):
    st.session_state["view_mode"] = "modules"
    st.session_state["module_index"] = max(0, min(idx, 6))
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# LISTE DES 7 MODULES DU WORKFLOW
# ─────────────────────────────────────────────────────────────────────────────
MODULE_KEYS = ["m1", "m2", "m3", "m4", "m5", "m6", "m7"]
MODULE_ICONS = ["📥", "⚙️", "📈", "🤖", "🔮", "💡", "📤"]


# ═════════════════════════════════════════════════════════════════════════════
# 1. ÉCRAN D'AUTHENTIFICATION (LOGIN / REGISTER)
# ═════════════════════════════════════════════════════════════════════════════
if st.session_state["user"] is None:
    # Barre supérieure compacte de sélection Langue / Thème
    top_col1, top_col2 = st.columns([3, 1])
    with top_col2:
        c_th, c_ln = st.columns(2)
        with c_th:
            if st.button("🌙" if is_dark else "☀️", help=t("theme_dark" if is_dark else "theme_light", lang), use_container_width=True):
                st.session_state["theme"] = "light" if is_dark else "dark"
                st.rerun()
        with c_ln:
            if st.button("🇬🇧 EN" if lang == "fr" else "🇫🇷 FR", use_container_width=True):
                st.session_state["lang"] = "en" if lang == "fr" else "fr"
                st.rerun()

    col_l, col_center, col_r = st.columns([1, 1.8, 1])
    with col_center:
        st.markdown("<div style='text-align:center; padding-top: 1.5rem;'>", unsafe_allow_html=True)
        if os.path.exists("logo_forcasta_thumb.png"):
            st.image("logo_forcasta_thumb.png", width=90)
        st.markdown(f"<div class='brand-title' style='justify-content:center;'>{t('app_name', lang)}</div>", unsafe_allow_html=True)
        st.markdown(f"<p class='brand-subtitle'>{t('app_subtitle', lang)}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["🔐 Connexion / Sign In", "📝 Inscription / Register"])

        with tab_login:
            with st.form("form_login"):
                username = st.text_input("Identifiant / Username", placeholder="Votre nom d'utilisateur")
                password = st.text_input("Mot de passe / Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Se connecter / Sign In", use_container_width=True, type="primary")

                if submitted:
                    if not username or not password:
                        st.error("Veuillez renseigner tous les champs requis." if lang == "fr" else "Please fill in all required fields.")
                    else:
                        user = verify_user(username.strip(), password)
                        if user:
                            st.session_state["user"] = user
                            st.rerun()
                        else:
                            st.error("Identifiants incorrects." if lang == "fr" else "Invalid credentials.")

            # Coordonnées démo utilisateur uniquement
            st.markdown(f"""
            <div class='forcasta-card' style='text-align: center; padding: 10px; margin-top: 12px;'>
                <span style='color: var(--text-secondary); font-size: 0.82rem;'>🔑 Compte utilisateur de test / Demo user account :</span><br>
                <span style='font-size: 0.9rem; font-weight: 600;'>
                    Identifiant : <code style='color: var(--mint-primary);'>user</code> &nbsp;|&nbsp; 
                    Mot de passe : <code style='color: var(--mint-primary);'>user123</code>
                </span>
            </div>
            """, unsafe_allow_html=True)

        with tab_register:
            with st.form("form_register"):
                new_username = st.text_input("Nom d'utilisateur souhaité")
                new_password = st.text_input("Mot de passe", type="password")
                new_confirm = st.text_input("Confirmation du mot de passe", type="password")
                reg_submitted = st.form_submit_button("Créer le compte", use_container_width=True)

                if reg_submitted:
                    if not new_username or not new_password:
                        st.error("Tous les champs sont requis." if lang == "fr" else "All fields are required.")
                    elif new_password != new_confirm:
                        st.error("Les mots de passe ne correspondent pas." if lang == "fr" else "Passwords do not match.")
                    elif len(new_password) < 4:
                        st.error("Le mot de passe doit comporter au moins 4 caractères." if lang == "fr" else "Password must be at least 4 characters.")
                    else:
                        uid = create_user(new_username.strip(), new_password, role="user")
                        if uid:
                            st.success("Compte créé avec succès ! Connectez-vous via l'onglet Connexion." if lang == "fr" else "Account created! Sign in now.")
                        else:
                            st.error("Ce nom d'utilisateur est déjà utilisé." if lang == "fr" else "Username already taken.")
    st.stop()


# ═════════════════════════════════════════════════════════════════════════════
# 2. VOLET LATÉRAL (SIDEBAR) & CONTRÔLES GLOBAUX
# ═════════════════════════════════════════════════════════════════════════════
user = st.session_state.get("user")
if not user:
    st.stop()
is_admin = bool(user.get("role") == "admin")

with st.sidebar:
    # ─────────────────────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    # 1. LOGO UNIQUE RÉTRÉCI (CLIQUABLE VERS ACCUEIL)
    # ─────────────────────────────────────────────────────────────────────────
    logo_b64 = get_logo_b64()
    if logo_b64:
        st.markdown(f"""
        <div style='text-align: center; margin-top: -0.6rem; margin-bottom: 0.35rem;'>
            <a href='?nav=home' target='_self' title="Retour à l'accueil / Home" style='text-decoration: none; display: inline-block;'>
                <img src='data:image/png;base64,{logo_b64}' style='width: 76px; max-width: 45%; border-radius: 9px; transition: transform 0.2s ease, box-shadow 0.2s ease; cursor: pointer; box-shadow: 0 3px 10px rgba(0,0,0,0.22);' onmouseover="this.style.transform='scale(1.06)';" onmouseout="this.style.transform='scale(1)';" />
            </a>
        </div>
        """, unsafe_allow_html=True)
    elif os.path.exists("logo_forcasta_thumb.png"):
        st.image("logo_forcasta_thumb.png", width=76)

    # Bouton Accueil / Home Dédié
    is_home = (st.session_state.get("view_mode") == "home")
    lbl_home = "Accueil" if lang == "fr" else "Home"
    if st.button(
        f"🏠 {lbl_home}",
        key="btn_sidebar_home",
        use_container_width=True,
        type="primary" if is_home else "secondary",
        help="Tableau de bord & Mes projets"
    ):
        st.session_state["view_mode"] = "home"
        st.rerun()

    # Toggles compacts Thème & Langue
    c_th, c_ln = st.columns(2)
    with c_th:
        if st.button("🌙 Sombre" if is_dark else "☀️ Clair", key="sb_theme_btn", use_container_width=True):
            st.session_state["theme"] = "light" if is_dark else "dark"
            st.rerun()
    with c_ln:
        if st.button("🇬🇧 EN" if lang == "fr" else "🇫🇷 FR", key="sb_lang_btn", use_container_width=True):
            st.session_state["lang"] = "en" if lang == "fr" else "fr"
            st.rerun()

    st.markdown("<hr style='margin: 0.35rem 0; border: none; border-top: 1px solid var(--border-subtle);'>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # 2. MODULES
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown(f"<span style='font-weight:700; color:var(--text-secondary); font-size: 0.78rem; letter-spacing: 0.5px;'>MODULES WORKFLOW</span>", unsafe_allow_html=True)
    sidebar_choices = [f"{i+1}. {MODULE_ICONS[i]} {t(f'{k}_short', lang).split('. ')[1]}" for i, k in enumerate(MODULE_KEYS)]
    if is_admin:
        sidebar_choices.append("8. 🛡️ " + t("admin_console", lang))

    if st.session_state.get("view_mode") == "modules":
        current_radio_idx = st.session_state.get("module_index", 0)
    elif st.session_state.get("view_mode") == "admin":
        current_radio_idx = len(sidebar_choices) - 1
    else:
        current_radio_idx = None

    selected_choice = st.radio(
        "Navigation :",
        options=range(len(sidebar_choices)),
        format_func=lambda x: sidebar_choices[x],
        index=current_radio_idx,
        label_visibility="collapsed"
    )

    if selected_choice is not None and selected_choice != current_radio_idx:
        if is_admin and selected_choice == len(sidebar_choices) - 1:
            st.session_state["view_mode"] = "admin"
        else:
            st.session_state["view_mode"] = "modules"
            st.session_state["module_index"] = selected_choice
        st.rerun()

    st.markdown("<hr style='margin: 0.35rem 0; border: none; border-top: 1px solid var(--border-subtle);'>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # 3. INFO PROJET
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown(f"<span style='font-weight:700; color:var(--text-secondary); font-size: 0.78rem; letter-spacing: 0.5px;'>INFO PROJET</span>", unsafe_allow_html=True)
    projects = get_user_projects(user["id"])
    project_options = {p["id"]: f"#{p['id']} - {p['name']}" for p in projects}

    if not project_options:
        st.info("Aucun projet existant." if lang == "fr" else "No projects yet.")
        st.session_state["active_project_id"] = None
    else:
        if st.session_state["active_project_id"] not in project_options:
            st.session_state["active_project_id"] = list(project_options.keys())[0]

        selected_id = st.selectbox(
            "Sélectionner projet :",
            options=list(project_options.keys()),
            format_func=lambda x: project_options[x],
            index=list(project_options.keys()).index(st.session_state["active_project_id"]),
            label_visibility="collapsed"
        )
        if selected_id != st.session_state["active_project_id"]:
            st.session_state["active_project_id"] = selected_id
            st.rerun()

        # Suppression du projet sélectionné pour l'utilisateur
        lbl_del = "Supprimer ce projet" if lang == "fr" else "Delete Project"
        with st.expander(f"🗑️ {lbl_del}", expanded=False):
            st.caption(f"Supprimer définitivement le projet #{selected_id} ?" if lang == "fr" else f"Permanently delete project #{selected_id}?")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("❌ Non" if lang == "fr" else "❌ No", key=f"no_del_{selected_id}", use_container_width=True):
                    st.rerun()
            with col_d2:
                if st.button("🗑️ Oui" if lang == "fr" else "🗑️ Yes", key=f"yes_del_{selected_id}", type="primary", use_container_width=True):
                    delete_project(selected_id)
                    st.session_state["active_project_id"] = None
                    st.session_state["view_mode"] = "home"
                    st.success("Projet supprimé avec succès." if lang == "fr" else "Project deleted successfully.")
                    st.rerun()

    with st.expander(f"➕ {t('new_project', lang)}", expanded=False):
        with st.form("new_project_form_sb", clear_on_submit=True):
            p_name = st.text_input(t("project_name", lang), placeholder="Ex: Ventes 2026")
            p_desc = st.text_area(t("project_desc", lang), placeholder="Description...")
            btn_create = st.form_submit_button(t("btn_create_project", lang), use_container_width=True, type="primary")
            if btn_create:
                if p_name.strip():
                    new_id = create_project(user["id"], p_name.strip(), p_desc.strip())
                    st.session_state["active_project_id"] = new_id
                    st.session_state["module_index"] = 0
                    st.session_state["view_mode"] = "modules"
                    st.success("Projet créé !" if lang == "fr" else "Project created!")
                    st.rerun()

    st.markdown("<hr style='margin: 0.35rem 0; border: none; border-top: 1px solid var(--border-subtle);'>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # 4. DÉCONNEXION
    # ─────────────────────────────────────────────────────────────────────────
    role_label = t("user_role_admin", lang) if is_admin else t("user_role_user", lang)
    role_badge = f"<span class='badge-admin'>🛡️ {role_label}</span>" if is_admin else f"<span class='badge-pill-mint'>👤 {role_label}</span>"
    st.markdown(f"<div style='margin-bottom: 0.25rem; font-size: 0.85rem;'><strong>{user['username']}</strong> {role_badge}</div>", unsafe_allow_html=True)

    if st.button(f"🚪 {t('logout', lang)}", key="btn_logout_sb", use_container_width=True):
        logout()


def render_home_dashboard():
    """Renders the executive home dashboard and project management cockpit."""
    user = st.session_state["user"]
    lang = st.session_state.get("lang", "fr")
    is_admin = bool(user.get("role") == "admin")
    projects = get_user_projects(user["id"])
    active_pid = st.session_state.get("active_project_id")

    lbl_welcome = "Tableau de Bord & Accueil" if lang == "fr" else "Dashboard & Home"
    lbl_subtitle = "Gérez vos projets d'analyse de séries temporelles et suivez vos prévisions." if lang == "fr" else "Manage your time-series projects and track commercial forecasts."
    st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 0.6rem;'>
        <div>
            <div class='brand-title' style='margin-bottom: 3px;'>🏠 {lbl_welcome}</div>
            <p class='brand-subtitle'>{lbl_subtitle}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4 Métriques exécutives
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(label="Mes Projets" if lang == "fr" else "My Projects", value=len(projects))
    with k2:
        active_display = "Aucun" if not active_pid else f"#{active_pid}"
        if active_pid:
            p_obj = get_project_by_id(active_pid)
            if p_obj:
                active_display = p_obj['name'][:18]
        st.metric(label="Projet Actif" if lang == "fr" else "Active Project", value=active_display)
    with k3:
        if active_pid:
            p_meta = read_project_meta(active_pid)
            champ = p_meta.get("selected_model", p_meta.get("champion_model", "Auto"))
        else:
            champ = "N/A"
        st.metric(label="Modèle Champion" if lang == "fr" else "Champion Model", value=champ)
    with k4:
        st.metric(label="Statut Plateforme" if lang == "fr" else "System Status", value="Opérationnel" if lang == "fr" else "Operational")

    st.markdown("<hr style='margin: 1rem 0; border: none; border-top: 1px solid var(--border-subtle);'>", unsafe_allow_html=True)

    # Section Mes Projets
    lbl_my_projs = "Mes Projets d'Analyse" if lang == "fr" else "My Sales Projects"
    st.markdown(f"### 📁 {lbl_my_projs}")

    with st.expander(f"➕ {t('new_project', lang)}", expanded=len(projects) == 0):
        with st.form("form_create_project_home", clear_on_submit=True):
            c_np1, c_np2 = st.columns([1.5, 2])
            with c_np1:
                p_name_h = st.text_input(t("project_name", lang), placeholder="Ex: Ventes 2026")
            with c_np2:
                p_desc_h = st.text_input(t("project_desc", lang), placeholder="Objectifs et périmètre...")
            btn_h_create = st.form_submit_button(t("btn_create_project", lang), type="primary", use_container_width=True)
            if btn_h_create:
                if p_name_h.strip():
                    new_id = create_project(user["id"], p_name_h.strip(), p_desc_h.strip())
                    st.session_state["active_project_id"] = new_id
                    st.session_state["module_index"] = 0
                    st.session_state["view_mode"] = "modules"
                    st.success("Projet créé avec succès !" if lang == "fr" else "Project successfully created!")
                    st.rerun()

    if not projects:
        st.info("Vous n'avez pas encore de projet enregistré. Cliquez sur 'Nouveau Projet' ci-dessus pour lancer votre première analyse." if lang == "fr" else "No projects saved yet. Click 'New Project' above to start your first forecast.")
    else:
        for p in projects:
            pid = p["id"]
            p_meta = read_project_meta(pid)
            clean_path = get_project_file(pid, "clean")
            features_path = get_project_file(pid, "features")
            forecast_path = get_project_file(pid, "forecast")
            
            p_steps_done = [
                os.path.exists(clean_path),
                os.path.exists(features_path),
                os.path.exists(clean_path),
                p_meta.get("champion_model") is not None,
                os.path.exists(forecast_path),
                os.path.exists(forecast_path),
                os.path.exists(forecast_path)
            ]
            pct = int((sum(p_steps_done) / 7) * 100)
            is_current = (pid == active_pid)

            border_style = "border: 1.5px solid var(--mint-primary);" if is_current else "border: 1px solid var(--border-subtle);"
            
            with st.container():
                st.markdown(f"""
                <div class='forcasta-card' style='{border_style} margin-bottom: 0.5rem; padding: 14px;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;'>
                        <div>
                            <span style='font-size: 1.15rem; font-weight: 700; color: var(--text-pure);'>{p['name']}</span>
                            <span class='badge-pill-mint'>ID #{pid}</span>
                            {"<span class='badge-champion'>PROJET ACTIF</span>" if is_current else ""}
                            <div style='color: var(--text-secondary); font-size: 0.82rem; margin-top: 4px;'>
                                {p['description'] if p['description'] else ('Créé le ' + str(p['created_at']))}
                            </div>
                        </div>
                        <div style='text-align: right; min-width: 140px;'>
                            <span style='font-size: 0.82rem; color: var(--mint-primary); font-weight: 700;'>Pipeline : {pct}% ({sum(p_steps_done)}/7)</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col_c1, col_c2, col_c3 = st.columns([2, 1.2, 1.2])
                with col_c1:
                    st.progress(pct / 100.0)
                with col_c2:
                    lbl_open = "Ouvrir le projet" if lang == "fr" else "Open Project"
                    if st.button(f"📂 {lbl_open}", key=f"home_open_{pid}", use_container_width=True, type="primary" if is_current else "secondary"):
                        st.session_state["active_project_id"] = pid
                        st.session_state["view_mode"] = "modules"
                        st.rerun()
                with col_c3:
                    lbl_btn_del = "Supprimer" if lang == "fr" else "Delete"
                    with st.popover(f"🗑️ {lbl_btn_del}", use_container_width=True):
                        st.write(f"Supprimer définitivement **{p['name']}** ?" if lang == "fr" else f"Permanently delete **{p['name']}**?")
                        lbl_conf_del = "Confirmer la suppression" if lang == "fr" else "Confirm Deletion"
                        if st.button(lbl_conf_del, key=f"home_del_confirm_{pid}", type="primary", use_container_width=True):
                            delete_project(pid)
                            if st.session_state.get("active_project_id") == pid:
                                st.session_state["active_project_id"] = None
                            st.success("Projet supprimé avec succès." if lang == "fr" else "Project deleted successfully.")
                            st.rerun()

    # Guide Méthodologique 7 Étapes
    st.markdown("<hr style='margin: 1.5rem 0; border: none; border-top: 1px solid var(--border-subtle);'>", unsafe_allow_html=True)
    st.markdown("### 🗺️ " + ("Méthodologie du Pipeline FORCASTA" if lang == "fr" else "FORCASTA Pipeline Methodology"))
    cols_m = st.columns(4)
    modules_info = [
        ("📥 1. Ingestion", "Upload CSV/Excel, parsing des dates et détection automatique des ventes."),
        ("⚙️ 2. Features", "Extraction de variables temporelles, lags dynamiques et moyennes mobiles."),
        ("📈 3. Historique", "Décomposition en tendance séculaire et visualisations de saisonnalité."),
        ("🤖 4. Benchmark", "Tournoi AutoML (Prophet, ARIMA, XGBoost) et élection du Champion."),
        ("🔮 5. Simulation", "What-If Analysis, scénarios commerciaux (+/- %) et bandes de confiance."),
        ("💡 6. Conseils", "Recommandations stratégiques d'aide à la décision et stocks."),
        ("📤 7. Exports", "Téléchargement instantané des rapports complets en CSV et Excel .xlsx.")
    ]
    for idx, (title, desc) in enumerate(modules_info):
        c = cols_m[idx % 4]
        with c:
            st.markdown(f"""
            <div class='forcasta-card' style='height: 140px; margin-bottom: 10px;'>
                <div style='font-weight: 700; color: var(--mint-primary); margin-bottom: 6px;'>{title}</div>
                <div style='font-size: 0.78rem; color: var(--text-secondary); line-height: 1.35;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# 3. CONTRÔLE DU PROJET ACTIF
# ═════════════════════════════════════════════════════════════════════════════
if st.session_state.get("view_mode") == "admin" and is_admin:
    # Affichage de la console d'administration en fin de fichier
    pass
elif st.session_state.get("view_mode") == "home":
    render_home_dashboard()
else:
    active_pid = st.session_state.get("active_project_id")
    if not active_pid:
        st.info(t("no_project_selected", lang))
        lbl_h_back = "Accueil" if lang == "fr" else "Home"
        if st.button(f"🏠 {lbl_h_back}", type="primary", use_container_width=False):
            st.session_state["view_mode"] = "home"
            st.rerun()
        st.stop()

    active_project = get_project_by_id(active_pid)
    meta = read_project_meta(active_pid)

    raw_path = get_project_file(active_pid, "raw")
    clean_path = get_project_file(active_pid, "clean")
    features_path = get_project_file(active_pid, "features")
    forecast_path = get_project_file(active_pid, "forecast")

    # ─────────────────────────────────────────────────────────────────────────
    # VÉRIFICATION TECHNIQUE DE COMPLÉTION DU PIPELINE
    # ─────────────────────────────────────────────────────────────────────────
    step_done = [
        os.path.exists(clean_path),                     # M1
        os.path.exists(features_path),                  # M2
        os.path.exists(clean_path),                     # M3
        meta.get("champion_model") is not None,         # M4
        os.path.exists(forecast_path),                  # M5
        os.path.exists(forecast_path),                  # M6
        os.path.exists(forecast_path)                   # M7
    ]
    completed_count = sum(step_done)
    progress_pct = int((completed_count / len(MODULE_KEYS)) * 100)

    # ─────────────────────────────────────────────────────────────────────────
    # EN-TÊTE TECHNIQUE DE PROJET & PROGRESSION
    # ─────────────────────────────────────────────────────────────────────────
    c_pinfo, c_pbar = st.columns([2.2, 1.2])
    with c_pinfo:
        model_tag = meta.get("selected_model", meta.get("champion_model", "Auto"))
        freq_tag = meta.get("freq", "M")
        st.markdown(f"""
        <div style='display: flex; align-items: center; gap: 8px; flex-wrap: wrap;'>
            <span style='font-size: 1.45rem; font-weight: 800; color: var(--text-pure);'>{active_project['name']}</span>
            <span class='badge-pill-mint'>ID #{active_pid}</span>
            <span class='badge-pill-mint'>FREQ : {freq_tag}</span>
            <span class='badge-champion'>MODÈLE : {model_tag}</span>
        </div>
        """, unsafe_allow_html=True)
    with c_pbar:
        st.caption(f"{t('progress_label', lang)} : **{progress_pct}%** ({completed_count}/7)")
        st.progress(progress_pct / 100.0)

    # ─────────────────────────────────────────────────────────────────────────
    # STEPPER INTERACTIF EN 7 ÉTAPES
    # ─────────────────────────────────────────────────────────────────────────
    cols_steps = st.columns(len(MODULE_KEYS))
    for i, m_key in enumerate(MODULE_KEYS):
        with cols_steps[i]:
            is_active = (st.session_state["module_index"] == i)
            is_done = step_done[i]
            btn_label = f"{'✅' if is_done else MODULE_ICONS[i]} {t(f'{m_key}_short', lang)}"
            btn_type = "primary" if is_active else "secondary"
            if st.button(btn_label, key=f"step_{i}", type=btn_type, use_container_width=True):
                go_to_module(i)

    # ─────────────────────────────────────────────────────────────────────────
    # COMPOSANT DE NAVIGATION BAS DE MODULE
    # ─────────────────────────────────────────────────────────────────────────
    def render_nav_footer(idx: int):
        st.write("")
        st.divider()
        c_prev, c_ind, c_next = st.columns([2, 2, 2])
        with c_prev:
            if idx > 0:
                p_key = MODULE_KEYS[idx - 1]
                if st.button(f"{t('btn_prev', lang)} : {t(f'{p_key}_short', lang)}", key=f"foot_prev_{idx}", use_container_width=True):
                    go_to_module(idx - 1)
        with c_ind:
            st.markdown(
                f"<div style='text-align: center; padding-top: 6px;'>"
                f"<span class='badge-pill-mint'>{t('step_counter', lang, current=idx + 1, total=7)}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        with c_next:
            if idx < len(MODULE_KEYS) - 1:
                n_key = MODULE_KEYS[idx + 1]
                if st.button(f"{t(f'{n_key}_short', lang)} : {t('btn_next', lang)}", key=f"foot_next_{idx}", type="primary", use_container_width=True):
                    go_to_module(idx + 1)
            else:
                if st.button(f"{t('btn_restart', lang)}", key=f"foot_restart_{idx}", use_container_width=True):
                    go_to_module(0)

    # ─────────────────────────────────────────────────────────────────────────
    # BANDEAU CONTEXTUEL DU MODULE
    # ─────────────────────────────────────────────────────────────────────────
    cur_idx = st.session_state["module_index"]
    cur_key = MODULE_KEYS[cur_idx]
    st.markdown(f"""
    <div class='module-hero-card'>
        <div style='display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <span class='badge-pill-mint' style='margin-bottom: 4px;'>{t('step_counter', lang, current=cur_idx + 1, total=7)}</span>
                <h3 style='color:var(--mint-primary); margin:3px 0 4px 0; font-size:1.45rem; font-weight:800;'>
                    {MODULE_ICONS[cur_idx]} {t(f'{cur_key}_name', lang)}
                </h3>
                <p style='color:var(--text-secondary); margin:0; font-size:0.88rem;'>{t(f'{cur_key}_desc', lang)}</p>
            </div>
            <div style='text-align:right;'>
                <span style='font-size:0.8rem; color:var(--text-secondary);'>Statut :</span><br>
                {'<span class=\"badge-pill-mint\">✅ ' + t('status_ready', lang) + '</span>' if step_done[cur_idx] else '<span class=\"badge-admin\">⚡ ' + t('status_pending', lang) + '</span>'}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


    # ═════════════════════════════════════════════════════════════════════════
    # MODULE 1 : INGESTION & NETTOYAGE
    # ═════════════════════════════════════════════════════════════════════════
    if cur_idx == 0:
        tab_up, tab_dm = st.tabs([t("m1_tab_upload", lang), t("m1_tab_demo", lang)])

        with tab_up:
            up_file = st.file_uploader(t("m1_upload_prompt", lang), type=["csv", "xlsx"])
            if up_file is not None:
                try:
                    df_in = load_data(up_file, up_file.name)
                    df_in.to_csv(raw_path, index=False)
                    save_project_meta(active_pid, {"raw_filename": up_file.name, "is_demo": False})
                    st.success(f"Fichier '{up_file.name}' importé ({len(df_in)} lignes)." if lang == "fr" else f"File '{up_file.name}' imported ({len(df_in)} rows).")
                except Exception as e:
                    st.error(f"Erreur d'importation : {e}")

        with tab_dm:
            st.write("Série temporelle mensuelle de démonstration (36 mois de ventes réelles) :" if lang == "fr" else "36-month monthly sales demonstration time series:")
            if st.button(t("m1_btn_demo", lang), type="primary"):
                if os.path.exists("demo_data_monthly_sales.csv"):
                    demo_df = pd.read_csv("demo_data_monthly_sales.csv")
                    demo_df.to_csv(raw_path, index=False)
                    save_project_meta(active_pid, {"raw_filename": "demo_data_monthly_sales.csv", "is_demo": True})
                    st.success("Données de démonstration chargées !" if lang == "fr" else "Demo data loaded!")
                    st.rerun()

        st.divider()

        if os.path.exists(raw_path):
            raw_df = pd.read_csv(raw_path)
            st.subheader("🔍 Données Brutes Importées" if lang == "fr" else "🔍 Raw Imported Data")
            st.dataframe(raw_df.head(6), use_container_width=True)

            cols = list(raw_df.columns)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                def_d = cols.index("Date") if "Date" in cols else 0
                date_col = st.selectbox(t("m1_date_col", lang), cols, index=def_d)
            with col2:
                def_s = cols.index("Sales") if "Sales" in cols else (1 if len(cols) > 1 else 0)
                sales_col = st.selectbox(t("m1_sales_col", lang), cols, index=def_s)
            with col3:
                freq_map = {"M": "Mensuelle / Monthly (M)", "W": "Hebdomadaire / Weekly (W)", "D": "Journalière / Daily (D)"}
                freq_val = st.selectbox(t("m1_freq", lang), options=list(freq_map.keys()), format_func=lambda x: freq_map[x], index=0)
            with col4:
                handle_out = st.checkbox(t("m1_outliers", lang), value=True)

            if st.button(t("m1_btn_clean", lang), type="primary", use_container_width=True):
                with st.spinner("Standardisation et traitement de la série..."):
                    try:
                        clean_df = clean_data(raw_df, date_col=date_col, sales_col=sales_col, freq=freq_val, handle_outliers=handle_out)
                        clean_df.to_csv(clean_path, index=False)
                        save_project_meta(active_pid, {
                            "date_col": date_col,
                            "sales_col": sales_col,
                            "freq": freq_val,
                            "handle_outliers": handle_out
                        })
                        st.success(f"Nettoyage réussi : {len(clean_df)} observations standardisées." if lang == "fr" else f"Cleaning complete: {len(clean_df)} standardized points.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur de nettoyage : {e}")

        if os.path.exists(clean_path):
            clean_df = pd.read_csv(clean_path)
            clean_df["Date"] = pd.to_datetime(clean_df["Date"])
            st.write("")
            st.subheader("✅ Série Temporelle Nettoyée" if lang == "fr" else "✅ Cleaned Time Series")

            k1, k2, k3, k4 = st.columns(4)
            k1.metric(t("m1_kpi_obs", lang), len(clean_df))
            k2.metric(t("m1_kpi_start", lang), clean_df["Date"].min().strftime("%Y-%m-%d"))
            k3.metric(t("m1_kpi_end", lang), clean_df["Date"].max().strftime("%Y-%m-%d"))
            k4.metric(t("m1_kpi_freq", lang), meta.get("freq", "M"))

            fig = px.line(clean_df, x="Date", y="Sales", markers=True)
            fig.update_traces(line_color="#B8F7E4", marker=dict(color="#B8F7E4", size=5))
            fig.update_layout(**PLOTLY_LAYOUT, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)

        render_nav_footer(0)


    # ═════════════════════════════════════════════════════════════════════════
    # MODULE 2 : FEATURE ENGINEERING
    # ═════════════════════════════════════════════════════════════════════════
    elif cur_idx == 1:
        if not os.path.exists(clean_path):
            st.warning(t("require_m1", lang))
            if st.button(t("btn_prev", lang)):
                go_to_module(0)
            st.stop()

        clean_df = pd.read_csv(clean_path)
        col_l, col_r = st.columns(2)
        with col_l:
            lags_str = st.text_input(t("m2_lags", lang), value="1, 2, 3")
        with col_r:
            roll_str = st.text_input(t("m2_rolling", lang), value="3, 6")

        if st.button(t("m2_btn_calc", lang), type="primary", use_container_width=True):
            try:
                lags = [int(x.strip()) for x in lags_str.split(",") if x.strip().isdigit()]
                rolls = [int(x.strip()) for x in roll_str.split(",") if x.strip().isdigit()]
                feat_df = engineer_all_features(clean_df, date_col="Date", sales_col="Sales", lags=lags, rolling_windows=rolls)
                feat_df.to_csv(features_path, index=False)
                save_project_meta(active_pid, {"lags": lags, "rolling_windows": rolls, "feature_columns": list(feat_df.columns)})
                st.success(f"{len(feat_df.columns)} variables générées avec succès." if lang == "fr" else f"{len(feat_df.columns)} features generated.")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur de calcul : {e}")

        if os.path.exists(features_path):
            f_df = pd.read_csv(features_path)
            st.subheader("📋 Matrice des Variables Prédictives" if lang == "fr" else "📋 Predictive Feature Matrix")
            st.dataframe(f_df.head(10), use_container_width=True)
            st.caption(f"Colonnes ({len(f_df.columns)}) : {', '.join(f_df.columns)}")

        render_nav_footer(1)


    # ═════════════════════════════════════════════════════════════════════════
    # MODULE 3 : ANALYSE HISTORIQUE
    # ═════════════════════════════════════════════════════════════════════════
    elif cur_idx == 2:
        if not os.path.exists(clean_path):
            st.warning(t("require_m1", lang))
            if st.button(t("btn_prev", lang)):
                go_to_module(0)
            st.stop()

        df_h = pd.read_csv(clean_path)
        df_h["Date"] = pd.to_datetime(df_h["Date"])
        df_h = df_h.sort_values("Date")

        mean_v = df_h["Sales"].mean()
        std_v = df_h["Sales"].std()
        min_v = df_h["Sales"].min()
        max_v = df_h["Sales"].max()
        growth_v = ((df_h["Sales"].iloc[-1] - df_h["Sales"].iloc[0]) / df_h["Sales"].iloc[0] * 100) if df_h["Sales"].iloc[0] > 0 else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric(t("m3_kpi_avg", lang), f"{mean_v:,.1f}")
        c2.metric(t("m3_kpi_std", lang), f"{std_v:,.1f}")
        c3.metric(t("m3_kpi_min", lang), f"{min_v:,.1f}")
        c4.metric(t("m3_kpi_max", lang), f"{max_v:,.1f}")
        c5.metric(t("m3_kpi_growth", lang), f"{growth_v:+.1f}%")

        st.divider()

        tab_t, tab_s, tab_y = st.tabs([t("m3_tab_trend", lang), t("m3_tab_monthly", lang), t("m3_tab_yearly", lang)])

        with tab_t:
            df_h["MA_3"] = df_h["Sales"].rolling(3).mean()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_h["Date"], y=df_h["Sales"], mode="lines+markers", name="Ventes réelles" if lang == "fr" else "Actual Sales", line=dict(color="#B8F7E4", width=2.5)))
            fig.add_trace(go.Scatter(x=df_h["Date"], y=df_h["MA_3"], mode="lines", name="Moyenne Mobile (3)" if lang == "fr" else "Moving Average (3)", line=dict(color="#87E7CA", dash="dash", width=2)))
            fig.update_layout(**PLOTLY_LAYOUT, margin=dict(l=20, r=20, t=30, b=20), hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

        with tab_s:
            df_h["Month"] = df_h["Date"].dt.month
            monthly_avg = df_h.groupby("Month")["Sales"].mean().reset_index()
            fig_m = px.bar(monthly_avg, x="Month", y="Sales", color="Sales", color_continuous_scale=["#0D9488", "#87E7CA", "#B8F7E4"])
            fig_m.update_layout(**PLOTLY_LAYOUT, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_m, use_container_width=True)

        with tab_y:
            df_h["Year"] = df_h["Date"].dt.year
            yearly_sum = df_h.groupby("Year")["Sales"].sum().reset_index()
            fig_y = px.bar(yearly_sum, x="Year", y="Sales", color_discrete_sequence=["#0D9488"])
            fig_y.update_layout(**PLOTLY_LAYOUT, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_y, use_container_width=True)

        render_nav_footer(2)


    # ═════════════════════════════════════════════════════════════════════════
    # MODULE 4 : BENCHMARK & CHAMPION
    # ═════════════════════════════════════════════════════════════════════════
    elif cur_idx == 3:
        if not os.path.exists(clean_path):
            st.warning(t("require_m1", lang))
            if st.button(t("btn_prev", lang)):
                go_to_module(0)
            st.stop()

        clean_df = pd.read_csv(clean_path)

        if st.button(t("m4_btn_eval", lang), type="primary", use_container_width=True):
            with st.spinner("Évaluation comparative en cours..." if lang == "fr" else "Benchmarking 4 architectures..."):
                try:
                    results, champion = evaluate_all_models(clean_df)
                    serialized = {}
                    for mname, data in results.items():
                        m_mape = data["mape"]
                        serialized[mname] = {
                            "mape": round(m_mape, 2) if m_mape != float("inf") else 999.0,
                            "status": "Optimum" if m_mape < 15 else ("Acceptable" if m_mape < 30 else "Inadapté")
                        }
                    save_project_meta(active_pid, {
                        "benchmark_results": serialized,
                        "champion_model": champion,
                        "selected_model": champion
                    })
                    st.success(f"Benchmark terminé ! Modèle Champion : {champion}" if lang == "fr" else f"Benchmark complete! Champion: {champion}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur d'évaluation : {e}")

        meta = read_project_meta(active_pid)
        if "benchmark_results" in meta:
            bench = meta["benchmark_results"]
            champ = meta.get("champion_model", "Random Forest")
            sel_m = meta.get("selected_model", champ)

            st.subheader("🏆 Classement par Précision (MAPE)" if lang == "fr" else "🏆 Accuracy Ranking (MAPE)")

            records = []
            for name, d in bench.items():
                records.append({
                    t("m4_table_algo", lang): name,
                    t("m4_table_mape", lang): f"{d['mape']:.2f}%",
                    t("m4_table_qual", lang): d["status"],
                    t("m4_table_champ", lang): "👑 CHAMPION" if name == champ else ""
                })
            st.table(pd.DataFrame(records))

            model_names = list(bench.keys())
            mapes = [bench[m]["mape"] for m in model_names]
            colors = ["#B8F7E4" if m == champ else "#0D9488" for m in model_names]

            fig_b = go.Figure(go.Bar(x=model_names, y=mapes, marker_color=colors, text=[f"{v:.2f}%" for v in mapes], textposition="auto"))
            fig_b.update_layout(**PLOTLY_LAYOUT, yaxis_title="MAPE (%)", margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_b, use_container_width=True)

            st.divider()

            st.subheader(t("m4_selected_model", lang))
            new_sel = st.selectbox("Modèle actif :" if lang == "fr" else "Active Model:", options=model_names, index=model_names.index(sel_m) if sel_m in model_names else 0)
            if new_sel != sel_m:
                save_project_meta(active_pid, {"selected_model": new_sel})
                st.success(f"Modèle sélectionné : {new_sel}")
                st.rerun()

        render_nav_footer(3)


    # ═════════════════════════════════════════════════════════════════════════
    # MODULE 5 : SIMULATION PRÉDICTIVE
    # ═════════════════════════════════════════════════════════════════════════
    elif cur_idx == 4:
        if not os.path.exists(clean_path):
            st.warning(t("require_m1", lang))
            if st.button(t("btn_prev", lang)):
                go_to_module(0)
            st.stop()

        meta = read_project_meta(active_pid)
        sel_model = meta.get("selected_model", meta.get("champion_model", "Random Forest"))
        det_freq = meta.get("freq", "M")
        clean_df = pd.read_csv(clean_path)

        col_h, col_s = st.columns(2)
        with col_h:
            horizon = st.slider(t("m5_horizon", lang), min_value=3, max_value=36, value=meta.get("forecast_horizon", 12))
        with col_s:
            scenario_pct = st.slider(t("m5_scenario", lang), min_value=-50.0, max_value=50.0, value=float(meta.get("scenario_pct", 0.0)), step=1.0)

        if st.button(t("m5_btn_calc", lang), type="primary", use_container_width=True):
            with st.spinner("Calcul des prévisions et des intervalles..."):
                try:
                    fc_df = refit_and_forecast(sel_model, clean_df, horizon, freq=det_freq)
                    mult = 1.0 + (scenario_pct / 100.0)
                    fc_df["Scenario_Sales"] = np.round(fc_df["Baseline_Sales"] * mult, 2)
                    margin = 0.08 + (np.arange(len(fc_df)) * 0.005)
                    fc_df["Lower_Bound"] = np.round(np.clip(fc_df["Baseline_Sales"] * (1 - margin), a_min=0, a_max=None), 2)
                    fc_df["Upper_Bound"] = np.round(fc_df["Baseline_Sales"] * (1 + margin), 2)

                    fc_df.to_csv(forecast_path, index=False)
                    save_project_meta(active_pid, {"forecast_horizon": horizon, "scenario_pct": scenario_pct})
                    st.success("Prévisions calculées avec succès !" if lang == "fr" else "Forecast generated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur de simulation : {e}")

        if os.path.exists(forecast_path):
            fc_df = pd.read_csv(forecast_path)
            fc_df["Date"] = pd.to_datetime(fc_df["Date"])
            clean_df["Date"] = pd.to_datetime(clean_df["Date"])

            st.subheader(t("m5_chart_title", lang))

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=clean_df["Date"], y=clean_df["Sales"], name="Historique Réel" if lang == "fr" else "Historical Actuals", mode="lines+markers", line=dict(color="#94A3B8", width=2)))
            
            if "Upper_Bound" in fc_df.columns and "Lower_Bound" in fc_df.columns:
                fig.add_trace(go.Scatter(x=fc_df["Date"], y=fc_df["Upper_Bound"], mode="lines", line=dict(width=0), showlegend=False))
                fig.add_trace(go.Scatter(x=fc_df["Date"], y=fc_df["Lower_Bound"], mode="lines", line=dict(width=0), fill="tonexty", fillcolor="rgba(184, 247, 228, 0.15)", name="Intervalle de Confiance" if lang == "fr" else "Confidence Interval"))

            fig.add_trace(go.Scatter(x=fc_df["Date"], y=fc_df["Baseline_Sales"], name="Prévision Baseline" if lang == "fr" else "Baseline Forecast", mode="lines+markers", line=dict(color="#B8F7E4", width=3)))

            if "Scenario_Sales" in fc_df.columns and meta.get("scenario_pct", 0) != 0:
                fig.add_trace(go.Scatter(x=fc_df["Date"], y=fc_df["Scenario_Sales"], name=f"Scénario ({meta.get('scenario_pct'):+.0f}%)", mode="lines+markers", line=dict(color="#87E7CA", width=2.5, dash="dash")))

            fig.update_layout(**PLOTLY_LAYOUT, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 Tableau des Valeurs Prévisionnelles" if lang == "fr" else "📋 Projected Data Table")
            display_df = fc_df.copy()
            display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
            st.dataframe(display_df, use_container_width=True)

        render_nav_footer(4)


    # ═════════════════════════════════════════════════════════════════════════
    # MODULE 6 : CONSEILS STRATÉGIQUES
    # ═════════════════════════════════════════════════════════════════════════
    elif cur_idx == 5:
        if not os.path.exists(clean_path) or not os.path.exists(forecast_path):
            st.warning(t("require_m5", lang))
            if st.button(t("btn_prev", lang)):
                go_to_module(4)
            st.stop()

        clean_df = pd.read_csv(clean_path)
        fc_df = pd.read_csv(forecast_path)
        meta = read_project_meta(active_pid)

        model_name = meta.get("selected_model", "Champion")
        bench = meta.get("benchmark_results", {})
        mape_val = bench.get(model_name, {}).get("mape", 12.5)

        recos = generate_recommendations(clean_df, fc_df, mape_val, model_name)

        st.subheader(f"{t('m6_title', lang)} ({model_name})")

        for title, desc in recos:
            st.markdown(f"""
            <div class='forcasta-card'>
                <h4 style='color: var(--mint-primary); margin-bottom: 0.4rem;'>{title}</h4>
                <p style='color: var(--text-main); margin-bottom: 0;'>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

        render_nav_footer(5)


    # ═════════════════════════════════════════════════════════════════════════
    # MODULE 7 : EXPORTS & RAPPORTS
    # ═════════════════════════════════════════════════════════════════════════
    elif cur_idx == 6:
        if not os.path.exists(forecast_path):
            st.warning("⚠️ Aucune prévision n'a été générée." if lang == "fr" else "⚠️ No forecast projections available.")
            if st.button(t("btn_prev", lang)):
                go_to_module(4)
            st.stop()

        fc_df = pd.read_csv(forecast_path)
        clean_df = pd.read_csv(clean_path) if os.path.exists(clean_path) else pd.DataFrame()

        col_csv, col_xlsx = st.columns(2)

        with col_csv:
            st.subheader(t("m7_csv_title", lang))
            st.write(t("m7_csv_desc", lang))
            csv_data = fc_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=t("m7_btn_csv", lang),
                data=csv_data,
                file_name=f"{active_project['name']}_previsions.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )

        with col_xlsx:
            st.subheader(t("m7_xlsx_title", lang))
            st.write(t("m7_xlsx_desc", lang))
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                if not clean_df.empty:
                    clean_df.to_excel(writer, index=False, sheet_name="Historique_Nettoyé")
                fc_df.to_excel(writer, index=False, sheet_name="Prévisions_Futures")
            buffer.seek(0)
            st.download_button(
                label=t("m7_btn_xlsx", lang),
                data=buffer,
                file_name=f"{active_project['name']}_Rapport_Global.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )

        render_nav_footer(6)


# ═════════════════════════════════════════════════════════════════════════════
# 4. CONSOLE ADMINISTRATEUR
# ═════════════════════════════════════════════════════════════════════════════
if st.session_state.get("view_mode") == "admin" and is_admin:
    st.markdown(f"<div class='brand-title'>🛡️ {t('admin_console', lang)}</div>", unsafe_allow_html=True)
    st.markdown("<p class='brand-subtitle'>Supervision technique de la base SQLite et gestion des autorisations</p>" if lang == "fr" else "<p class='brand-subtitle'>Technical supervision of SQLite database and permissions management</p>", unsafe_allow_html=True)

    col_ab1, col_ab2 = st.columns([1, 1])
    with col_ab1:
        lbl_adm_home = "Accueil" if lang == "fr" else "Home"
        if st.button(f"🏠 {lbl_adm_home}", key="btn_admin_home", use_container_width=True):
            st.session_state["view_mode"] = "home"
            st.rerun()
    with col_ab2:
        if st.button(t("back_to_project", lang), key="btn_admin_back_proj", use_container_width=True):
            st.session_state["view_mode"] = "modules"
            st.rerun()

    tab_users, tab_db, tab_all_proj = st.tabs(["👥 Utilisateurs / Users", "🗄️ Maintenance Base SQLite", "📁 Projets / Projects"])

    with tab_users:
        st.subheader("Comptes Enregistrés" if lang == "fr" else "Registered Users")
        users_list = get_all_users()
        u_df = pd.DataFrame(users_list)
        if not u_df.empty:
            st.dataframe(u_df[["id", "username", "role", "created_at"]], use_container_width=True)

        st.divider()
        col_new_u, col_mod_u = st.columns(2)

        with col_new_u:
            st.markdown("#### ➕ Ajouter un utilisateur" if lang == "fr" else "#### ➕ Create New User")
            with st.form("admin_create_user_form"):
                u_name = st.text_input("Nom d'utilisateur / Username")
                u_pwd = st.text_input("Mot de passe / Password", type="password")
                u_role = st.selectbox("Rôle :", ["user", "admin"])
                submit_u = st.form_submit_button("Créer le compte" if lang == "fr" else "Create Account", use_container_width=True, type="primary")
                if submit_u:
                    if u_name and u_pwd:
                        uid = create_user(u_name.strip(), u_pwd, role=u_role)
                        if uid:
                            st.success(f"Utilisateur '{u_name}' créé (ID #{uid}) !")
                            st.rerun()
                        else:
                            st.error("Ce nom d'utilisateur existe déjà.")
                    else:
                        st.error("Renseignez tous les champs.")

        with col_mod_u:
            st.markdown("#### ⚙️ Gérer un compte existant" if lang == "fr" else "#### ⚙️ Manage Existing Account")
            user_options = {u["id"]: f"#{u['id']} - {u['username']} ({u['role']})" for u in users_list}
            target_uid = st.selectbox("Choisir l'utilisateur :", options=list(user_options.keys()), format_func=lambda x: user_options[x])

            if target_uid:
                target_user = [u for u in users_list if u["id"] == target_uid][0]
                new_role = st.selectbox("Rôle :", ["user", "admin"], index=0 if target_user["role"] == "user" else 1)
                if st.button("Modifier le rôle" if lang == "fr" else "Update Role", use_container_width=True):
                    if target_uid == user["id"] and new_role != "admin":
                        st.error("Action impossible sur votre propre compte actif.")
                    else:
                        update_user_role(target_uid, new_role)
                        st.success("Rôle actualisé !")
                        st.rerun()

                new_pwd_input = st.text_input("Réinitialiser mot de passe :" if lang == "fr" else "Reset Password:", type="password", key="admin_pwd_change")
                if st.button("Mettre à jour mot de passe" if lang == "fr" else "Update Password", use_container_width=True):
                    if new_pwd_input:
                        update_user_password(target_uid, new_pwd_input)
                        st.success("Mot de passe modifié !")
                    else:
                        st.warning("Veuillez saisir un mot de passe.")

                if target_uid != user["id"]:
                    if st.button("🗑️ Supprimer cet utilisateur" if lang == "fr" else "🗑️ Delete User", type="secondary", use_container_width=True):
                        delete_user(target_uid)
                        st.success("Compte supprimé !")
                        st.rerun()

    with tab_db:
        st.subheader("Santé & Taille de la Base de Données" if lang == "fr" else "Database Health & Size")
        stats = get_db_stats()
        s1, s2, s3 = st.columns(3)
        s1.metric("Utilisateurs", stats.get("total_users", 0))
        s2.metric("Projets créés", stats.get("total_projects", 0))
        s3.metric("Taille BDD", f"{stats.get('db_size_kb', 0):,.1f} Ko")

        st.divider()
        col_vac, col_back = st.columns(2)
        with col_vac:
            st.markdown("#### 🧹 Nettoyage VACUUM" if lang == "fr" else "#### 🧹 VACUUM Optimization")
            if st.button("Exécuter VACUUM" if lang == "fr" else "Run VACUUM", use_container_width=True, type="primary"):
                res = vacuum_database()
                st.success(f"Opération réussie. Intégrité : {res}")

        with col_back:
            st.markdown("#### 💾 Sauvegarde" if lang == "fr" else "#### 💾 Backup")
            if os.path.exists(DB_PATH):
                with open(DB_PATH, "rb") as f_db:
                    st.download_button(
                        label="⬇️ Exporter le fichier .db" if lang == "fr" else "⬇️ Export .db file",
                        data=f_db.read(),
                        file_name="sales_forecasting_backup.db",
                        mime="application/x-sqlite3",
                        use_container_width=True
                    )

    with tab_all_proj:
        st.subheader("Inventaire & Gestion des Projets" if lang == "fr" else "All Projects Inventory & Management")
        all_projs = get_all_projects_admin()
        if all_projs:
            st.dataframe(pd.DataFrame(all_projs), use_container_width=True)

            st.markdown("<hr style='margin: 1.2rem 0; border: none; border-top: 1px solid var(--border-subtle);'>", unsafe_allow_html=True)
            st.markdown("#### 🗑️ Suppression Administrative d'un Projet" if lang == "fr" else "#### 🗑️ Administrative Project Deletion")
            st.caption("Permet à l'administrateur de purger n'importe quel projet et ses artefacts du disque." if lang == "fr" else "Allows admin to purge any project and disk artifacts across all users.")

            admin_proj_opts = {p["id"]: f"#{p['id']} - {p['name']} (Propriétaire: {p['owner_username']})" for p in all_projs}
            target_del_pid = st.selectbox(
                "Sélectionner le projet à supprimer :" if lang == "fr" else "Select project to delete:",
                options=list(admin_proj_opts.keys()),
                format_func=lambda x: admin_proj_opts[x],
                key="admin_del_proj_sel"
            )

            col_ad1, col_ad2 = st.columns([1.5, 2])
            with col_ad1:
                confirm_chk = st.checkbox("Confirmer la suppression irréversible" if lang == "fr" else "Confirm permanent deletion", key="chk_admin_del_confirm")
            with col_ad2:
                if st.button("🗑️ Supprimer ce projet (Admin)" if lang == "fr" else "🗑️ Delete Project (Admin)", type="primary", disabled=not confirm_chk, use_container_width=True):
                    delete_project(target_del_pid)
                    if st.session_state.get("active_project_id") == target_del_pid:
                        st.session_state["active_project_id"] = None
                    st.success(f"Projet #{target_del_pid} supprimé avec succès !" if lang == "fr" else f"Project #{target_del_pid} deleted successfully!")
                    st.rerun()
        else:
            st.info("Aucun projet enregistré." if lang == "fr" else "No projects recorded.")
