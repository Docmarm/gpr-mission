# app_admin.py - Version Améliorée
import streamlit as st
import os
import requests
from datetime import datetime, timedelta
import pandas as pd
import io
import plotly.express as px
import plotly.graph_objects as go
import calendar

# -------------------------
# Configuration de la page
# -------------------------
st.set_page_config(
    page_title="Admin - Gestion Missions",
    layout="wide",
    page_icon="⚙️",
    initial_sidebar_state="expanded"
)

# -------------------------
# CSS personnalisé amélioré
# -------------------------
st.markdown(
    """
<style>
div[data-testid="stSidebarNav"] { display: none; }
section[data-testid="stSidebarHeader"] { display: none; }
/* Cards KPI modernes avec animations */
.kpi-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    height: 100%;
}
.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(0,0,0,0.18);
}
.kpi-value { 
    font-size: 32px; 
    font-weight: 700; 
    margin-top: 8px;
    letter-spacing: -1px;
}
.kpi-sub { 
    font-size: 13px; 
    opacity: 0.9;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Badges de statut améliorés */
.status-badge {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.s-pending { background: #ffd54a; color: #000; }
.s-approved { background: #4caf50; color: #fff; }
.s-rejected { background: #ef5350; color: #fff; }
.s-cancelled { background: #9e9e9e; color: #fff; }

/* Cards de contenu */
.card-box {
    padding: 16px;
    border-radius: 12px;
    background: #ffffff;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    border: 1px solid #f0f0f0;
    transition: all 0.3s ease;
}
.card-box:hover {
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border-color: #667eea;
}

/* Styles de texte */
.small-muted { 
    font-size: 12px; 
    color: #6c757d;
    font-weight: 500;
}
.section-header {
    font-size: 20px;
    font-weight: 700;
    color: #2c3e50;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 3px solid #667eea;
}

/* Amélioration des expanders */
.streamlit-expanderHeader {
    font-weight: 600;
    font-size: 16px;
    background-color: #f8f9fa;
    border-radius: 8px;
}

/* Animations de chargement */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
.loading-indicator {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Style des boutons */
.stButton>button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.3s ease;
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

/* Tables */
.dataframe {
    border-radius: 8px;
    overflow: hidden;
}

/* Success/Error messages améliorés */
.stSuccess, .stError, .stWarning, .stInfo {
    border-radius: 8px;
    padding: 12px 16px;
}
/* Quick Stats */
.quick-stats { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 16px; border-radius: 12px; margin: 16px 0; display: flex; justify-content: space-around; color: white; box-shadow: 0 6px 20px rgba(0,0,0,0.15); }
.quick-stat-item { text-align: center; }
.quick-stat-value { font-size: 28px; font-weight: 800; display: block; }
.quick-stat-label { font-size: 11px; opacity: 0.9; text-transform: uppercase; letter-spacing: 0.5px; }
</style>
""",
    unsafe_allow_html=True,
)

# Navigation personnalisée dans la sidebar
if st.sidebar.button("🏠 Accueil"):
    st.switch_page("mission_home_page.py")
if st.sidebar.button("📝 Demande de mission"):
    st.session_state.app_mode = "demande"
    st.switch_page("mission_home_page.py")
if st.sidebar.button("🗺️ Planification"):
    st.switch_page("pages/mission.py")
st.sidebar.markdown("---")
if st.sidebar.button("⚙️ Admin"):
    st.switch_page("pages/admin.py")

# -------------------------
# Initialisation Firebase sécurisée
# -------------------------
@st.cache_resource
def initialize_firebase_safe():
    """Initialise Firebase avec gestion d'erreurs robuste"""
    try:
        from firebase_config import initialize_firebase
        db = initialize_firebase()
        return db, None
    except Exception as e:
        return None, str(e)

db, firebase_error = initialize_firebase_safe()

# -------------------------
# Système de notifications toast
# -------------------------
def show_toast(message, type="info"):
    """Affiche une notification élégante"""
    if type == "success":
        st.success(f"✅ {message}")
    elif type == "error":
        st.error(f"❌ {message}")
    elif type == "warning":
        st.warning(f"⚠️ {message}")
    else:
        st.info(f"ℹ️ {message}")

# -------------------------
# Authentification améliorée
# -------------------------
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    # Écran de connexion moderne
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; color: #667eea;'>🔐</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>Connexion Administrateur</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6c757d;'>Accédez au panneau de gestion</p>", unsafe_allow_html=True)

        if firebase_error:
            with st.expander("⚠️ Configuration Firebase", expanded=False):
                st.error(f"Firebase non configuré : {firebase_error}")
                st.info(
                    "Pour configurer Firebase, ajoutez vos credentials dans `.streamlit/secrets.toml` "
                    "ou utilisez `FIREBASE_SERVICE_ACCOUNT` ou `firebase-credentials.json`."
                )

        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("👤 Identifiant", placeholder="Entrez votre identifiant")
            password = st.text_input("🔑 Mot de passe", type="password", placeholder="Entrez votre mot de passe")
            
            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_b:
                submitted = st.form_submit_button("Se connecter", use_container_width=True, type="primary")
            
            if submitted:
                if not username or not password:
                    show_toast("Veuillez remplir tous les champs", "error")
                else:
                    # Tentative de connexion avec credentials locaux
                    cfg = st.secrets.get("admin", {}) if st.secrets else {}
                    expected_user = (cfg.get("username") or os.getenv("ADMIN_USERNAME") or "admin").strip().lower()
                    expected_pass = cfg.get("password") or os.getenv("ADMIN_PASSWORD") or "admin123"
                    
                    if username.strip().lower() == expected_user and password == expected_pass:
                        st.session_state.admin_logged_in = True
                        st.session_state.admin_user = {"email": expected_user, "role": "admin"}
                        show_toast("Connexion réussie ! Bienvenue 👋", "success")
                        st.rerun()
                    elif db is not None:
                        # Tentative avec Firebase
                        try:
                            from firebase_admin import auth
                            from firebase_config import FIREBASE_CONFIG
                            api_key = FIREBASE_CONFIG.get("apiKey")
                            
                            if api_key:
                                r = requests.post(
                                    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
                                    json={"email": username.strip(), "password": password, "returnSecureToken": True},
                                    timeout=10,
                                )
                                
                                if r.status_code == 200:
                                    id_token = r.json().get("idToken")
                                    decoded = auth.verify_id_token(id_token)
                                    uid = decoded.get("uid")
                                    
                                    # Récupération du rôle
                                    role = None
                                    try:
                                        doc = db.collection("users").document(uid).get()
                                        role = (doc.to_dict() or {}).get("role")
                                    except Exception:
                                        role = decoded.get("role")
                                    
                                    if role in ("admin", "manager"):
                                        st.session_state.admin_logged_in = True
                                        st.session_state.admin_user = {"uid": uid, "email": username.strip(), "role": role}
                                        show_toast(f"Connexion réussie en tant que {role} 🎉", "success")
                                        st.rerun()
                                    else:
                                        show_toast("Accès refusé - Droits administrateur requis", "error")
                                else:
                                    show_toast("Identifiants Firebase invalides", "error")
                            else:
                                show_toast("Configuration Firebase incomplète (apiKey manquante)", "error")
                        except Exception as e:
                            show_toast(f"Erreur Firebase : {e}", "error")
                    else:
                        show_toast("Identifiants incorrects", "error")
    st.stop()

# -------------------------
# Sidebar & Navigation améliorée
# -------------------------
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #667eea;'>🎯 Admin Panel</h2>", unsafe_allow_html=True)
    
    user_info = st.session_state.get('admin_user', {})
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 15px; border-radius: 12px; color: white; text-align: center; margin-bottom: 20px;'>
        <p style='margin: 0; font-size: 14px; opacity: 0.9;'>👤 Connecté en tant que</p>
        <p style='margin: 5px 0; font-size: 16px; font-weight: 700;'>{user_info.get('email', 'Admin')}</p>
        <p style='margin: 0; font-size: 12px; opacity: 0.8;'>🔑 {user_info.get('role', 'admin').upper()}</p>
    </div>
    """, unsafe_allow_html=True)
    # Quick Stats
    try:
        from firebase_config import StatisticsManager
        stats_side = StatisticsManager().get_dashboard_stats()
    except Exception:
        stats_side = get_mock_stats()
    st.markdown(f"""
    <div class='quick-stats'>
        <div class='quick-stat-item'>
            <span class='quick-stat-value'>{stats_side.get('pending_requests', 0)}</span>
            <span class='quick-stat-label'>En attente</span>
        </div>
        <div class='quick-stat-item'>
            <span class='quick-stat-value'>{stats_side.get('active_missions', 0)}</span>
            <span class='quick-stat-label'>Actives</span>
        </div>
        <div class='quick-stat-item'>
            <span class='quick-stat-value'>{stats_side.get('missions_this_month', 0)}</span>
            <span class='quick-stat-label'>Ce mois</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation avec icônes améliorées
    page = st.radio(
        "📍 Navigation",
        [
            "📊 Tableau de bord",
            "📝 Demandes",
            "🚗 Véhicules",
            "👨‍✈️ Chauffeurs",
            "📅 Calendrier",
            "📈 Statistiques",
            "👥 Utilisateurs"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Statut système
    if db is None:
        st.warning("⚠️ Mode dégradé\nDonnées simulées")
    else:
        st.success("✅ Système connecté")
    
    st.markdown("---")
    
    # Bouton de déconnexion stylisé
    if st.button("🚪 Déconnexion", use_container_width=True, type="secondary"):
        st.session_state.admin_logged_in = False
        st.rerun()
    
    st.markdown("---")
    st.caption("💻 Developed by @Moctar TALL\nv2.0 • 2026")

# -------------------------
# Helpers: Mock data avec cache
# -------------------------
@st.cache_data(ttl=60)
def get_mock_stats():
    """Retourne des statistiques simulées"""
    return {
        "pending_requests": 8,
        "active_missions": 5,
        "total_vehicles": 18,
        "total_drivers": 12,
        "missions_this_month": 42,
        "vehicles_available": 9,
        "drivers_available": 7,
    }

@st.cache_data(ttl=60)
def load_requests_mock(status=None):
    """Génère des demandes fictives pour le mode dégradé"""
    base = []
    for i in range(1, 51):
        base.append({
            "id": f"req_{i}",
            "request_id": f"MR-{1000+i}",
            "motif_mission": f"Visite site {i}",
            "nom_demandeur": f"User {i}",
            "email_demandeur": f"user{i}@example.com",
            "service_demandeur": "Operations",
            "date_depart": (datetime.now() + timedelta(days=i%5)).strftime("%Y-%m-%d"),
            "date_retour": (datetime.now() + timedelta(days=(i%5)+1)).strftime("%Y-%m-%d"),
            "destination": "Site A",
            "nb_passagers": 1 + (i % 4),
            "type_vehicule": "SUV" if i % 2 == 0 else "Berline",
            "status": ["pending","approved","rejected","cancelled"][i % 4],
            "created_at": (datetime.now() - timedelta(days=i)).isoformat(),
            "avec_chauffeur": True if i % 3 == 0 else False
        })
    if status and status != "all":
        return [r for r in base if r['status'] == status]
    return base

@st.cache_data(ttl=30)
def load_requests_live(_db=None, status=None):
    """Charge les demandes depuis Firebase"""
    try:
        from firebase_config import MissionRequestManager
        req_mgr = MissionRequestManager()
        reqs = req_mgr.get_all_requests(status=status) if status and status != "all" else req_mgr.get_all_requests()
        out = []
        for r in reqs:
            created = r.get('created_at')
            if isinstance(created, datetime):
                created = created.isoformat()
            out.append({**r, "created_at": created})
        return out
    except Exception:
        return []

@st.cache_data(ttl=120)
def cached_all_drivers():
    from firebase_config import DriverManager
    return DriverManager().get_all_drivers()

@st.cache_data(ttl=120)
def cached_all_vehicles():
    from firebase_config import VehicleManager
    return VehicleManager().get_all_vehicles()

# -------------------------
# Utilitaires
# -------------------------
def status_badge_html(status):
    """Génère un badge HTML coloré pour le statut"""
    cls_map = {
        "pending": ("s-pending", "En attente"),
        "approved": ("s-approved", "Approuvé"),
        "rejected": ("s-rejected", "Rejeté"),
        "cancelled": ("s-cancelled", "Annulé")
    }
    cls, label = cls_map.get(status, ("s-pending", status.capitalize()))
    return f"<span class='status-badge {cls}'>{label}</span>"

def modern_progress(label, value, max_value=100, color="#667eea"):
    percentage = (value / max_value) * 100 if max_value > 0 else 0
    st.markdown(f"""
    <div style='margin: 16px 0;'>
        <div style='display: flex; justify-content: space-between; margin-bottom: 8px;'>
            <span style='font-weight: 600; color: #2c3e50;'>{label}</span>
            <span style='font-weight: 700; color: {color};'>{value}/{max_value}</span>
        </div>
        <div style='background: #e0e0e0; height: 12px; border-radius: 10px; overflow: hidden;'>
            <div style='background: linear-gradient(90deg, {color} 0%, #764ba2 100%); width: {percentage}%; height: 100%; border-radius: 10px; transition: width 0.5s ease;'></div>
        </div>
        <div style='text-align: right; font-size: 12px; color: #6c757d; margin-top: 4px;'>
            {percentage:.1f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

def modern_alert(message, alert_type="info", icon=None):
    cfg = {
        "info": {"color": "#2196F3", "bg": "#E3F2FD", "icon": "ℹ️"},
        "success": {"color": "#4caf50", "bg": "#E8F5E9", "icon": "✅"},
        "warning": {"color": "#ff9800", "bg": "#FFF3E0", "icon": "⚠️"},
        "error": {"color": "#f44336", "bg": "#FFEBEE", "icon": "❌"},
    }
    c = cfg.get(alert_type, cfg["info"]) 
    ic = icon if icon else c["icon"]
    st.markdown(f"""
    <div style='background: {c["bg"]}; border-left: 4px solid {c["color"]}; padding: 16px 20px; border-radius: 12px; margin: 12px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>
        <div style='display: flex; align-items: center; gap: 12px;'>
            <span style='font-size: 24px;'>{ic}</span>
            <span style='color: #2c3e50; font-weight: 500;'>{message}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def advanced_pagination(data, items_per_page=10, key="pagination"):
    total_items = len(data)
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
    if f"{key}_page" not in st.session_state:
        st.session_state[f"{key}_page"] = 1
    current_page = st.session_state[f"{key}_page"]
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    with col1:
        if st.button("⏮️ Première", key=f"{key}_first", disabled=(current_page == 1)):
            st.session_state[f"{key}_page"] = 1
            st.rerun()
    with col2:
        if st.button("◀️ Préc", key=f"{key}_prev", disabled=(current_page == 1)):
            st.session_state[f"{key}_page"] = max(1, current_page - 1)
            st.rerun()
    with col3:
        st.markdown(f"""
        <div style='text-align: center; padding: 8px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; font-weight: 700;'>
            Page {current_page} sur {total_pages} ({total_items} éléments)
        </div>
        """, unsafe_allow_html=True)
    with col4:
        if st.button("Suiv ▶️", key=f"{key}_next", disabled=(current_page == total_pages)):
            st.session_state[f"{key}_page"] = min(total_pages, current_page + 1)
            st.rerun()
    with col5:
        if st.button("Dernière ⏭️", key=f"{key}_last", disabled=(current_page == total_pages)):
            st.session_state[f"{key}_page"] = total_pages
            st.rerun()
    with st.expander("🔍 Aller à la page"):
        jump_page = st.number_input("Numéro de page", min_value=1, max_value=total_pages, value=current_page, key=f"{key}_jump")
        if st.button("Aller", key=f"{key}_go"):
            st.session_state[f"{key}_page"] = jump_page
            st.rerun()
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    return data[start_idx:end_idx], current_page, total_pages

def advanced_search_bar(data, columns=None):
    st.markdown("""
    <div style='background: white; padding: 20px; border-radius: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); margin-bottom: 24px;'>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search_query = st.text_input("🔍 Recherche globale", placeholder="Rechercher dans tous les champs...", key="global_search")
    with col2:
        search_columns = columns or data.columns.tolist()
        selected_column = st.selectbox("Colonne", ["Toutes"] + search_columns, key="search_column")
    with col3:
        case_sensitive = st.checkbox("Sensible à la casse", value=False)
    st.markdown("</div>", unsafe_allow_html=True)
    if search_query:
        if selected_column == "Toutes":
            mask = data.astype(str).apply(lambda row: row.str.contains(search_query, case=case_sensitive, na=False).any(), axis=1)
        else:
            mask = data[selected_column].astype(str).str.contains(search_query, case=case_sensitive, na=False)
        return data[mask]
    return data

def advanced_export_options(data, filename_prefix="export"):
    with st.expander("📥 Options d'export avancées"):
        col1, col2, col3 = st.columns(3)
        with col1:
            export_format = st.radio("Choisir le format", ["CSV", "Excel", "JSON"], horizontal=True)
        with col2:
            all_columns = data.columns.tolist()
            selected_columns = st.multiselect("Colonnes à exporter", all_columns, default=all_columns)
        with col3:
            include_index = st.checkbox("Inclure l'index", value=False)
            include_timestamp = st.checkbox("Horodatage dans le nom", value=True)
        if st.button("📥 Générer l'export", type="primary", use_container_width=True):
            export_data = data[selected_columns] if selected_columns else data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if include_timestamp else ""
            filename = f"{filename_prefix}_{timestamp}" if timestamp else filename_prefix
            if export_format == "CSV":
                csv = export_data.to_csv(index=include_index).encode('utf-8')
                st.download_button("💾 Télécharger CSV", data=csv, file_name=f"{filename}.csv", mime="text/csv", use_container_width=True)
            elif export_format == "Excel":
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    export_data.to_excel(writer, index=include_index, sheet_name='Data')
                st.download_button("💾 Télécharger Excel", data=buffer.getvalue(), file_name=f"{filename}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            elif export_format == "JSON":
                json_data = export_data.to_json(orient='records', indent=2)
                st.download_button("💾 Télécharger JSON", data=json_data, file_name=f"{filename}.json", mime="application/json", use_container_width=True)

def modern_file_uploader(accept_multiple=True, file_types=None):
    st.markdown("""
    <div style='border: 3px dashed #667eea; border-radius: 16px; padding: 40px; text-align: center; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 20%); margin: 20px 0; transition: all 0.3s ease;' onmouseover='this.style.background="linear-gradient(135deg, #667eea 0%, #764ba2 20%)"' onmouseout='this.style.background="linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 20%)"'>
        <div style='font-size: 64px; margin-bottom: 16px;'>📁</div>
        <h3 style='color: #2c3e50; margin-bottom: 8px;'>Glissez-déposez vos fichiers ici</h3>
        <p style='color: #6c757d;'>ou cliquez pour parcourir</p>
    </div>
    """, unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Sélectionner des fichiers", accept_multiple_files=accept_multiple, type=file_types, label_visibility="collapsed")
    if uploaded_files:
        files = uploaded_files if accept_multiple else [uploaded_files]
        st.success(f"✅ {len(files)} fichier(s) téléchargé(s)")
        for file in files:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**📄 {file.name}**")
            with col2:
                size_mb = file.size / (1024 * 1024)
                st.caption(f"{size_mb:.2f} MB")
            with col3:
                st.caption(file.type)
        return files if accept_multiple else files[0]
    return None

def confirm_action(message, button_text="Confirmer", key=None):
    if f"{key}_confirm_dialog" not in st.session_state:
        st.session_state[f"{key}_confirm_dialog"] = False
    if not st.session_state[f"{key}_confirm_dialog"]:
        if st.button(button_text, key=f"{key}_trigger", type="primary"):
            st.session_state[f"{key}_confirm_dialog"] = True
            st.rerun()
    else:
        st.warning(f"⚠️ {message}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Oui, confirmer", key=f"{key}_yes", type="primary", use_container_width=True):
                st.session_state[f"{key}_confirm_dialog"] = False
                return True
        with col2:
            if st.button("❌ Annuler", key=f"{key}_no", use_container_width=True):
                st.session_state[f"{key}_confirm_dialog"] = False
                st.rerun()
    return False


def setup_keyboard_shortcuts():
    st.markdown("""
    <script>
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'k') { e.preventDefault(); document.querySelector('input[placeholder*="Recherche"]')?.focus(); }
            if (e.ctrlKey && e.key === 'n') { e.preventDefault(); }
            if (e.ctrlKey && e.key === 's') { e.preventDefault(); document.querySelector('button[kind="primary"]')?.click(); }
        });
    </script>
    """, unsafe_allow_html=True)

def to_excel_bytes(df: pd.DataFrame, sheet_name="export"):
    """Convertit un DataFrame en bytes Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

def format_date(date_val):
    """Formatte une date de manière lisible"""
    if pd.isna(date_val):
        return "—"
    if isinstance(date_val, str):
        try:
            date_val = pd.to_datetime(date_val)
        except:
            return date_val
    return date_val.strftime("%d/%m/%Y %H:%M")

# -------------------------
# PAGE: Tableau de bord amélioré
# -------------------------
if page == "📊 Tableau de bord":
    st.markdown("<h1 style='color: #2c3e50;'>📊 Tableau de bord</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6c757d; font-size: 16px;'>Vue d'ensemble de la gestion des missions</p>", unsafe_allow_html=True)
    
    # Contrôles améliorés
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 2, 3, 2])
        with col1:
            range_days = st.selectbox(
                "📅 Période", 
                ["7 jours", "14 jours", "30 jours", "90 jours"], 
                index=1,
                help="Sélectionnez la période d'analyse"
            )
            mapping = {"7 jours": 7, "14 jours": 14, "30 jours": 30, "90 jours": 90}
            days = mapping[range_days]
        
        with col2:
            view_mode = st.radio(
                "👁️ Affichage", 
                ["Compact", "Complet"], 
                index=0, 
                horizontal=True,
                help="Mode d'affichage des KPIs"
            )
        
        with col3:
            q_search = st.text_input(
                "🔎 Recherche rapide", 
                value="",
                placeholder="Rechercher demande, chauffeur, véhicule..."
            )
        
        with col4:
            auto_refresh = st.checkbox("🔄 Actualisation auto", value=False)
            if auto_refresh:
                st.markdown("<small>⏱️ Refresh: 60s</small>", unsafe_allow_html=True)

    st.markdown("---")

    # Chargement des statistiques
    with st.spinner("📊 Chargement des statistiques..."):
        try:
            if db is not None:
                from firebase_config import StatisticsManager, CalendarManager
                stats = StatisticsManager().get_dashboard_stats()
                availability = CalendarManager().check_availability(
                    datetime.now(), 
                    datetime.now() + timedelta(days=1)
                )
                pending = stats.get('pending_requests', 0)
                active = stats.get('active_missions', 0)
                total_veh = stats.get('total_vehicles', 0)
                total_drv = stats.get('total_drivers', 0)
                veh_available = availability.get('vehicles_count', 0)
                drv_available = availability.get('drivers_count', 0)
                missions_month = stats.get('missions_this_month', 0)
            else:
                ms = get_mock_stats()
                pending, active = ms['pending_requests'], ms['active_missions']
                total_veh, total_drv = ms['total_vehicles'], ms['total_drivers']
                veh_available, drv_available = ms['vehicles_available'], ms['drivers_available']
                missions_month = ms['missions_this_month']
        except Exception as e:
            show_toast(f"Erreur chargement stats: {e}", "error")
            ms = get_mock_stats()
            pending, active = ms['pending_requests'], ms['active_missions']
            total_veh, total_drv = ms['total_vehicles'], ms['total_drivers']
            veh_available, drv_available = ms['vehicles_available'], ms['drivers_available']
            missions_month = ms['missions_this_month']

    # KPI Cards avec animations
    k1, k2, k3, k4 = st.columns(4)
    
    with k1:
        st.markdown(
            f"""<div class='kpi-card'>
                <div class='kpi-sub'>⏳ Demandes en attente</div>
                <div class='kpi-value'>{pending}</div>
            </div>""", 
            unsafe_allow_html=True
        )
    
    with k2:
        st.markdown(
            f"""<div class='kpi-card'>
                <div class='kpi-sub'>🚀 Missions actives</div>
                <div class='kpi-value'>{active}</div>
            </div>""", 
            unsafe_allow_html=True
        )
    
    with k3:
        pct_veh = (veh_available / total_veh * 100) if total_veh > 0 else 0
        st.markdown(
            f"""<div class='kpi-card'>
                <div class='kpi-sub'>🚗 Véhicules disponibles</div>
                <div class='kpi-value'>{veh_available} / {total_veh}</div>
                <div class='kpi-sub'>{pct_veh:.0f}% de disponibilité</div>
            </div>""", 
            unsafe_allow_html=True
        )
    
    with k4:
        pct_drv = (drv_available / total_drv * 100) if total_drv > 0 else 0
        st.markdown(
            f"""<div class='kpi-card'>
                <div class='kpi-sub'>👨‍✈️ Chauffeurs disponibles</div>
                <div class='kpi-value'>{drv_available} / {total_drv}</div>
                <div class='kpi-sub'>{pct_drv:.0f}% de disponibilité</div>
            </div>""", 
            unsafe_allow_html=True
        )
    st.markdown("<br>", unsafe_allow_html=True)
    used_veh = max(0, total_veh - veh_available)
    modern_progress("Utilisation véhicules", used_veh, total_veh, "#4caf50")

    # KPIs supplémentaires en mode Complet
    if view_mode == "Complet":
        st.markdown("<br>", unsafe_allow_html=True)
        c5, c6, c7, c8 = st.columns(4)
        
        with c5:
            st.markdown(
                f"""<div class='card-box'>
                    <div class='small-muted'>📅 Missions ce mois</div>
                    <div class='kpi-value' style='color: #667eea;'>{missions_month}</div>
                </div>""", 
                unsafe_allow_html=True
            )
        
        with c6:
            st.markdown(
                f"""<div class='card-box'>
                    <div class='small-muted'>🚙 Total véhicules</div>
                    <div class='kpi-value' style='color: #667eea;'>{total_veh}</div>
                </div>""", 
                unsafe_allow_html=True
            )
        
        with c7:
            st.markdown(
                f"""<div class='card-box'>
                    <div class='small-muted'>👥 Total chauffeurs</div>
                    <div class='kpi-value' style='color: #667eea;'>{total_drv}</div>
                </div>""", 
                unsafe_allow_html=True
            )
        
        with c8:
            taux_approbation = (42 / (42 + 8) * 100) if (42 + 8) > 0 else 0  # Exemple
            st.markdown(
                f"""<div class='card-box'>
                    <div class='small-muted'>✅ Taux d'approbation</div>
                    <div class='kpi-value' style='color: #4caf50;'>{taux_approbation:.0f}%</div>
                </div>""", 
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Graphiques et tableaux
    left, right = st.columns([2, 1])
    
    with left:
        st.markdown("<div class='section-header'>📈 Évolution des demandes</div>", unsafe_allow_html=True)
        
        try:
            lookback_start = datetime.now() - timedelta(days=days-1)
            requests = load_requests_live(_db=db) if db is not None else load_requests_mock()
            df_req = pd.DataFrame(requests)
            
            if not df_req.empty:
                df_req['created_at'] = pd.to_datetime(df_req['created_at'], errors='coerce', utc=True).dt.tz_convert(None)
                df_req = df_req[df_req['created_at'] >= lookback_start]
                df_req['date'] = df_req['created_at'].dt.date
                ts = df_req.groupby('date').size().rename('count').reset_index()
            else:
                ts = pd.DataFrame({
                    'date': pd.date_range(start=lookback_start.date(), periods=days).date, 
                    'count': [0]*days
                })
            
            # Compléter les jours manquants
            full_range = pd.date_range(start=lookback_start.date(), periods=days).date
            ts = ts.set_index('date').reindex(full_range, fill_value=0).rename_axis('date').reset_index()
            
            # Graphique moderne avec Plotly
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=ts['date'],
                y=ts['count'],
                mode='lines+markers',
                name='Demandes',
                line=dict(color='#667eea', width=3),
                marker=dict(size=8, color='#764ba2'),
                fill='tozeroy',
                fillcolor='rgba(102, 126, 234, 0.1)'
            ))
            
            fig.update_layout(
                title=f"Demandes créées — {days} derniers jours",
                xaxis_title="Date",
                yaxis_title="Nombre de demandes",
                height=380,
                hovermode='x unified',
                template='plotly_white',
                margin=dict(t=40, l=20, r=20, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            show_toast(f"Erreur graphique: {e}", "error")
        
        # Tableau des demandes récentes
        st.markdown("<div class='section-header'>🔍 Demandes récentes</div>", unsafe_allow_html=True)
        
        try:
            df_table = df_req.copy() if 'df_req' in locals() else pd.DataFrame(
                load_requests_live(_db=db) if db is not None else load_requests_mock()
            )
            
            if not df_table.empty:
                df_table['created_at'] = pd.to_datetime(df_table['created_at'], errors='coerce', utc=True).dt.tz_convert(None)
                df_table['created'] = df_table['created_at'].dt.strftime("%d/%m/%Y %H:%M")
                
                # Filtrage par recherche
                if q_search:
                    mask = df_table.astype(str).apply(
                        lambda row: row.str.contains(q_search, case=False).any(), 
                        axis=1
                    )
                    df_table = df_table[mask]
                
                # Tri par date décroissante
                df_table = df_table.sort_values('created_at', ascending=False).head(20)
                
                # Colonnes à afficher
                display_df = df_table[['request_id', 'motif_mission', 'nom_demandeur', 'date_depart', 'date_retour', 'status', 'created']].copy()
                display_df.columns = ['Référence', 'Motif', 'Demandeur', 'Départ', 'Retour', 'Statut', 'Créé le']
                
                st.dataframe(
                    display_df.reset_index(drop=True),
                    use_container_width=True,
                    height=350,
                    hide_index=True
                )
                
                st.caption(f"📊 {len(df_table)} résultat(s) affiché(s)")
            else:
                st.info("Aucune demande trouvée pour cette période")
                
        except Exception as e:
            show_toast(f"Erreur listing demandes: {e}", "error")
    
    with right:
        # Répartition par statut
        st.markdown("<div class='section-header'>🎯 Répartition par statut</div>", unsafe_allow_html=True)
        
        try:
            all_requests = load_requests_live(_db=db) if db is not None else load_requests_mock()
            
            if all_requests:
                status_counts = pd.Series([r.get('status', 'pending') for r in all_requests]).value_counts()
                
                # Labels français
                status_labels = {
                    'pending': 'En attente',
                    'approved': 'Approuvé',
                    'rejected': 'Rejeté',
                    'cancelled': 'Annulé'
                }
                
                status_df = pd.DataFrame({
                    'Statut': [status_labels.get(s, s) for s in status_counts.index],
                    'Count': status_counts.values
                })
                
                # Couleurs personnalisées
                colors = ['#ffd54a', '#4caf50', '#ef5350', '#9e9e9e']
                
                fig2 = px.pie(
                    status_df,
                    values='Count',
                    names='Statut',
                    hole=0.5,
                    color_discrete_sequence=colors
                )
                
                fig2.update_layout(
                    height=320,
                    margin=dict(t=20, b=20),
                    showlegend=True,
                    legend=dict(orientation="v", yanchor="middle", y=0.5)
                )
                
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Aucune donnée disponible")
                
        except Exception as e:
            show_toast(f"Erreur statuts: {e}", "error")
        
        # Top chauffeurs
        st.markdown("<div class='section-header'>🏆 Top chauffeurs (mois)</div>", unsafe_allow_html=True)
        
        try:
            if db is not None:
                from firebase_config import StatisticsManager, DriverManager
                stats_mgr = StatisticsManager()
                now = datetime.now()
                report = stats_mgr.get_monthly_report(now.year, now.month) or {}
                drivers_map = {d.get('id'): d.get('name') for d in cached_all_drivers()}
                
                rows = []
                for did, dstat in (report.get('driver_stats') or {}).items():
                    rows.append({
                        'Chauffeur': drivers_map.get(did, did),
                        'Missions': int(dstat.get('missions', dstat.get('missaions', 0) or 0)),
                        'Km': float(dstat.get('km', 0) or 0)
                    })
                
                df_top = pd.DataFrame(rows)
                if not df_top.empty and 'Missions' in df_top.columns:
                    df_top = df_top.sort_values('Missions', ascending=False).head(10)
            else:
                # Données simulées
                df_top = pd.DataFrame({
                    'Chauffeur': [f"Chauffeur {i}" for i in range(1, 7)],
                    'Missions': [12, 10, 9, 7, 5, 3],
                    'Km': [1200, 980, 760, 540, 300, 150]
                })
            
            if df_top.empty:
                st.info("Aucune mission ce mois")
            else:
                # Ajouter des badges de position avec longueur adaptée
                n = len(df_top)
                medals = ['🥇', '🥈', '🥉'][:n] + ['🎖️'] * max(n - 3, 0)
                df_top.insert(0, '🏅', medals)
                
                st.dataframe(
                    df_top.reset_index(drop=True),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Export
                col_exp1, col_exp2 = st.columns(2)
                with col_exp1:
                    csv = df_top.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 CSV",
                        data=csv,
                        file_name="top_chauffeurs.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                with col_exp2:
                    try:
                        xlsx = to_excel_bytes(df_top, "Top Chauffeurs")
                        st.download_button(
                            "📥 Excel",
                            data=xlsx,
                            file_name="top_chauffeurs.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    except:
                        pass
                        
        except Exception as e:
            show_toast(f"Erreur top chauffeurs: {e}", "error")
        
        st.markdown("<div class='section-header'>💰 Montants par chauffeur (mois)</div>", unsafe_allow_html=True)
        try:
            if db is not None:
                from firebase_config import StatisticsManager
                stats_mgr = StatisticsManager()
                now = datetime.now()
                report = stats_mgr.get_monthly_report(now.year, now.month) or {}
                dstats = report.get('driver_stats') or {}
                drivers_map = {d.get('id'): d.get('name') for d in cached_all_drivers()}
                rows = []
                for did, s in dstats.items():
                    rows.append({
                        'Chauffeur': drivers_map.get(did, did),
                        'Missions': int(s.get('missions', 0)),
                        'Jours': int(s.get('days', 0)),
                        'Per Diem (FCFA)': int(s.get('perdiem_fcfa', 0)),
                        'Hôtel (FCFA)': int(s.get('hotel_fcfa', 0)),
                        'Total (FCFA)': int(s.get('total_fcfa', (s.get('perdiem_fcfa', 0) or 0) + (s.get('hotel_fcfa', 0) or 0)))
                    })
                df_pay = pd.DataFrame(rows)
                if not df_pay.empty:
                    df_pay = df_pay.sort_values('Total (FCFA)', ascending=False)
                    st.dataframe(df_pay.reset_index(drop=True), use_container_width=True, hide_index=True)
                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        csv = df_pay.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 CSV montants", data=csv, file_name="montants_chauffeurs.csv", mime="text/csv", use_container_width=True)
                    with col_p2:
                        try:
                            xlsx = to_excel_bytes(df_pay, "Montants Chauffeurs")
                            st.download_button("📥 Excel montants", data=xlsx, file_name="montants_chauffeurs.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                        except:
                            pass
                else:
                    st.info("Aucune mission ce mois")
            else:
                df_pay = pd.DataFrame({
                    'Chauffeur': [f"Chauffeur {i}" for i in range(1, 6)],
                    'Missions': [5,4,3,2,1],
                    'Jours': [10,8,6,4,2],
                    'Per Diem (FCFA)': [80000,64000,48000,32000,16000],
                    'Hôtel (FCFA)': [300000,240000,180000,120000,60000],
                    'Total (FCFA)': [380000,304000,228000,152000,76000]
                })
                st.dataframe(df_pay, use_container_width=True, hide_index=True)
        except Exception as e:
            show_toast(f"Erreur montants: {e}", "error")
    
    # (Section astuces supprimée)

# -------------------------
# PAGE: Demandes (suite dans le prochain message...)
# -------------------------
elif page == "📝 Demandes":
    st.markdown("<h1 style='color: #2c3e50;'>📝 Gestion des demandes de mission</h1>", unsafe_allow_html=True)
    setup_keyboard_shortcuts()
    
    if db is None:
        st.warning("⚠️ Firebase non disponible. Mode lecture simulée activé.")

    try:
        # Chargement avec indicateur
        with st.spinner("🔄 Chargement des demandes..."):
            requests_all = load_requests_live(_db=db) if db is not None else load_requests_mock()
        
        # Filtres avancés
        with st.expander("🔍 Filtres avancés", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                status_filter = st.selectbox(
                    "Statut",
                    ["all", "pending", "approved", "rejected", "cancelled"],
                    format_func=lambda x: {
                        "all": "Tous",
                        "pending": "En attente",
                        "approved": "Approuvé",
                        "rejected": "Rejeté",
                        "cancelled": "Annulé"
                    }.get(x, x),
                    index=0
                )
            
            with col2:
                date_from = st.date_input(
                    "Depuis",
                    value=datetime.now().date() - timedelta(days=30)
                )
            
            with col3:
                date_to = st.date_input(
                    "Jusqu'à",
                    value=datetime.now().date() + timedelta(days=30)
                )
            
            with col4:
                q = st.text_input(
                    "Recherche",
                    placeholder="Réf, demandeur, destination..."
                )
        
        # Application des filtres
        df_all = pd.DataFrame(requests_all)
        
        if not df_all.empty:
            df_all['created_at'] = pd.to_datetime(df_all['created_at'], errors='coerce', utc=True).dt.tz_convert(None)
            df_all['date_depart_dt'] = pd.to_datetime(df_all['date_depart'], errors='coerce')
            
            # Filtres
            df_all = df_all[
                (df_all['date_depart_dt'].dt.date >= date_from) &
                (df_all['date_depart_dt'].dt.date <= date_to)
            ]
            
            if status_filter != "all":
                df_all = df_all[df_all['status'] == status_filter]
            
            df_all = advanced_search_bar(df_all)
        
        drivers_map = {}
        vehicles_map = {}
        if db is not None:
            try:
                drivers_map = {d.get('id'): d.get('name') for d in cached_all_drivers()}
                vehicles_map = {v.get('id'): v.get('immatriculation') for v in cached_all_vehicles()}
            except Exception:
                drivers_map = {}
                vehicles_map = {}
        
        # Actions en masse
        if not df_all.empty:
            st.markdown("<div class='section-header'>⚡ Actions en masse</div>", unsafe_allow_html=True)
            
            display_for_select = df_all[['request_id', 'motif_mission', 'nom_demandeur', 'date_depart', 'status']].copy()
            display_for_select['label'] = display_for_select.apply(
                lambda r: f"{r['request_id']} • {r['motif_mission']} • {r['nom_demandeur']} ({r['status']})",
                axis=1
            )
            
            selected_bulk = st.multiselect(
                "Sélectionner des demandes",
                options=display_for_select['label'].tolist(),
                help="Sélectionnez une ou plusieurs demandes pour une action groupée"
            )
            
            if selected_bulk:
                ids_bulk = [
                    display_for_select.loc[display_for_select['label'] == lbl, 'request_id'].values[0]
                    for lbl in selected_bulk
                ]
                
                st.info(f"✅ {len(ids_bulk)} demande(s) sélectionnée(s)")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("✅ Approuver", key="bulk_approve", use_container_width=True, type="primary"):
                        if db is not None:
                            from firebase_config import MissionRequestManager
                            mgr = MissionRequestManager()
                            success_count = 0
                            for rid in ids_bulk:
                                try:
                                    mgr.update_request_status_by_request_id(rid, 'approved')
                                    success_count += 1
                                except Exception:
                                    pass
                            show_toast(f"{success_count}/{len(ids_bulk)} demandes approuvées", "success")
                        else:
                            show_toast(f"{len(ids_bulk)} demandes approuvées (simulé)", "success")
                        st.rerun()
                
                with col2:
                    if st.button("❌ Rejeter", key="bulk_reject", use_container_width=True):
                        if db is not None:
                            from firebase_config import MissionRequestManager
                            mgr = MissionRequestManager()
                            success_count = 0
                            for rid in ids_bulk:
                                try:
                                    mgr.update_request_status_by_request_id(rid, 'rejected')
                                    success_count += 1
                                except Exception:
                                    pass
                            show_toast(f"{success_count}/{len(ids_bulk)} demandes rejetées", "warning")
                        else:
                            show_toast(f"{len(ids_bulk)} demandes rejetées (simulé)", "warning")
                        st.rerun()
                
                with col3:
                    sel_rows = df_all[df_all['request_id'].isin(ids_bulk)]
                    csv = sel_rows.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Export CSV",
                        data=csv,
                        file_name="demandes_selection.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col4:
                    try:
                        xlsx = to_excel_bytes(sel_rows, "Demandes")
                        st.download_button(
                            "📥 Export Excel",
                            data=xlsx,
                            file_name="demandes_selection.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    except:
                        pass
        
        st.markdown("---")
        advanced_export_options(df_all, filename_prefix="demandes_export")
        with st.expander("📎 Ajouter des pièces jointes (local)"):
            modern_file_uploader(accept_multiple=True, file_types=["pdf","jpg","jpeg","png"]) 
        
        # Pagination et affichage
        if not df_all.empty:
            df_all = df_all.sort_values('created_at', ascending=False)
            subset, current_page, total_pages = advanced_pagination(df_all.to_dict(orient='records'), items_per_page=10, key="req_pag")
            
            # Affichage des demandes
            for idx, r in enumerate(subset, 1):
                status_color = {
                    'pending': '🟡',
                    'approved': '🟢',
                    'rejected': '🔴',
                    'cancelled': '⚫'
                }.get(r.get('status', 'pending'), '🟡')
                
                header = f"{status_color} **{r.get('request_id', 'N/A')}** — {r.get('motif_mission', 'Sans motif')}"
                
                with st.expander(header, expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**👤 Demandeur:** {r.get('nom_demandeur')} ({r.get('email_demandeur')})")
                        st.markdown(f"**🏢 Service:** {r.get('service_demandeur', '—')}")
                        st.markdown(f"**📅 Période:** {r.get('date_depart')} → {r.get('date_retour')}")
                        st.markdown(f"**📍 Destination:** {r.get('destination', '—')}")
                        st.markdown(f"**👥 Passagers:** {r.get('nb_passagers', 1)} • **🚗 Véhicule:** {r.get('type_vehicule', 'Indifférent')}")
                        st.markdown(f"**👨‍✈️ Avec chauffeur:** {'Oui' if r.get('avec_chauffeur') else 'Non'}")
                        
                        # Affichage amélioré des affectations avec noms lisibles
                        assigned_driver = r.get('assigned_driver')
                        assigned_vehicle = r.get('assigned_vehicle')
                        
                        if assigned_driver or assigned_vehicle:
                            driver_display = drivers_map.get(assigned_driver, assigned_driver or '—') if assigned_driver else '—'
                            vehicle_display = vehicles_map.get(assigned_vehicle, assigned_vehicle or '—') if assigned_vehicle else '—'
                            
                            st.success(f"**✅ Affecté:** Chauffeur: {driver_display} • Véhicule: {vehicle_display}")
                        
                        atts = r.get('attachments') or []
                        if atts:
                            st.markdown("**📎 Documents:**")
                            for a in atts:
                                st.markdown(f"- [{a.get('name', 'Pièce jointe')}]({a.get('url', '')})")
                    
                    with col2:
                        st.markdown(status_badge_html(r.get('status', 'pending')), unsafe_allow_html=True)
                        st.markdown(f"<small>Créé le {format_date(r.get('created_at'))}</small>", unsafe_allow_html=True)
                        
                        # Changement de statut
                        st.markdown("---")
                        st.markdown("**🔄 Modifier le statut**")
                        new_status = st.selectbox(
                            "Nouveau statut",
                            options=["pending", "approved", "rejected", "cancelled"],
                            format_func=lambda x: {
                                "pending": "En attente",
                                "approved": "Approuvé",
                                "rejected": "Rejeté",
                                "cancelled": "Annulé"
                            }.get(x, x),
                            index=["pending", "approved", "rejected", "cancelled"].index(r.get('status', 'pending')),
                            key=f"status_{r.get('id')}"
                        )
                        
                        if st.button("💾 Appliquer", key=f"apply_{r.get('id')}", use_container_width=True):
                            try:
                                if db is not None:
                                    from firebase_config import MissionRequestManager
                                    MissionRequestManager().update_request_status(r['id'], new_status)
                                    show_toast("Statut mis à jour avec succès", "success")
                                else:
                                    show_toast("Statut mis à jour (simulé)", "success")
                                st.rerun()
                            except Exception as e:
                                show_toast(f"Erreur: {e}", "error")
                    
                    # Actions rapides
                    if r.get('status') == 'pending':
                        st.markdown("---")
                        st.markdown("**⚡ Actions rapides**")
                        
                        col_a1, col_a2, col_a3 = st.columns(3)
                        
                        with col_a1:
                            if st.button("🎯 Auto-affecter", key=f"auto_{r.get('id')}", use_container_width=True):
                                try:
                                    if db is not None:
                                        from firebase_config import MissionRequestManager, DriverManager, VehicleManager
                                        res = MissionRequestManager().auto_assign(r['id'])
                                        if res:
                                            try:
                                                dlist = DriverManager().get_all_drivers()
                                                vlist = VehicleManager().get_all_vehicles()
                                                dname = next((d.get('name') for d in dlist if d.get('id') == res.get('driver_id')), res.get('driver_id'))
                                                vlabel = next((v.get('immatriculation') for v in vlist if v.get('id') == res.get('vehicle_id')), res.get('vehicle_id'))
                                                rec = {**res, 'driver_name': dname, 'vehicle_name': vlabel}
                                            except Exception:
                                                rec = res
                                            st.session_state[f"auto_info_{r['id']}"] = rec
                                            show_toast("Recommandation générée avec succès !", "success")
                                            st.rerun()
                                        else:
                                            show_toast("Aucune ressource disponible", "warning")
                                    else:
                                        # Mode simulé - générer une recommandation fictive
                                        st.session_state[f"auto_info_{r['id']}"] = {
                                            'vehicle_id': 'v_sim_1',
                                            'vehicle_name': 'Toyota Hilux - AA-001-SN',
                                            'driver_id': 'd_sim_1',
                                            'driver_name': 'Chauffeur Ahmed',
                                            'score': 95
                                        }
                                        show_toast("Recommandation générée (mode simulé)", "info")
                                        st.rerun()
                                except Exception as e:
                                    show_toast(f"Erreur: {e}", "error")
                        
                        # Afficher la recommandation si disponible
                        rec_info = st.session_state.get(f"auto_info_{r.get('id')}")
                        if rec_info:
                            st.success("✅ **Recommandation disponible**")
                            col_rec1, col_rec2 = st.columns(2)
                            with col_rec1:
                                vehicle_name = rec_info.get('vehicle_name') or rec_info.get('vehicle_id', 'N/A')
                                st.markdown(f"**🚗 Véhicule:**  \n{vehicle_name}")
                            with col_rec2:
                                driver_name = rec_info.get('driver_name') or rec_info.get('driver_id', 'N/A')
                                st.markdown(f"**👨‍✈️ Chauffeur:**  \n{driver_name}")
                            
                            if rec_info.get('score'):
                                st.caption(f"📊 Score de compatibilité: {rec_info.get('score')}%")
                        
                        with col_a2:
                            requires_driver = bool(r.get('avec_chauffeur'))
                            has_assignment = bool(r.get('assigned_driver') and r.get('assigned_vehicle'))
                            has_reco = bool(st.session_state.get(f"auto_info_{r.get('id')}"))
                            
                            approve_disabled = requires_driver and not has_assignment and not has_reco
                            
                            if st.button(
                                "✅ Approuver",
                                key=f"approve_{r.get('id')}",
                                disabled=approve_disabled,
                                use_container_width=True,
                                type="primary"
                            ):
                                try:
                                    if db is not None:
                                        from firebase_config import MissionRequestManager
                                        mgr = MissionRequestManager()
                                        
                                        rec = st.session_state.get(f"auto_info_{r.get('id')}")
                                        if requires_driver and not has_assignment:
                                            if rec:
                                                mgr.manual_assign_and_create_mission(
                                                    r['id'],
                                                    rec.get('vehicle_id'),
                                                    rec.get('driver_id')
                                                )
                                                show_toast("Affectation et approbation réussies !", "success")
                                            else:
                                                res = mgr.auto_assign(r['id'])
                                                if res:
                                                    mgr.manual_assign_and_create_mission(
                                                        r['id'],
                                                        res.get('vehicle_id'),
                                                        res.get('driver_id')
                                                    )
                                                    show_toast("Affectation automatique réussie !", "success")
                                                else:
                                                    show_toast("Ressources indisponibles", "warning")
                                        else:
                                            mgr.update_request_status(r['id'], 'approved')
                                            show_toast("Demande approuvée !", "success")
                                    else:
                                        show_toast("Demande approuvée (simulé)", "success")
                                    st.rerun()
                                except Exception as e:
                                    show_toast(f"Erreur: {e}", "error")
                        
                        with col_a3:
                            if confirm_action("Confirmer le rejet de cette demande ?", button_text="❌ Rejeter", key=f"reject_{r.get('id')}"):
                                try:
                                    if db is not None:
                                        from firebase_config import MissionRequestManager
                                        MissionRequestManager().update_request_status(r['id'], 'rejected')
                                        show_toast("Demande rejetée", "warning")
                                    else:
                                        show_toast("Demande rejetée (simulé)", "warning")
                                    st.rerun()
                                except Exception as e:
                                    show_toast(f"Erreur: {e}", "error")
                        
                        # Affectation manuelle
                        if st.checkbox("🔧 Affectation manuelle", key=f"manual_{r.get('id')}"):
                            with st.form(f"assign_form_{r.get('id')}"):
                                st.markdown("**Sélectionner les ressources**")
                                
                                start_dt = r.get('date_depart')
                                end_dt = r.get('date_retour')
                                
                                if isinstance(start_dt, str):
                                    start_dt = pd.to_datetime(start_dt, utc=True, errors='coerce').tz_convert(None).to_pydatetime()
                                if isinstance(end_dt, str):
                                    end_dt = pd.to_datetime(end_dt, utc=True, errors='coerce').tz_convert(None).to_pydatetime()
                                
                                d_options = {"— Aucun —": None}
                                v_options = {"— Aucun —": None}
                                
                                if db is not None and start_dt and end_dt:
                                    try:
                                        from firebase_config import DriverManager, VehicleManager
                                        d_list = DriverManager().get_available_drivers(start_dt, end_dt)
                                        v_list = VehicleManager().get_available_vehicles(start_dt, end_dt)
                                        
                                        d_options.update({
                                            f"{d.get('name', 'Sans nom')} (#{d.get('id')[:6]})": d.get('id')
                                            for d in d_list
                                        })
                                        v_options.update({
                                            f"{v.get('immatriculation', 'Sans immat')} - {v.get('type', '')}": v.get('id')
                                            for v in v_list
                                        })
                                    except Exception:
                                        pass
                                
                                col_d, col_v = st.columns(2)
                                with col_d:
                                    d_label = st.selectbox("👨‍✈️ Chauffeur", list(d_options.keys()))
                                with col_v:
                                    v_label = st.selectbox("🚗 Véhicule", list(v_options.keys()))
                                
                                if st.form_submit_button("💾 Affecter les ressources", type="primary", use_container_width=True):
                                    did = d_options.get(d_label)
                                    vid = v_options.get(v_label)
                                    
                                    if not did or not vid:
                                        show_toast("Veuillez sélectionner un chauffeur et un véhicule", "warning")
                                    else:
                                        try:
                                            if db is not None:
                                                from firebase_config import MissionRequestManager
                                                mgr = MissionRequestManager()
                                                mgr.manual_assign_and_create_mission(r['id'], vid, did)
                                                show_toast("Association réussie !", "success")
                                            else:
                                                show_toast("Association réussie (simulé)", "success")
                                            st.rerun()
                                        except Exception as e:
                                            show_toast(f"Erreur: {e}", "error")
        else:
            st.info("🔍 Aucune demande ne correspond aux critères de filtrage")
    
    except Exception as e:
        show_toast(f"Erreur critique: {e}", "error")
        st.exception(e)

# -------------------------
# PAGE: Véhicules
# -------------------------
elif page == "🚗 Véhicules":
    st.markdown("<h1 style='color: #2c3e50;'>🚗 Gestion des véhicules</h1>", unsafe_allow_html=True)
    
    if db is None:
        st.warning("⚠️ Mode dégradé : opérations limitées")
    
    try:
        # Chargement des données
        vehicles = []
        drivers = []
        
        if db is not None:
            from firebase_config import VehicleManager, DriverManager
            vehicle_manager = VehicleManager()
            driver_manager = DriverManager()
            vehicles = vehicle_manager.get_all_vehicles()
            drivers = driver_manager.get_all_drivers()
        else:
            vehicles = [
                {
                    "id": f"v{i}",
                    "immatriculation": f"AA-00{i}-SN",
                    "marque": ["Toyota", "Peugeot", "Nissan"][i % 3],
                    "modele": ["Hilux", "508", "Patrol"][i % 3],
                    "type": "SUV" if i % 2 == 0 else "Berline",
                    "capacite": [4, 5, 7][i % 3],
                    "assigned_driver": None
                }
                for i in range(1, 8)
            ]
            drivers = [
                {"id": f"d{i}", "name": f"Chauffeur {i}", "status": "active"}
                for i in range(1, 6)
            ]
        
        # Statistiques rapides
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Total véhicules", len(vehicles))
        with col2:
            assigned = sum(1 for v in vehicles if v.get('assigned_driver'))
            st.metric("✅ Véhicules affectés", assigned)
        with col3:
            available = len(vehicles) - assigned
            st.metric("🆓 Véhicules libres", available)
        with col4:
            active_drivers = sum(1 for d in drivers if d.get('status') == 'active')
            st.metric("👨‍✈️ Chauffeurs actifs", active_drivers)
        
        st.markdown("---")
        
        # Ajout d'un véhicule
        with st.expander("➕ Ajouter un nouveau véhicule"):
            with st.form("create_vehicle_form", clear_on_submit=True):
                st.markdown("**Informations du véhicule**")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    immat = st.text_input("📋 Immatriculation *", placeholder="Ex: AA-001-SN")
                    marque = st.text_input("🏭 Marque", placeholder="Ex: Toyota")
                
                with col2:
                    modele = st.text_input("🚙 Modèle", placeholder="Ex: Hilux")
                    vtype = st.selectbox(
                        "📦 Type *",
                        ["Berline", "SUV", "4x4", "Minibus", "Utilitaire"],
                        index=0
                    )
                
                with col3:
                    capacite = st.number_input("👥 Capacité", min_value=1, max_value=50, value=5)
                    annee = st.number_input("📅 Année", min_value=2000, max_value=2026, value=2023)
                
                notes = st.text_area("📝 Notes / Observations", height=80, placeholder="Informations complémentaires...")
                
                col_submit1, col_submit2, col_submit3 = st.columns([1, 1, 1])
                with col_submit2:
                    submitted = st.form_submit_button("➕ Ajouter le véhicule", type="primary", use_container_width=True)
                
                if submitted:
                    if not immat or not vtype:
                        show_toast("L'immatriculation et le type sont obligatoires", "error")
                    else:
                        try:
                            if db is not None:
                                vehicle_id = vehicle_manager.add_vehicle({
                                    "immatriculation": immat.strip().upper(),
                                    "marque": marque.strip(),
                                    "modele": modele.strip(),
                                    "type": vtype,
                                    "capacite": int(capacite),
                                    "annee": int(annee),
                                    "notes": notes.strip()
                                })
                                show_toast(f"Véhicule {immat} ajouté avec succès !", "success")
                            else:
                                show_toast(f"Véhicule {immat} ajouté (simulé)", "success")
                            st.rerun()
                        except Exception as e:
                            show_toast(f"Erreur lors de l'ajout: {e}", "error")
        
        # Association chauffeur ↔ véhicule
        with st.expander("🔗 Associer un chauffeur à un véhicule"):
            if not vehicles:
                st.info("Aucun véhicule disponible pour association")
            else:
                with st.form("assign_driver_form"):
                    st.markdown("**Créer une association**")
                    
                    col1, col2 = st.columns(2)
                    
                    vehicle_options = {
                        f"{v.get('immatriculation', '')} — {v.get('marque', '')} {v.get('modele', '')} ({v.get('type', '')})": v.get('id')
                        for v in vehicles
                    }
                    
                    driver_options = {
                        f"{d.get('name', '')} (ID: {d.get('id', '')[:6]})": d.get('id')
                        for d in drivers
                        if d.get('status', 'active') == 'active'
                    }
                    
                    with col1:
                        selected_vehicle_label = st.selectbox("🚗 Sélectionner un véhicule", list(vehicle_options.keys()))
                    
                    with col2:
                        selected_driver_label = st.selectbox("👨‍✈️ Sélectionner un chauffeur", list(driver_options.keys()))
                    
                    col_sub1, col_sub2, col_sub3 = st.columns([1, 1, 1])
                    with col_sub2:
                        submitted_assign = st.form_submit_button("🔗 Créer l'association", type="primary", use_container_width=True)
                    
                    if submitted_assign:
                        try:
                            vehicle_id = vehicle_options[selected_vehicle_label]
                            driver_id = driver_options[selected_driver_label]
                            
                            if db is not None:
                                vehicle_manager.assign_driver(vehicle_id, driver_id)
                                show_toast("Association créée avec succès !", "success")
                            else:
                                show_toast("Association créée (simulé)", "success")
                            st.rerun()
                        except Exception as e:
                            show_toast(f"Erreur: {e}", "error")
        
        st.markdown("---")
        
        # Tableau des véhicules
        if vehicles:
            st.markdown("<div class='section-header'>🚗 Liste des véhicules</div>", unsafe_allow_html=True)
            
            # Préparer les données
            df_vehicles = pd.DataFrame(vehicles)
            
            # Colonnes à afficher
            display_cols = ['immatriculation', 'marque', 'modele', 'type', 'capacite']
            
            if 'assigned_driver' in df_vehicles.columns:
                df_vehicles['Chauffeur affecté'] = df_vehicles['assigned_driver'].fillna('—')
                display_cols.append('Chauffeur affecté')
            
            if 'annee' in df_vehicles.columns:
                display_cols.insert(4, 'annee')
            
            # Renommer les colonnes
            col_names = {
                'immatriculation': '📋 Immatriculation',
                'marque': '🏭 Marque',
                'modele': '🚙 Modèle',
                'type': '📦 Type',
                'capacite': '👥 Capacité',
                'annee': '📅 Année'
            }
            
            display_df = df_vehicles[[col for col in display_cols if col in df_vehicles.columns]].copy()
            display_df = display_df.rename(columns=col_names)
            
            # Afficher le tableau
            st.dataframe(
                display_df.reset_index(drop=True),
                use_container_width=True,
                height=400,
                hide_index=True
            )
            
            # Export
            col_exp1, col_exp2, col_exp3 = st.columns([1, 1, 2])
            with col_exp1:
                csv = df_vehicles.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Exporter CSV",
                    data=csv,
                    file_name="vehicules.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col_exp2:
                try:
                    xlsx = to_excel_bytes(df_vehicles, "Véhicules")
                    st.download_button(
                        "📥 Exporter Excel",
                        data=xlsx,
                        file_name="vehicules.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                except:
                    pass
        else:
            st.info("🔍 Aucun véhicule enregistré dans le système")
    
    except Exception as e:
        show_toast(f"Erreur: {e}", "error")
        st.exception(e)

# -------------------------
# PAGE: Chauffeurs
# -------------------------
elif page == "👨‍✈️ Chauffeurs":
    st.markdown("<h1 style='color: #2c3e50;'>👨‍✈️ Gestion des chauffeurs</h1>", unsafe_allow_html=True)
    
    if db is None:
        st.warning("⚠️ Mode dégradé : lecture simulée")
    
    try:
        drivers = []
        
        if db is not None:
            from firebase_config import DriverManager, VehicleManager
            driver_manager = DriverManager()
            vehicle_manager = VehicleManager()
            drivers = driver_manager.get_all_drivers()
        else:
            drivers = [
                {
                    "id": f"d{i}",
                    "name": f"Chauffeur {i}",
                    "email": f"chauffeur{i}@example.com",
                    "phone": f"+221 77 000 00{i:02d}",
                    "license_number": f"SN{i:04d}",
                    "status": "active" if i % 4 != 0 else "inactive",
                    "assigned_vehicle": None
                }
                for i in range(1, 13)
            ]
        
        # Statistiques
        col1, col2, col3, col4 = st.columns(4)
        
        active_count = sum(1 for d in drivers if d.get('status') == 'active')
        inactive_count = len(drivers) - active_count
        assigned_count = sum(1 for d in drivers if d.get('assigned_vehicle'))
        
        with col1:
            st.metric("📊 Total chauffeurs", len(drivers))
        with col2:
            st.metric("✅ Actifs", active_count)
        with col3:
            st.metric("⏸️ Inactifs", inactive_count)
        with col4:
            st.metric("🚗 Avec véhicule", assigned_count)
        
        st.markdown("---")
        
        # Statistiques détaillées d'un chauffeur
        with st.expander("📊 Statistiques d'un chauffeur"):
            if not drivers:
                st.info("Aucun chauffeur disponible")
            else:
                options = {
                    f"{d.get('name')} ({d.get('email', 'N/A')})": d.get('id')
                    for d in drivers
                }
                
                selected_label = st.selectbox("Choisir un chauffeur", list(options.keys()))
                sel_id = options[selected_label]
                
                # Charger les stats
                stats = {
                    "total_missions": 23,
                    "missions_this_month": 4,
                    "total_km": 1250,
                    "driver_info": {}
                }
                
                if db is not None:
                    try:
                        stats = driver_manager.get_driver_statistics(sel_id)
                    except Exception:
                        pass
                
                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                
                col_s1.metric("🎯 Missions totales", stats.get('total_missions', 0))
                col_s2.metric("📅 Missions ce mois", stats.get('missions_this_month', 0))
                col_s3.metric("🛣️ Kilomètres total", f"{stats.get('total_km', 0):,} km")
                
                avg_km = (stats.get('total_km', 0) / stats.get('total_missions', 1)) if stats.get('total_missions', 0) > 0 else 0
                col_s4.metric("📏 Moyenne km/mission", f"{avg_km:.0f} km")
                
                # Info chauffeur
                info = stats.get('driver_info', {})
                if info:
                    st.markdown("---")
                    st.markdown("**📋 Informations**")
                    col_i1, col_i2, col_i3 = st.columns(3)
                    col_i1.write(f"📧 Email: {info.get('email', '—')}")
                    col_i2.write(f"📞 Téléphone: {info.get('phone', '—')}")
                    col_i3.write(f"🪪 Permis: {info.get('license_number', '—')}")
        
        # Ajout d'un chauffeur
        with st.expander("➕ Ajouter un nouveau chauffeur"):
            with st.form("create_driver_form", clear_on_submit=True):
                st.markdown("**Informations du chauffeur**")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    name = st.text_input("👤 Nom complet *", placeholder="Ex: Amadou Diallo")
                    email = st.text_input("📧 Email", placeholder="email@example.com")
                
                with col2:
                    phone = st.text_input("📞 Téléphone *", placeholder="+221 77 000 00 00")
                    license_no = st.text_input("🪪 N° permis", placeholder="SN0001")
                
                with col3:
                    status = st.selectbox("📊 Statut", ["active", "inactive"], index=0)
                    notes = st.text_area("📝 Notes", height=100, placeholder="Observations...")
                
                col_sub1, col_sub2, col_sub3 = st.columns([1, 1, 1])
                with col_sub2:
                    sub = st.form_submit_button("➕ Ajouter le chauffeur", type="primary", use_container_width=True)
                
                if sub:
                    if not name or not phone:
                        show_toast("Le nom et le téléphone sont obligatoires", "error")
                    else:
                        try:
                            if db is not None:
                                driver_id = driver_manager.add_driver({
                                    "name": name.strip(),
                                    "email": email.strip(),
                                    "phone": phone.strip(),
                                    "license_number": license_no.strip().upper(),
                                    "status": status,
                                    "notes": notes.strip()
                                })
                                show_toast(f"Chauffeur {name} ajouté avec succès !", "success")
                            else:
                                show_toast(f"Chauffeur {name} ajouté (simulé)", "success")
                            st.rerun()
                        except Exception as e:
                            show_toast(f"Erreur: {e}", "error")
        
        st.markdown("---")
        
        # Liste des chauffeurs
        if drivers:
            st.markdown("<div class='section-header'>👥 Liste des chauffeurs</div>", unsafe_allow_html=True)
            
            df_drivers = pd.DataFrame(drivers)
            
            # Colonnes à afficher
            display_cols = ['name', 'email', 'phone', 'license_number', 'status']
            if 'assigned_vehicle' in df_drivers.columns:
                df_drivers['vehicle'] = df_drivers['assigned_vehicle'].fillna('—')
                display_cols.append('vehicle')
            
            col_names = {
                'name': '👤 Nom',
                'email': '📧 Email',
                'phone': '📞 Téléphone',
                'license_number': '🪪 Permis',
                'status': '📊 Statut',
                'vehicle': '🚗 Véhicule'
            }
            
            display_df = df_drivers[[col for col in display_cols if col in df_drivers.columns]].copy()
            display_df = display_df.rename(columns=col_names)
            
            st.dataframe(
                display_df.reset_index(drop=True),
                use_container_width=True,
                height=400,
                hide_index=True
            )
            
            # Export
            col_exp1, col_exp2, col_exp3 = st.columns([1, 1, 2])
            with col_exp1:
                csv = df_drivers.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Exporter CSV",
                    data=csv,
                    file_name="chauffeurs.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col_exp2:
                try:
                    xlsx = to_excel_bytes(df_drivers, "Chauffeurs")
                    st.download_button(
                        "📥 Exporter Excel",
                        data=xlsx,
                        file_name="chauffeurs.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                except:
                    pass
        else:
            st.info("🔍 Aucun chauffeur enregistré")
    
    except Exception as e:
        show_toast(f"Erreur: {e}", "error")
        st.exception(e)

# -------------------------
# PAGE: Calendrier
# -------------------------
elif page == "📅 Calendrier":
    st.markdown("<h1 style='color: #2c3e50;'>📅 Calendrier des missions</h1>", unsafe_allow_html=True)
    
    if db is None:
        st.warning("⚠️ Mode dégradé : calendrier simulé")
    
    try:
        # Sélection de période
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            start_date_input = st.date_input(
                "📅 Date de début",
                value=datetime.now() - timedelta(days=30)
            )
        
        with col2:
            end_date_input = st.date_input(
                "📅 Date de fin",
                value=datetime.now() + timedelta(days=30)
            )
        
        with col3:
            view_type = st.selectbox(
                "👁️ Vue",
                ["Timeline", "Liste", "Calendrier (mois)"],
                index=0
            )
        
        start_dt = datetime.combine(start_date_input, datetime.min.time())
        end_dt = datetime.combine(end_date_input, datetime.max.time())
        
        # Charger les missions
        missions = []
        drivers_map = {}
        
        if db is not None:
            from firebase_config import CalendarManager, DriverManager, VehicleManager
            calendar_manager = CalendarManager()
            missions = calendar_manager.get_missions_in_period(start_dt, end_dt)
            drivers_map = {d.get('id'): d.get('name') for d in cached_all_drivers()}
            vehicles_map = {v.get('id'): v.get('immatriculation') for v in cached_all_vehicles()}
        else:
            # Données simulées
            for i in range(1, 15):
                missions.append({
                    "id": f"mission_{i}",
                    "motif_mission": f"Mission {i}",
                    "start_date": datetime.now() + timedelta(days=i, hours=8),
                    "end_date": datetime.now() + timedelta(days=i, hours=16),
                    "assigned_driver": f"d{i%5}",
                    "assigned_vehicle": f"v{i%7}",
                    "destination": f"Site {chr(65 + i%10)}"
                })
            drivers_map = {f"d{i}": f"Chauffeur {i}" for i in range(10)}
        
        if not missions:
            st.info("🔍 Aucune mission planifiée pour cette période")
        else:
            st.success(f"📊 {len(missions)} mission(s) trouvée(s)")
            
            if view_type == "Timeline":
                # Vue Timeline
                cal_data = []
                for m in missions:
                    driver_id = m.get('driver_id') or m.get('assigned_driver')
                    driver_name = drivers_map.get(driver_id, driver_id or 'Non affecté')
                    
                    cal_data.append({
                        "Mission": m.get('motif_mission', 'Mission') + f" ({m.get('destination', '')})",
                        "Début": m.get('start_date'),
                        "Fin": m.get('end_date'),
                        "Chauffeur": driver_name
                    })
                
                df_cal = pd.DataFrame(cal_data)
                
                # Créer le graphique timeline
                fig = px.timeline(
                    df_cal,
                    x_start="Début",
                    x_end="Fin",
                    y="Mission",
                    color="Chauffeur",
                    title="Vue temporelle des missions"
                )
                
                fig.update_yaxes(autorange="reversed")
                fig.update_layout(
                    height=max(420, len(missions) * 30),
                    hovermode='closest',
                    template='plotly_white'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            elif view_type == "Calendrier (mois)":
                # Vue Calendrier mensuel navigable
                # État du mois courant
                if 'cal_month_start' not in st.session_state:
                    st.session_state.cal_month_start = datetime(datetime.now().year, datetime.now().month, 1)
                # Navigation mois
                nav_prev, nav_title, nav_next = st.columns([1,3,1])
                with nav_prev:
                    if st.button("◀ Mois précédent"):
                        ms = st.session_state.cal_month_start
                        prev_month = (ms.replace(day=1) - timedelta(days=1)).replace(day=1)
                        st.session_state.cal_month_start = prev_month
                        st.rerun()
                with nav_title:
                    st.subheader(st.session_state.cal_month_start.strftime("%B %Y").capitalize())
                with nav_next:
                    if st.button("Mois suivant ▶"):
                        ms = st.session_state.cal_month_start
                        next_month = (ms.replace(day=28) + timedelta(days=4)).replace(day=1)
                        st.session_state.cal_month_start = next_month
                        st.rerun()

                month_start = st.session_state.cal_month_start
                month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                # Préparer mapping missions par jour
                def to_dt(x):
                    if isinstance(x, str):
                        try:
                            return pd.to_datetime(x, utc=True, errors='coerce').tz_convert(None).to_pydatetime()
                        except Exception:
                            return pd.to_datetime(x, errors='coerce')
                    return x
                mission_map = {}
                for m in missions:
                    s = to_dt(m.get('start_date'))
                    e = to_dt(m.get('end_date'))
                    if not s or not e:
                        continue
                    day = s.date()
                    while day <= e.date():
                        mission_map.setdefault(day, []).append(m)
                        day = (datetime.combine(day, datetime.min.time()) + timedelta(days=1)).date()

                # En-têtes jours
                headers = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
                hc = st.columns(7)
                for i, h in enumerate(headers):
                    hc[i].markdown(f"**{h}**")

                # Calcul grille 6 semaines
                first_weekday = (month_start.weekday())  # Monday=0
                grid_start = month_start - timedelta(days=first_weekday)
                days_grid = [grid_start + timedelta(days=i) for i in range(42)]

                selected_date = st.session_state.get("calendar_selected_date")
                idx = 0
                for _ in range(6):
                    cols = st.columns(7)
                    for ci in range(7):
                        d = days_grid[idx]; idx += 1
                        in_month = (d.month == month_start.month)
                        count = len(mission_map.get(d.date(), []))
                        label = f"{d.day} ({count})" if count else f"{d.day}"
                        if cols[ci].button(label, key=f"daybtn_{d.date().isoformat()}"):
                            st.session_state["calendar_selected_date"] = d.date()
                            st.rerun()
                        if not in_month:
                            cols[ci].caption("")
                        elif count:
                            cols[ci].caption("{} mission(s)".format(count))

                # Détails du jour sélectionné
                sd = st.session_state.get("calendar_selected_date")
                if sd:
                    st.markdown(f"### 📅 Missions du {sd.strftime('%d/%m/%Y')}")
                    items = mission_map.get(sd, [])
                    if not items:
                        st.info("Aucune mission ce jour")
                    else:
                        rows = []
                        for m in items:
                            driver_id = m.get('driver_id') or m.get('assigned_driver')
                            driver_name = drivers_map.get(driver_id, 'Non affecté')
                            vehicle_id = m.get('vehicle_id') or m.get('assigned_vehicle')
                            vehicle_label = vehicles_map.get(vehicle_id, vehicle_id or 'N/A') if db is not None else (vehicle_id or 'N/A')
                            rows.append({
                                '🎯 Mission': m.get('motif_mission', 'Sans titre'),
                                '👨‍✈️ Chauffeur': driver_name,
                                '🚗 Véhicule': vehicle_label,
                                '📅 Début': format_date(m.get('start_date')),
                                '📅 Fin': format_date(m.get('end_date')),
                                '📍 Destination': m.get('destination', '—')
                            })
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            else:
                # Vue Liste
                list_data = []
                for m in missions:
                    driver_id = m.get('driver_id') or m.get('assigned_driver')
                    driver_name = drivers_map.get(driver_id, 'Non affecté')
                    vehicle_id = m.get('vehicle_id') or m.get('assigned_vehicle', 'N/A')
                    vehicle_label = vehicles_map.get(vehicle_id, vehicle_id or 'N/A') if db is not None else vehicle_id
                    
                    list_data.append({
                        '🎯 Mission': m.get('motif_mission', 'Sans titre'),
                        '📍 Destination': m.get('destination', '—'),
                        '📅 Début': format_date(m.get('start_date')),
                        '📅 Fin': format_date(m.get('end_date')),
                        '👨‍✈️ Chauffeur': driver_name,
                        '🚗 Véhicule': vehicle_label
                    })
                
                df_list = pd.DataFrame(list_data)
                st.dataframe(
                    df_list.reset_index(drop=True),
                    use_container_width=True,
                    height=500,
                    hide_index=True
                )
                
                # Export
                col1, col2 = st.columns(2)
                with col1:
                    csv = df_list.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Exporter CSV",
                        data=csv,
                        file_name="calendrier_missions.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                with col2:
                    try:
                        xlsx = to_excel_bytes(df_list, "Calendrier")
                        st.download_button(
                            "📥 Exporter Excel",
                            data=xlsx,
                            file_name="calendrier_missions.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    except:
                        pass
    
    except Exception as e:
        show_toast(f"Erreur: {e}", "error")
        st.exception(e)

# -------------------------
# PAGE: Statistiques
# -------------------------
elif page == "📈 Statistiques":
    st.markdown("<h1 style='color: #2c3e50;'>📈 Statistiques et rapports</h1>", unsafe_allow_html=True)
    st.info("📊 Exports avancés, graphiques et rapports synthétiques")
    
    try:
        # Filtres de période
        col1, col2, col3 = st.columns(3)
        
        with col1:
            rpt_from = st.date_input(
                "📅 Depuis",
                value=datetime.now().date() - timedelta(days=30)
            )
        
        with col2:
            rpt_to = st.date_input(
                "📅 Jusqu'à",
                value=datetime.now().date()
            )
        
        with col3:
            report_type = st.selectbox(
                "📑 Type de rapport",
                ["Vue globale", "Demandes", "Top chauffeurs", "Utilisation véhicules", "Par service"],
                index=0
            )
        
        # Charger les données
        if db is not None:
            requests_df = pd.DataFrame(load_requests_live(_db=db))
        else:
            requests_df = pd.DataFrame(load_requests_mock())
        
        if not requests_df.empty:
            requests_df['created_at'] = pd.to_datetime(requests_df['created_at'], errors='coerce', utc=True).dt.tz_convert(None)
            if 'date_depart' in requests_df.columns:
                requests_df['date_depart_dt'] = pd.to_datetime(requests_df['date_depart'], errors='coerce')
                mask = (requests_df['date_depart_dt'].dt.date >= rpt_from) & (requests_df['date_depart_dt'].dt.date <= rpt_to)
                df_period = requests_df[mask].copy()
            else:
                df_period = requests_df.copy()
        else:
            df_period = pd.DataFrame()

        # Missions sur la période (pour stats avancées)
        df_missions = pd.DataFrame()
        drivers_map = {}
        vehicles_map = {}
        services_map = {}
        period_start_dt = datetime.combine(rpt_from, datetime.min.time())
        period_end_dt = datetime.combine(rpt_to, datetime.max.time())
        if db is not None:
            try:
                from firebase_config import CalendarManager, DriverManager, VehicleManager, MissionRequestManager
                cal = CalendarManager()
                missions = cal.get_missions_in_period(period_start_dt, period_end_dt)
                df_missions = pd.DataFrame(missions)
                drivers_map = {d.get('id'): d.get('name') for d in cached_all_drivers()}
                vehicles_map = {v.get('id'): v.get('immatriculation') for v in cached_all_vehicles()}
                # map request_id -> service
                try:
                    reqs = MissionRequestManager().get_all_requests()
                    services_map = {r.get('request_id'): r.get('service_demandeur') for r in reqs}
                except Exception:
                    services_map = {}
                if not df_missions.empty:
                    df_missions['start_date'] = pd.to_datetime(df_missions['start_date'], errors='coerce')
                    df_missions['end_date'] = pd.to_datetime(df_missions['end_date'], errors='coerce')
                    df_missions['duration_hours'] = (df_missions['end_date'] - df_missions['start_date']).dt.total_seconds() / 3600
                    df_missions['driver_name'] = df_missions['driver_id'].apply(lambda x: drivers_map.get(x, x))
                    df_missions['vehicle_plate'] = df_missions['vehicle_id'].apply(lambda x: vehicles_map.get(x, x))
                    df_missions['service'] = df_missions['request_id'].apply(lambda x: services_map.get(x, '—'))
                    if 'distance_km' not in df_missions.columns:
                        df_missions['distance_km'] = 0.0
            except Exception as e:
                pass
        
        st.markdown("---")
        
        # Rapports selon le type
        if report_type == "Vue globale":
            st.markdown("<div class='section-header'>📊 Vue d'ensemble</div>", unsafe_allow_html=True)
            
            # KPIs
            if db is not None:
                from firebase_config import StatisticsManager
                sm = StatisticsManager()
                dash = sm.get_dashboard_stats()
            else:
                dash = get_mock_stats()
            
            kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
            kpi1.metric("⏳ En attente", dash.get('pending_requests', 0))
            kpi2.metric("🚀 Actives", dash.get('active_missions', 0))
            kpi3.metric("🚗 Véhicules", dash.get('total_vehicles', 0))
            kpi4.metric("👨‍✈️ Chauffeurs", dash.get('total_drivers', 0))
            kpi5.metric("📅 Ce mois", dash.get('missions_this_month', 0))

            # KPIs période basée sur missions
            if not df_missions.empty:
                tot_m = len(df_missions)
                tot_km = float(df_missions.get('distance_km', pd.Series(dtype=float)).fillna(0).sum()) if 'distance_km' in df_missions.columns else 0.0
                tot_h = float(df_missions['duration_hours'].fillna(0).sum())
                kpa, kpb, kpc = st.columns(3)
                kpa.metric("📦 Missions (période)", tot_m)
                kpb.metric("🕒 Heures (période)", f"{tot_h:.1f} h")
                kpc.metric("🛣️ Km (période)", f"{tot_km:.0f} km")
            
            # Graphiques
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                if not df_missions.empty:
                    df_daily = df_missions.copy()
                    df_daily['date'] = df_daily['start_date'].dt.date
                    ts = df_daily.groupby('date').size().reset_index(name='Missions')
                    fig1 = px.line(
                        ts,
                        x='date',
                        y='Missions',
                        title="📈 Missions par jour (période)",
                        markers=True
                    )
                    fig1.update_layout(height=350, template='plotly_white')
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.info("Aucune mission sur la période")
            with col_g2:
                if not df_period.empty:
                    status_counts = df_period['status'].value_counts()
                    status_labels = {
                        'pending': 'En attente',
                        'approved': 'Approuvé',
                        'rejected': 'Rejeté',
                        'cancelled': 'Annulé'
                    }
                    fig2 = px.pie(
                        values=status_counts.values,
                        names=[status_labels.get(s, s) for s in status_counts.index],
                        title="🎯 Répartition des demandes par statut",
                        hole=0.45,
                        color_discrete_sequence=['#ffd54a', '#4caf50', '#ef5350', '#9e9e9e']
                    )
                    fig2.update_layout(height=350)
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("Aucune demande sur la période")
        
        elif report_type == "Demandes":
            st.markdown("<div class='section-header'>📝 Rapport des demandes</div>", unsafe_allow_html=True)
            
            if df_period.empty:
                st.info("🔍 Aucune demande pour cette période")
            else:
                st.success(f"📊 {len(df_period)} demande(s) sur la période")
                
                # Tableau détaillé
                export_cols = ['request_id', 'motif_mission', 'nom_demandeur', 'email_demandeur',
                              'service_demandeur', 'date_depart', 'date_retour', 'destination',
                              'nb_passagers', 'type_vehicule', 'status', 'created_at']
                
                export_df = df_period[[c for c in export_cols if c in df_period.columns]].copy()
                
                # Renommer
                export_df.columns = ['Référence', 'Motif', 'Demandeur', 'Email', 'Service',
                                    'Départ', 'Retour', 'Destination', 'Passagers',
                                    'Type véhicule', 'Statut', 'Créé le']
                
                st.dataframe(
                    export_df.reset_index(drop=True),
                    use_container_width=True,
                    height=400,
                    hide_index=True
                )
                
                # Exports
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    csv = export_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Télécharger CSV",
                        data=csv,
                        file_name=f"rapport_demandes_{rpt_from}_{rpt_to}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                with col2:
                    try:
                        xlsx = to_excel_bytes(export_df, "Demandes")
                        st.download_button(
                            "📥 Télécharger Excel",
                            data=xlsx,
                            file_name=f"rapport_demandes_{rpt_from}_{rpt_to}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    except:
                        pass
        
        elif report_type == "Top chauffeurs":
            st.markdown("<div class='section-header'>🏆 Top chauffeurs</div>", unsafe_allow_html=True)
            if not df_missions.empty:
                df_top = df_missions.groupby('driver_name', dropna=False).agg(
                    Missions=('driver_name', 'size'),
                    Kilomètres=('distance_km', 'sum'),
                    Heures=('duration_hours', 'sum')
                ).reset_index()
                df_top['Kilomètres'] = df_top['Kilomètres'].fillna(0)
                df_top = df_top.sort_values('Missions', ascending=False)
            else:
                df_top = pd.DataFrame(columns=['Chauffeur','Missions','Kilomètres','Heures'])
            
            if df_top.empty:
                st.info("🔍 Aucune statistique chauffeur disponible")
            else:
                # Graphique
                fig = px.bar(
                    df_top.head(10),
                    x='driver_name',
                    y='Missions',
                    color='Kilomètres',
                    title="🏆 Top 10 chauffeurs par nombre de missions",
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(height=400, template='plotly_white')
                st.plotly_chart(fig, use_container_width=True)
                
                # Tableau
                st.dataframe(
                    df_top.rename(columns={'driver_name':'Chauffeur'}).reset_index(drop=True),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Export
                col1, col2 = st.columns(2)
                with col1:
                    csv = df_top.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Télécharger CSV",
                        data=csv,
                        file_name="top_chauffeurs.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                with col2:
                    try:
                        xlsx = to_excel_bytes(df_top.rename(columns={'driver_name':'Chauffeur'}), "Top Chauffeurs")
                        st.download_button(
                            "📥 Télécharger Excel",
                            data=xlsx,
                            file_name="top_chauffeurs.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    except:
                        pass
        
        elif report_type == "Utilisation véhicules":
            st.markdown("<div class='section-header'>🚗 Utilisation des véhicules</div>", unsafe_allow_html=True)
            if df_missions.empty:
                st.info("🔍 Aucune mission sur la période")
            else:
                total_hours_period = max((period_end_dt - period_start_dt).total_seconds() / 3600, 0.001)
                util = df_missions.groupby('vehicle_plate')['duration_hours'].sum().reset_index().rename(columns={'duration_hours':'Heures occupées'})
                util['Utilisation'] = (util['Heures occupées'] / total_hours_period) * 100
                util = util.sort_values('Utilisation', ascending=False)
                fig = px.bar(util, x='vehicle_plate', y='Utilisation', title='🚗 Taux d\'utilisation des véhicules (période)', labels={'vehicle_plate':'Véhicule','Utilisation':'% utilisation'})
                fig.update_layout(height=400, template='plotly_white')
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(util, use_container_width=True, hide_index=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button("📥 Export CSV", data=util.to_csv(index=False).encode('utf-8'), file_name="utilisation_vehicules.csv", mime="text/csv", use_container_width=True)
                with col2:
                    try:
                        st.download_button("📥 Export Excel", data=to_excel_bytes(util, "Utilisation"), file_name="utilisation_vehicules.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                    except:
                        pass

        else:  # Par service
            st.markdown("<div class='section-header'>🏢 Répartition par service</div>", unsafe_allow_html=True)
            if df_missions.empty:
                st.info("🔍 Aucune mission sur la période")
            else:
                by_service = df_missions.groupby('service').size().reset_index(name='Missions')
                fig = px.bar(by_service, x='service', y='Missions', title="🏢 Missions par service", labels={'service':'Service','Missions':'Nombre'})
                fig.update_layout(height=400, template='plotly_white')
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(by_service, use_container_width=True, hide_index=True)
                st.download_button("📥 Export CSV", data=by_service.to_csv(index=False).encode('utf-8'), file_name="missions_par_service.csv", mime="text/csv", use_container_width=True)
    
    except Exception as e:
        show_toast(f"Erreur: {e}", "error")
        st.exception(e)

# -------------------------
# PAGE: Utilisateurs
# -------------------------
elif page == "👥 Utilisateurs":
    st.markdown("<h1 style='color: #2c3e50;'>👥 Gestion des utilisateurs</h1>", unsafe_allow_html=True)
    
    if db is None:
        st.error("❌ Firebase requis pour la gestion des utilisateurs")
        st.info("💡 Configurez Firebase pour activer cette fonctionnalité")
    else:
        try:
            from firebase_admin import auth
            
            # Création d'utilisateur
            with st.expander("➕ Créer un nouveau compte utilisateur", expanded=True):
                with st.form("create_user_form", clear_on_submit=True):
                    st.markdown("**Informations du compte**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        u_email = st.text_input("📧 Email *", placeholder="utilisateur@example.com")
                        u_password = st.text_input("🔑 Mot de passe *", type="password", help="Min. 6 caractères")
                        u_name = st.text_input("👤 Nom complet", placeholder="Prénom Nom")
                    
                    with col2:
                        u_phone = st.text_input("📞 Téléphone", placeholder="+221 77 000 00 00")
                        u_role = st.selectbox(
                            "🔐 Rôle *",
                            ["user", "manager", "admin"],
                            format_func=lambda x: {
                                "user": "👤 Utilisateur",
                                "manager": "👔 Manager",
                                "admin": "🔑 Administrateur"
                            }.get(x, x),
                            index=0,
                            help="user: peut créer des demandes | manager: peut approuver | admin: accès complet"
                        )
                        u_service = st.text_input("🏢 Service", placeholder="Ex: Operations")
                    
                    col_sub1, col_sub2, col_sub3 = st.columns([1, 1, 1])
                    with col_sub2:
                        submitted_user = st.form_submit_button(
                            "➕ Créer le compte",
                            type="primary",
                            use_container_width=True
                        )
                    
                    if submitted_user:
                        if not u_email or not u_password:
                            show_toast("Email et mot de passe sont obligatoires", "error")
                        elif len(u_password) < 6:
                            show_toast("Le mot de passe doit contenir au moins 6 caractères", "error")
                        else:
                            try:
                                # Créer l'utilisateur dans Firebase Auth
                                user = auth.create_user(
                                    email=u_email.strip(),
                                    password=u_password,
                                    display_name=u_name.strip() or None
                                )
                                
                                # Définir les custom claims (rôle)
                                auth.set_custom_user_claims(user.uid, {"role": u_role})
                                
                                # Créer le document utilisateur dans Firestore
                                db.collection("users").document(user.uid).set({
                                    "email": u_email.strip(),
                                    "name": u_name.strip(),
                                    "phone": u_phone.strip(),
                                    "role": u_role,
                                    "service": u_service.strip(),
                                    "created_at": datetime.now(),
                                    "status": "active"
                                })
                                
                                show_toast(f"✅ Compte créé pour {u_email} avec le rôle {u_role}", "success")
                                st.balloons()
                            except Exception as e:
                                show_toast(f"Erreur lors de la création: {e}", "error")
            
            # Liste des utilisateurs
            st.markdown("---")
            st.markdown("<div class='section-header'>👥 Liste des utilisateurs</div>", unsafe_allow_html=True)
            
            try:
                # Récupérer tous les utilisateurs depuis Firestore
                users_ref = db.collection("users").stream()
                users_list = []
                
                for doc in users_ref:
                    user_data = doc.to_dict()
                    users_list.append({
                        'ID': doc.id,
                        '👤 Nom': user_data.get('name', '—'),
                        '📧 Email': user_data.get('email', '—'),
                        '📞 Téléphone': user_data.get('phone', '—'),
                        '🔐 Rôle': user_data.get('role', 'user'),
                        '🏢 Service': user_data.get('service', '—'),
                        '📊 Statut': user_data.get('status', 'active')
                    })
                
                if users_list:
                    df_users = pd.DataFrame(users_list)
                    
                    # Filtres
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        role_filter = st.multiselect(
                            "Filtrer par rôle",
                            options=['user', 'manager', 'admin'],
                            default=['user', 'manager', 'admin']
                        )
                    with col_f2:
                        status_filter = st.radio(
                            "Statut",
                            options=['Tous', 'active', 'inactive'],
                            horizontal=True,
                            index=0
                        )
                    
                    # Appliquer les filtres
                    if role_filter:
                        df_users = df_users[df_users['🔐 Rôle'].isin(role_filter)]
                    if status_filter != 'Tous':
                        df_users = df_users[df_users['📊 Statut'] == status_filter]
                    
                    st.dataframe(
                        df_users.drop(columns=['ID']).reset_index(drop=True),
                        use_container_width=True,
                        height=400,
                        hide_index=True
                    )
                    
                    st.caption(f"📊 {len(df_users)} utilisateur(s) affiché(s)")
                    
                    # Export
                    col_exp1, col_exp2 = st.columns(2)
                    with col_exp1:
                        csv = df_users.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "📥 Exporter CSV",
                            data=csv,
                            file_name="utilisateurs.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    with col_exp2:
                        try:
                            xlsx = to_excel_bytes(df_users, "Utilisateurs")
                            st.download_button(
                                "📥 Exporter Excel",
                                data=xlsx,
                                file_name="utilisateurs.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                        except:
                            pass
                else:
                    st.info("🔍 Aucun utilisateur trouvé dans la base de données")
            
            except Exception as e:
                show_toast(f"Erreur lors du chargement des utilisateurs: {e}", "error")
            
            # Gestion des rôles
            st.markdown("---")
            with st.expander("🔐 Modifier le rôle d'un utilisateur"):
                st.markdown("**⚠️ Attention**: La modification des rôles affecte les permissions d'accès")
                
                try:
                    # Liste des utilisateurs pour modification
                    users_ref = db.collection("users").stream()
                    users_dict = {}
                    
                    for doc in users_ref:
                        user_data = doc.to_dict()
                        label = f"{user_data.get('name', 'Sans nom')} ({user_data.get('email', 'N/A')}) - Rôle actuel: {user_data.get('role', 'user')}"
                        users_dict[label] = {
                            'uid': doc.id,
                            'current_role': user_data.get('role', 'user')
                        }
                    
                    if users_dict:
                        with st.form("change_role_form"):
                            selected_user_label = st.selectbox(
                                "Sélectionner un utilisateur",
                                options=list(users_dict.keys())
                            )
                            
                            new_role = st.selectbox(
                                "Nouveau rôle",
                                options=["user", "manager", "admin"],
                                format_func=lambda x: {
                                    "user": "👤 Utilisateur",
                                    "manager": "👔 Manager",
                                    "admin": "🔑 Administrateur"
                                }.get(x, x)
                            )
                            
                            col_sub1, col_sub2, col_sub3 = st.columns([1, 1, 1])
                            with col_sub2:
                                if st.form_submit_button("🔄 Modifier le rôle", type="primary", use_container_width=True):
                                    try:
                                        user_info = users_dict[selected_user_label]
                                        uid = user_info['uid']
                                        
                                        # Mettre à jour les custom claims
                                        auth.set_custom_user_claims(uid, {"role": new_role})
                                        
                                        # Mettre à jour Firestore
                                        db.collection("users").document(uid).update({
                                            "role": new_role,
                                            "updated_at": datetime.now()
                                        })
                                        
                                        show_toast(f"Rôle mis à jour vers '{new_role}' avec succès", "success")
                                        st.rerun()
                                    except Exception as e:
                                        show_toast(f"Erreur: {e}", "error")
                    else:
                        st.info("Aucun utilisateur disponible")
                
                except Exception as e:
                    show_toast(f"Erreur: {e}", "error")
            
            # Désactivation/Réactivation de compte
            st.markdown("---")
            with st.expander("🔒 Désactiver / Réactiver un compte"):
                st.markdown("**ℹ️ Info**: Les comptes désactivés ne peuvent plus se connecter")
                
                try:
                    users_ref = db.collection("users").stream()
                    users_status_dict = {}
                    
                    for doc in users_ref:
                        user_data = doc.to_dict()
                        status = user_data.get('status', 'active')
                        label = f"{user_data.get('name', 'Sans nom')} ({user_data.get('email', 'N/A')}) - Statut: {status}"
                        users_status_dict[label] = {
                            'uid': doc.id,
                            'email': user_data.get('email'),
                            'current_status': status
                        }
                    
                    if users_status_dict:
                        with st.form("change_status_form"):
                            selected_user_label = st.selectbox(
                                "Sélectionner un utilisateur",
                                options=list(users_status_dict.keys())
                            )
                            
                            user_info = users_status_dict[selected_user_label]
                            current_status = user_info['current_status']
                            
                            action = "Désactiver" if current_status == "active" else "Réactiver"
                            new_status = "inactive" if current_status == "active" else "active"
                            
                            col_sub1, col_sub2, col_sub3 = st.columns([1, 1, 1])
                            with col_sub2:
                                if st.form_submit_button(
                                    f"{'🔒' if action == 'Désactiver' else '🔓'} {action} le compte",
                                    type="primary" if action == "Réactiver" else "secondary",
                                    use_container_width=True
                                ):
                                    try:
                                        uid = user_info['uid']
                                        
                                        # Mettre à jour Firebase Auth
                                        auth.update_user(uid, disabled=(new_status == "inactive"))
                                        
                                        # Mettre à jour Firestore
                                        db.collection("users").document(uid).update({
                                            "status": new_status,
                                            "updated_at": datetime.now()
                                        })
                                        
                                        show_toast(f"Compte {action.lower()}é avec succès", "success")
                                        st.rerun()
                                    except Exception as e:
                                        show_toast(f"Erreur: {e}", "error")
                    else:
                        st.info("Aucun utilisateur disponible")
                
                except Exception as e:
                    show_toast(f"Erreur: {e}", "error")
        
        except Exception as e:
            show_toast(f"Erreur de gestion des utilisateurs: {e}", "error")
            st.exception(e)

# -------------------------
# Footer et aide
# -------------------------
st.markdown("---")

# Section d'aide contextuelle
with st.expander("❓ Aide et documentation"):
    st.markdown("""
    ### 📖 Guide d'utilisation rapide
    
    #### 📊 Tableau de bord
    - Vue d'ensemble des statistiques en temps réel
    - Graphiques d'évolution des demandes
    - Top des chauffeurs les plus actifs
    - Recherche rapide dans toutes les demandes
    
    #### 📝 Gestion des demandes
    - **Filtrage avancé** : Par statut, date, ou recherche libre
    - **Actions en masse** : Approuver/rejeter plusieurs demandes simultanément
    - **Auto-affectation** : Le système recommande automatiquement les ressources disponibles
    - **Affectation manuelle** : Choisir manuellement un chauffeur et un véhicule
    
    #### 🚗 Véhicules et 👨‍✈️ Chauffeurs
    - Ajouter de nouvelles ressources
    - Associer chauffeurs et véhicules
    - Consulter les statistiques de performance
    - Exporter les données en CSV ou Excel
    
    #### 📅 Calendrier
    - Vue timeline de toutes les missions
    - Filtrage par période
    - Export des plannings
    
    #### 📈 Statistiques
    - Rapports personnalisés par période
    - Exports multiples formats (CSV, Excel)
    - Graphiques interactifs
    - Analyse des performances
    
    #### 👥 Utilisateurs
    - Création de comptes avec rôles
    - Gestion des permissions (user, manager, admin)
    - Activation/Désactivation de comptes
    
    ### 🔐 Rôles et permissions
    
    - **👤 User** : Peut créer et consulter ses propres demandes
    - **👔 Manager** : Peut approuver/rejeter les demandes, gérer les ressources
    - **🔑 Admin** : Accès complet à toutes les fonctionnalités
    
    ### 💡 Astuces
    
    - Utilisez **CTRL + F** pour rechercher rapidement dans les tableaux
    - Les données sont **sauvegardées automatiquement** après chaque action
    - Les **exports** préservent tous les filtres actifs
    - L'**actualisation automatique** peut être activée sur le tableau de bord
    
    ### 🆘 Support
    
    En cas de problème :
    1. Contacter Moctar TALL (77 639 96 12)
    """)

# Informations de version et développeur
col_footer1, col_footer2, col_footer3 = st.columns([1, 2, 1])

with col_footer2:
    st.markdown("""
    <div style='text-align: center; padding: 20px; color: #6c757d;'>
        <p style='margin: 5px 0;'><strong>Système de Gestion des Missions</strong></p>
        <p style='margin: 5px 0; font-size: 12px;'>💻 Développé par <strong>@Moctar TALL</strong></p>
        <p style='margin: 5px 0; font-size: 10px;'>Tous droits réservés © 2026</p>
    </div>
    """, unsafe_allow_html=True)

# Mode debug (optionnel, à activer seulement en développement)
if os.getenv("DEBUG_MODE") == "true":
    with st.expander("🔧 Mode Debug (développeurs uniquement)"):
        st.write("**Session State:**")
        st.json(dict(st.session_state))
        
        st.write("**Database Status:**")
        st.write(f"Firebase connecté: {db is not None}")
        if firebase_error:
            st.error(f"Erreur Firebase: {firebase_error}")
            

# Auto-refresh pour le mode temps réel (si activé)
if page == "📊 Tableau de bord" and st.session_state.get('auto_refresh', False):
    import time
    time.sleep(60)
    st.rerun()
# Page admin améliorée - À ajouter dans app_admin.py
# Cette section vient après le code existant

# -------------------------
# PAGE: Suivi Excel (Nouvelle page)
# -------------------------
elif page == "📊 Suivi Style Excel":
    st.markdown("<h1 style='color: #2c3e50;'>📊 Suivi des Missions - Vue Excel</h1>", unsafe_allow_html=True)
    st.info("💡 Visualisation et gestion comme dans votre fichier Excel d'origine")
    
    try:
        # Filtres de période
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        with col_f1:
            start_date = st.date_input(
                "📅 Depuis",
                value=datetime.now().date() - timedelta(days=90)
            )
        
        with col_f2:
            end_date = st.date_input(
                "📅 Jusqu'à",
                value=datetime.now().date() + timedelta(days=30)
            )
        
        with col_f3:
            structure_filter = st.selectbox(
                "🏢 Structure",
                ["Toutes", "DAL/GPR/ESP", "DAL/DRP/EMI", "DAL/TCG", "Autre"]
            )
        
        with col_f4:
            etat_filter = st.selectbox(
                "📊 État",
                ["Tous", "Planifié", "En cours", "Fait", "Annulé"]
            )
        
        # Chargement des données
        if db is not None:
            from firebase_config import MissionRequestManager
            mgr = MissionRequestManager()
            
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
            
            requests = mgr.get_requests_by_period(start_dt, end_dt)
        else:
            requests = load_requests_mock()
        
        # Application des filtres
        if structure_filter != "Toutes":
            requests = [r for r in requests if r.get('structure', '').startswith(structure_filter)]
        
        if etat_filter != "Tous":
            requests = [r for r in requests if r.get('etat_mission') == etat_filter]
        
        # Statistiques rapides
        st.markdown("### 📈 Statistiques de la période")
        
        col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
        
        total = len(requests)
        planifies = sum(1 for r in requests if r.get('etat_mission') == 'Planifié')
        en_cours = sum(1 for r in requests if r.get('etat_mission') == 'En cours')
        faits = sum(1 for r in requests if r.get('etat_mission') == 'Fait')
        perdus = sum(1 for r in requests if r.get('perdu_m'))
        
        col_s1.metric("📦 Total", total)
        col_s2.metric("📅 Planifiés", planifies, delta=f"{(planifies/total*100) if total > 0 else 0:.0f}%")
        col_s3.metric("🔄 En cours", en_cours, delta=f"{(en_cours/total*100) if total > 0 else 0:.0f}%")
        col_s4.metric("✅ Réalisés", faits, delta=f"{(faits/total*100) if total > 0 else 0:.0f}%")
        col_s5.metric("❌ Perdus", perdus, delta=f"{(perdus/total*100) if total > 0 else 0:.0f}%")
        
        st.markdown("---")
        
        # Tableau style Excel
        if requests:
            import pandas as pd
            
            # Préparer les données pour affichage
            excel_data = []
            for r in requests:
                date_depart = r.get('date_depart')
                date_retour = r.get('date_retour')
                
                # Conversion des dates
                if isinstance(date_depart, str):
                    date_depart = pd.to_datetime(date_depart, errors='coerce')
                if isinstance(date_retour, str):
                    date_retour = pd.to_datetime(date_retour, errors='coerce')
                
                excel_data.append({
                    'ID': r.get('request_id', ''),
                    'Structure': r.get('structure', r.get('service_demandeur', '')),
                    'Action': r.get('action', r.get('motif_mission', ''))[:50] + '...' if len(r.get('action', r.get('motif_mission', ''))) > 50 else r.get('action', r.get('motif_mission', '')),
                    'Destination': r.get('destination', ''),
                    'Porteur': r.get('porteur', r.get('nom_demandeur', '')),
                    'Départ': date_depart.strftime('%d/%m/%Y') if pd.notna(date_depart) else '—',
                    'Retour': date_retour.strftime('%d/%m/%Y') if pd.notna(date_retour) else '—',
                    'Jours': r.get('nombre_jours', 0),
                    'Véh.': r.get('nombre_vehicules_valides', 0),
                    'Chauffeur': r.get('assigned_driver', '—')[:20],
                    'État': r.get('etat_mission', 'Planifié'),
                    'CR': r.get('compte_cr', r.get('compte_cr', '')),
                    '❌': '🔴' if r.get('perdu_m') else ''
                })
            
            df_excel = pd.DataFrame(excel_data)
            
            # Affichage avec coloration
            st.markdown("### 📋 Tableau de suivi")
            
            # Utiliser aggrid pour un meilleur affichage
            st.dataframe(
                df_excel,
                use_container_width=True,
                height=500,
                hide_index=True
            )
            
            # Actions en masse
            st.markdown("---")
            st.markdown("### ⚡ Actions groupées")
            
            col_act1, col_act2, col_act3, col_act4 = st.columns(4)
            
            with col_act1:
                selected_ids = st.multiselect(
                    "Sélectionner des missions",
                    options=df_excel['ID'].tolist(),
                    format_func=lambda x: f"{x} - {df_excel[df_excel['ID']==x]['Action'].values[0][:30]}..."
                )
            
            if selected_ids:
                with col_act2:
                    new_etat = st.selectbox(
                        "Changer l'état",
                        ["Planifié", "En cours", "Fait", "Annulé"]
                    )
                    
                    if st.button("📝 Appliquer", use_container_width=True):
                        if db is not None:
                            for req_id in selected_ids:
                                mgr.update_mission_status(req_id, new_etat)
                            show_toast(f"{len(selected_ids)} mission(s) mise(s) à jour", "success")
                        else:
                            show_toast(f"{len(selected_ids)} mission(s) mise(s) à jour (simulé)", "info")
                        st.rerun()
                
                with col_act3:
                    if st.button("❌ Marquer comme Perdues", use_container_width=True):
                        motif = st.text_input("Motif de perte")
                        if motif:
                            if db is not None:
                                for req_id in selected_ids:
                                    mgr.mark_as_lost(req_id, motif)
                                show_toast(f"{len(selected_ids)} mission(s) marquée(s) comme perdues", "warning")
                            else:
                                show_toast(f"{len(selected_ids)} mission(s) marquée(s) comme perdues (simulé)", "info")
                            st.rerun()
                
                with col_act4:
                    # Export sélection
                    df_selection = df_excel[df_excel['ID'].isin(selected_ids)]
                    csv = df_selection.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Exporter sélection",
                        data=csv,
                        file_name=f"selection_missions_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            # Exports complets
            st.markdown("---")
            st.markdown("### 📥 Exports")
            
            col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)
            
            with col_exp1:
                csv_all = df_excel.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📄 Export CSV",
                    data=csv_all,
                    file_name=f"suivi_missions_{start_date}_{end_date}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col_exp2:
                try:
                    xlsx = to_excel_bytes(df_excel, "Suivi Missions")
                    st.download_button(
                        "📊 Export Excel",
                        data=xlsx,
                        file_name=f"suivi_missions_{start_date}_{end_date}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Erreur export Excel: {e}")
            
            with col_exp3:
                # Export avec format Excel original
                if db is not None:
                    df_original = mgr.export_to_excel_format(requests)
                    xlsx_original = to_excel_bytes(df_original, "Suivi")
                    st.download_button(
                        "📋 Format Excel Original",
                        data=xlsx_original,
                        file_name=f"suivi_original_{start_date}_{end_date}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            
            with col_exp4:
                # Impression PDF (placeholder)
                st.button("🖨️ Imprimer (PDF)", use_container_width=True, disabled=True)
                st.caption("Fonctionnalité à venir")
        
        else:
            st.info("🔍 Aucune mission trouvée pour cette période")
        
        # Statistiques par structure
        if requests and db is not None:
            st.markdown("---")
            st.markdown("### 📊 Répartition par structure")
            
            stats = mgr.get_statistics_by_structure(start_dt, end_dt)
            
            stats_data = []
            for structure, data in stats.items():
                stats_data.append({
                    'Structure': structure,
                    'Total': data['total_missions'],
                    'Réalisées': data['missions_realisees'],
                    'Planifiées': data['missions_planifiees'],
                    'Perdues': data['missions_perdues'],
                    'Total jours': data['total_jours'],
                    'Véhicules': data['total_vehicules'],
                    'Taux réalisation': f"{(data['missions_realisees']/data['total_missions']*100) if data['total_missions'] > 0 else 0:.1f}%"
                })
            
            df_stats = pd.DataFrame(stats_data)
            
            # Graphique
            import plotly.express as px
            
            fig = px.bar(
                df_stats,
                x='Structure',
                y=['Réalisées', 'Planifiées', 'Perdues'],
                title="Répartition des missions par structure",
                barmode='group',
                color_discrete_map={
                    'Réalisées': '#28a745',
                    'Planifiées': '#ffc107',
                    'Perdues': '#dc3545'
                }
            )
            fig.update_layout(height=400, template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
            
            # Tableau des stats
            st.dataframe(
                df_stats,
                use_container_width=True,
                hide_index=True
            )
        
        # Import Excel
        st.markdown("---")
        with st.expander("📤 Importer un fichier Excel existant"):
            st.info("💡 Importez votre ancien fichier Excel pour migrer les données dans le système")
            
            uploaded_file = st.file_uploader(
                "Sélectionner votre fichier Excel",
                type=['xlsx', 'xls'],
                help="Le fichier doit contenir les colonnes: Structure, Action, Destination, etc."
            )
            
            if uploaded_file:
                if st.button("🚀 Lancer l'import", type="primary"):
                    try:
                        if db is not None:
                            result = import_excel_to_firebase(uploaded_file)
                            
                            st.success(f"✅ {result['imported']} mission(s) importée(s) avec succès")
                            
                            if result['errors']:
                                st.warning(f"⚠️ {len(result['errors'])} erreur(s) rencontrée(s)")
                                with st.expander("Voir les erreurs"):
                                    for error in result['errors']:
                                        st.text(error)
                        else:
                            st.error("❌ Firebase requis pour l'import")
                    except Exception as e:
                        st.error(f"❌ Erreur lors de l'import: {e}")
    
    except Exception as e:
        show_toast(f"Erreur: {e}", "error")
        st.exception(e)
