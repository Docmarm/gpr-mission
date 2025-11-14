from __future__ import annotations
import streamlit as st
from datetime import datetime, timedelta
import json
import os
import requests
from typing import Dict, List
import pandas as pd

# (déplacé en haut du fichier)

# Configuration de la page
st.set_page_config(
    page_title="Gestion des Missions", 
    layout="wide",
    page_icon="🚗",
    initial_sidebar_state="collapsed"
)

# CSS personnalisé pour une belle page d'accueil
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 3rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .main-header h1 {
        font-size: 3rem;
        margin-bottom: 0.5rem;
        font-weight: bold;
    }
    
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    .option-card {
        background: white;
        border-radius: 15px;
        padding: 2.5rem;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        cursor: pointer;
        border: 2px solid transparent;
        height: 100%;
    }
    
    .option-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        border-color: #667eea;
    }
    
    .option-icon {
        font-size: 5rem;
        margin-bottom: 1rem;
    }
    
    .option-title {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    
    .option-description {
        color: #666;
        font-size: 1.1rem;
        line-height: 1.6;
    }
    
    .feature-list {
        text-align: left;
        margin-top: 1.5rem;
        padding-left: 1rem;
    }
    
    .feature-item {
        margin: 0.5rem 0;
        color: #555;
    }
    
    .footer {
        text-align: center;
        margin-top: 4rem;
        padding: 2rem;
        color: #666;
        border-top: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation de la session
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = None

# En-tête principal
st.markdown("""
<div class="main-header">
    <h1>🚗 Gestion des Missions</h1>
    <p>Plateforme digitale de gestion des véhicules et missions GPR/EMI</p>
</div>
""", unsafe_allow_html=True)

# Lien discret vers l'interface admin dans la sidebar
if st.sidebar.button("⚙️ Admin", key="sidebar_admin"):
    st.switch_page("pages/admin.py")

# Si aucun mode n'est sélectionné, afficher les options
if st.session_state.app_mode is None:
    st.markdown("## 👋 Bienvenue ! Que souhaitez-vous faire aujourd'hui ?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="option-card">
            <div class="option-icon">📋</div>
            <div class="option-title">Demander une Mission</div>
            <div class="option-description">
                Interface client pour soumettre et suivre vos demandes de mission
            </div>
            <div class="feature-list">
                <div class="feature-item">✅ Vérifier les disponibilités</div>
                <div class="feature-item">✅ Soumettre une demande</div>
                <div class="feature-item">✅ Suivre votre demande</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Demander une Mission", type="primary", use_container_width=True, key="btn_demande"):
            st.session_state.app_mode = "demande"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="option-card">
            <div class="option-icon">🗺️</div>
            <div class="option-title">Planifier un Itinéraire</div>
            <div class="option-description">
                Outil de planification d'itinéraire et optimisation de missions terrain
            </div>
            <div class="feature-list">
                <div class="feature-item">✅ Optimisation d'itinéraire</div>
                <div class="feature-item">✅ Calcul des distances</div>
                <div class="feature-item">✅ Planning détaillé</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Planifier un Itinéraire", type="primary", use_container_width=True, key="btn_planif"):
            st.switch_page("pages/mission.py")

    


    # Footer
    st.markdown(
        """
        <div class="footer">
            <p>🏢 Service GPR/EMI - Sonatel</p>
            <p>💻 Développé par @Moctar TALL • Tous droits réservés</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -------------------------
# Adja (IA) — Intégration DeepSeek
# -------------------------
# (Conseiller Adja retiré)
    

# Mode Demande de Mission
if st.session_state.app_mode == "demande":
    # Bouton retour
    if st.button("⬅️ Retour à l'accueil"):
        st.session_state.app_mode = None
        st.rerun()
    
    st.title("📋 Demande de Mission")
    
    # Onglets pour l'interface client
    tab_disponibilite, tab_demande, tab_suivi = st.tabs([
        "📅 Vérifier Disponibilités", 
        "📝 Nouvelle Demande", 
        "🔍 Suivre mes Demandes"
    ])
    
    with tab_disponibilite:
        st.header("📅 Calendrier des Disponibilités")
        st.info("💡 Consultez les créneaux disponibles avant de faire votre demande")
        
        col_date1, col_date2 = st.columns(2)
        
        with col_date1:
            date_debut_check = st.date_input(
                "Date de départ souhaitée",
                value=datetime.now().date(),
                min_value=datetime.now().date()
            )
        
        with col_date2:
            date_fin_check = st.date_input(
                "Date de retour prévue",
                value=datetime.now().date() + timedelta(days=1),
                min_value=datetime.now().date()
            )
        
        if st.button("🔍 Vérifier la disponibilité", type="primary"):
            try:
                from firebase_config import CalendarManager
                start_dt = datetime.combine(date_debut_check, datetime.min.time())
                end_dt = datetime.combine(date_fin_check, datetime.max.time())
                cal = CalendarManager()
                availability = cal.check_availability(start_dt, end_dt)
                if availability.get("available"):
                    st.success("✅ Des véhicules et chauffeurs sont disponibles pour cette période")
                else:
                    st.warning("⚠️ Aucun créneau disponible sur cette période")
                st.markdown("### 🚗 Véhicules disponibles")
                vehicles = availability.get("vehicles", [])
                types = {}
                for v in vehicles:
                    t = v.get("type", "Indifférent")
                    types[t] = types.get(t, 0) + 1
                col_v1, col_v2, col_v3 = st.columns(3)
                metric_items = list(types.items())
                m1 = metric_items[0] if len(metric_items) > 0 else ("Berline", 0)
                m2 = metric_items[1] if len(metric_items) > 1 else ("Station-Wagon", 0)
                m3 = metric_items[2] if len(metric_items) > 2 else ("4x4", 0)
                with col_v1:
                    st.metric(str(m1[0]), f"{m1[1]} disponibles")
                with col_v2:
                    st.metric(str(m2[0]), f"{m2[1]} disponibles")
                with col_v3:
                    st.metric(str(m3[0]), f"{m3[1]} disponibles")
                st.markdown("### 👨‍✈️ Chauffeurs disponibles")
                st.metric("Chauffeurs", availability.get("drivers_count", 0))
            except Exception as e:
                st.error(f"❌ Vérification impossible: {e}")
    
# Formulaire de demande amélioré - À remplacer dans app.py (tab_demande)

    with tab_demande:
        st.header("📝 Nouvelle Demande de Mission")
        st.info("💡 Tous les champs marqués d'un (*) sont obligatoires")
        
        with st.form("formulaire_demande"):
            # SECTION 1: Structure et Organisation
            st.subheader("🏢 Structure et Organisation")
            
            col_org1, col_org2, col_org3 = st.columns(3)
            
            with col_org1:
                structure = st.text_input(
                    "Structure/Direction*",
                    placeholder="Ex: DAL/GPR/ESP",
                    help="Saisissez directement votre direction/structure"
                )
            
            with col_org2:
                compte_cr = st.text_input(
                    "Compte C.R. / Centre de Coût*",
                    placeholder="Ex: L2300",
                    help="Compte de refacturation"
                )
            
            with col_org3:
                date_expression_besoin = st.date_input(
                    "Date d'expression du besoin*",
                    value=datetime.now().date(),
                    help="Date à laquelle le besoin a été exprimé"
                )
            
            st.divider()
            
            # SECTION 2: Demandeur et Porteur
            st.subheader("👤 Informations Demandeur")
            
            col_dem1, col_dem2, col_dem3 = st.columns(3)
            
            with col_dem1:
                nom_demandeur = st.text_input(
                    "Nom et Prénom*",
                    placeholder="Ex: Moctar TALL"
                )
            
            with col_dem2:
                email_demandeur = st.text_input(
                    "Email*",
                    placeholder="prenom.nom@sonatel.sn"
                )
            
            with col_dem3:
                telephone_demandeur = st.text_input(
                    "Téléphone*",
                    placeholder="+221 77 XXX XX XX"
                )
            
            col_dem4, col_dem5 = st.columns(2)
            
            with col_dem4:
                fonction_demandeur = st.text_input(
                    "Fonction",
                    placeholder="Ex: Ingénieur Projet"
                )
            
            with col_dem5:
                porteur = st.text_input(
                    "Porteur du projet/action*",
                    placeholder="Nom du responsable du projet",
                    help="Personne responsable de l'action/projet"
                )
            
            st.divider()
            
            # SECTION 3: Détails de la Mission
            st.subheader("🚗 Détails de la Mission")
            
            action_motif = st.text_area(
                "Action / Motif de la mission*",
                placeholder="Décrivez précisément l'action à mener et le motif de la mission...",
                height=100,
                help="Soyez précis sur l'objet de votre mission"
            )
            
            col_miss1, col_miss2, col_miss3 = st.columns(3)
            
            with col_miss1:
                destination = st.text_input(
                    "Destination(s)*",
                    placeholder="Ex: Thiès, Saint-Louis, Louga"
                )
            
            with col_miss2:
                date_depart = st.date_input(
                    "Date de départ*",
                    value=datetime.now().date(),
                    min_value=datetime.now().date(),
                    help="Date de début de la mission"
                )
            
            with col_miss3:
                heure_depart = st.time_input(
                    "Heure de départ souhaitée*",
                    value=datetime.strptime("08:00", "%H:%M").time()
                )
            
            col_miss4, col_miss5, col_miss6 = st.columns(3)
            
            with col_miss4:
                date_retour = st.date_input(
                    "Date de retour*",
                    value=datetime.now().date() + timedelta(days=1),
                    min_value=datetime.now().date(),
                    help="Date de fin de la mission"
                )
            
            with col_miss5:
                # Calcul automatique du nombre de jours
                if date_depart and date_retour:
                    nombre_jours = (date_retour - date_depart).days + 1
                    st.metric(
                        "Nombre de jours",
                        nombre_jours,
                        help="Calculé automatiquement"
                    )
                else:
                    nombre_jours = 0
            
            with col_miss6:
                nombre_vehicules = st.number_input(
                    "Nombre de véhicules*",
                    min_value=1,
                    max_value=10,
                    value=1,
                    help="Nombre de véhicules nécessaires"
                )
            
            col_miss7, col_miss8, col_miss9 = st.columns(3)
            
            with col_miss7:
                nb_passagers = st.number_input(
                    "Nombre de passagers*",
                    min_value=1,
                    max_value=50,
                    value=1
                )
            
            with col_miss8:
                type_vehicule = st.selectbox(
                    "Type de véhicule souhaité",
                    ["Indifférent", "Berline", "Station-Wagon", "4x4", "Minibus", "Pick-up"]
                )
            
            with col_miss9:
                avec_chauffeur = st.checkbox(
                    "Avec chauffeur",
                    value=True,
                    help="Cochez si vous avez besoin d'un chauffeur"
                )
            
            st.divider()
            
            # SECTION 4: Priorité et Compléments
            st.subheader("⚡ Priorité et Informations complémentaires")
            
            col_prio1, col_prio2 = st.columns(2)
            
            with col_prio1:
                urgence = st.select_slider(
                    "Niveau d'urgence",
                    options=["Normal", "Urgent", "Très urgent"],
                    value="Normal",
                    help="Indiquez le niveau de priorité de votre demande"
                )
            
            with col_prio2:
                type_mission = st.selectbox(
                    "Type de mission",
                    [
                        "Visite terrain",
                        "Déplacement administratif",
                        "Formation",
                        "Maintenance",
                        "Installation",
                        "Réunion externe",
                        "Autre"
                    ]
                )
            
            notes_supplementaires = st.text_area(
                "Notes supplémentaires / Contraintes particulières",
                placeholder="Informations complémentaires, contraintes horaires, besoins spécifiques...",
                height=80
            )
            
            st.divider()
            
            # SECTION 5: Documents
            st.subheader("📎 Documents justificatifs")
            
            col_doc1, col_doc2 = st.columns(2)
            
            with col_doc1:
                ordre_mission = st.file_uploader(
                    "Ordre de mission (optionnel)",
                    type=["pdf", "jpg", "jpeg", "png"],
                    help="Joindre votre ordre de mission si disponible"
                )
            
            with col_doc2:
                autres_docs = st.file_uploader(
                    "Autres documents (optionnel)",
                    type=["pdf", "jpg", "jpeg", "png", "doc", "docx"],
                    accept_multiple_files=True,
                    help="Programme de visite, liste participants, etc."
                )
            
            st.divider()
            
            # Récapitulatif avant soumission
            with st.expander("📋 Récapitulatif de votre demande", expanded=False):
                st.markdown(f"""
                **Structure:** {structure}  
                **Porteur:** {porteur}  
                **Demandeur:** {nom_demandeur} ({email_demandeur})  
                **Action:** {action_motif[:100]}...  
                **Destination:** {destination}  
                **Période:** Du {date_depart} au {date_retour} ({nombre_jours} jour(s))  
                **Véhicules:** {nombre_vehicules} véhicule(s), {nb_passagers} passager(s)  
                **Type:** {type_vehicule}  
                **Avec chauffeur:** {'Oui' if avec_chauffeur else 'Non'}  
                **Urgence:** {urgence}  
                **Compte CR:** {compte_cr}
                """)
            
            # Validation et soumission
            st.markdown("---")
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            
            with col_btn2:
                submitted = st.form_submit_button(
                    "📤 Soumettre la demande",
                    type="primary",
                    use_container_width=True
                )
            
            if submitted:
                # Validation des champs obligatoires
                required_fields = {
                    'Structure': structure,
                    'Nom': nom_demandeur,
                    'Email': email_demandeur,
                    'Téléphone': telephone_demandeur,
                    'Porteur': porteur,
                    'Action/Motif': action_motif,
                    'Destination': destination,
                    'Compte CR': compte_cr
                }
                
                missing_fields = [k for k, v in required_fields.items() if not str(v).strip()]
                
                if missing_fields:
                    st.error(f"❌ Champs obligatoires manquants: {', '.join(missing_fields)}")
                else:
                    try:
                        from firebase_config import MissionRequestManager
                        
                        req_mgr = MissionRequestManager()
                        
                        # Préparer les données
                        request_data = {
                            # Champs Excel
                            'structure': structure.strip(),
                            'action': action_motif.strip(),
                            'porteur': porteur.strip(),
                            'date_expression_besoin': datetime.combine(
                                date_expression_besoin,
                                datetime.min.time()
                            ),
                            'nombre_vehicules_valides': int(nombre_vehicules),
                            'compte_cr': compte_cr.strip(),
                            'etat_mission': 'Planifié',
                            
                            # Champs standard
                            'nom_demandeur': nom_demandeur.strip(),
                            'email_demandeur': email_demandeur.strip().lower(),
                            'telephone_demandeur': telephone_demandeur.strip(),
                            'service_demandeur': structure.strip(),
                            'fonction_demandeur': fonction_demandeur.strip(),
                            'motif_mission': action_motif.strip(),
                            'destination': destination.strip(),
                            'date_depart': datetime.combine(date_depart, heure_depart),
                            'date_retour': datetime.combine(
                                date_retour,
                                datetime.strptime("23:59", "%H:%M").time()
                            ),
                            'nb_passagers': int(nb_passagers),
                            'type_vehicule': type_vehicule,
                            'urgence': urgence,
                            'avec_chauffeur': bool(avec_chauffeur),
                            'type_mission': type_mission,
                            'notes': notes_supplementaires.strip()
                        }
                        
                        # Créer la demande
                        request_id = req_mgr.create_request(request_data)
                        
                        # Upload des documents
                        docs_uploaded = []
                        if ordre_mission is not None:
                            try:
                                att = req_mgr.upload_attachment(request_id, ordre_mission)
                                docs_uploaded.append("Ordre de mission")
                            except Exception as e:
                                st.warning(f"⚠️ Impossible de charger l'ordre de mission: {e}")
                        
                        if autres_docs:
                            for doc in autres_docs:
                                try:
                                    req_mgr.upload_attachment(request_id, doc)
                                    docs_uploaded.append(doc.name)
                                except Exception as e:
                                    st.warning(f"⚠️ Impossible de charger {doc.name}: {e}")
                        
                        # Notification de succès
                        st.success("✅ Votre demande a été soumise avec succès !")
                        st.balloons()
                        
                        # Affichage du numéro de suivi
                        st.info(f"""
                        ### 🎫 Numéro de suivi: `{request_id}`
                        
                        **Conservez ce numéro** pour suivre l'état de votre demande.
                        
                        📧 Un email de confirmation va vous être envoyé à: {email_demandeur}
                        """)
                        
                        if docs_uploaded:
                            st.success(f"📎 Documents chargés: {', '.join(docs_uploaded)}")
                        
                        # Récapitulatif final
                        with st.expander("📋 Détails de votre demande", expanded=True):
                            col_r1, col_r2 = st.columns(2)
                            
                            with col_r1:
                                st.markdown(f"""
                                **📌 Identification**  
                                - Numéro: `{request_id}`  
                                - Structure: {structure}  
                                - Porteur: {porteur}  
                                - Demandeur: {nom_demandeur}  
                                - Email: {email_demandeur}  
                                - Compte CR: {compte_cr}
                                
                                **🚗 Mission**  
                                - Action: {action_motif[:80]}...  
                                - Destination: {destination}  
                                - Type: {type_mission}
                                """)
                            
                            with col_r2:
                                st.markdown(f"""
                                **📅 Planning**  
                                - Expression besoin: {date_expression_besoin.strftime('%d/%m/%Y')}  
                                - Départ: {date_depart.strftime('%d/%m/%Y')} à {heure_depart.strftime('%H:%M')}  
                                - Retour: {date_retour.strftime('%d/%m/%Y')}  
                                - Durée: {nombre_jours} jour(s)
                                
                                **🚙 Ressources**  
                                - Véhicules: {nombre_vehicules}  
                                - Passagers: {nb_passagers}  
                                - Type souhaité: {type_vehicule}  
                                - Avec chauffeur: {'Oui' if avec_chauffeur else 'Non'}
                                """)
                        
                        # Prochaines étapes
                        st.info("""
                        ### 📍 Prochaines étapes
                        
                        1. ✅ Votre demande est en cours de traitement
                        2. 👀 Un administrateur va l'examiner sous 24-48h
                        3. 📧 Vous recevrez une notification par email
                        4. 🔍 Suivez l'état dans l'onglet "Suivre mes Demandes"
                        """)
                        
                    except Exception as e:
                        st.error(f"❌ Erreur lors de l'enregistrement: {e}")
                        st.exception(e)
        
    with tab_suivi:
        st.header("🔍 Suivre mes Demandes")
        tracking_id = st.text_input("Numéro de suivi", placeholder="Ex: DM-20250114-153045")
        if st.button("🔍 Rechercher", type="primary"):
            try:
                from firebase_config import MissionRequestManager
                req_mgr = MissionRequestManager()
                req = req_mgr.get_request(tracking_id.strip())
                if not req:
                    st.info("💡 Aucune demande trouvée avec ce numéro")
                else:
                    with st.expander(f"📄 Détails {req.get('request_id','')}", expanded=True):
                        st.write(f"**Statut:** {req.get('status','')}")
                        st.write(f"**Demandeur:** {req.get('nom_demandeur','')} ({req.get('email_demandeur','')})")
                        st.write(f"**Service:** {req.get('service_demandeur','')}")
                        st.write(f"**Période:** {req.get('date_depart')} au {req.get('date_retour')}")
                        st.write(f"**Destination:** {req.get('destination','')}")
                        st.write(f"**Passagers:** {req.get('nb_passagers',1)}")
                        st.write(f"**Véhicule souhaité:** {req.get('type_vehicule','Indifférent')}")
                        atts = req.get('attachments', []) or []
                        if atts:
                            st.markdown("**Documents:**")
                            for a in atts:
                                st.markdown(f"- [{a.get('name','Pièce jointe')}]({a.get('url','')})")
            except Exception as e:
                st.error(f"❌ Recherche impossible: {e}")
        st.divider()
        st.subheader("📋 Mes demandes réelles")
        email_lookup = st.text_input("Votre email", placeholder="Ex: moctar.tall@sonatel.sn")
        if st.button("🔎 Lister mes demandes"):
            try:
                from firebase_config import MissionRequestManager
                req_mgr = MissionRequestManager()
                reqs = req_mgr.get_user_requests(email_lookup.strip()) if email_lookup else []
                if not reqs:
                    st.info("Aucune demande trouvée")
                else:
                    rows = []
                    for r in reqs:
                        rows.append({
                            "Numéro": r.get("request_id",""),
                            "Statut": r.get("status",""),
                            "Départ": r.get("date_depart",""),
                            "Retour": r.get("date_retour",""),
                            "Destination": r.get("destination",""),
                            "Type": r.get("type_vehicule","Indifférent")
                        })
                    import pandas as pd
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"❌ Chargement impossible: {e}")

elif st.session_state.app_mode == "planification":
    # Bouton retour
    if st.button("⬅️ Retour à l'accueil"):
        st.session_state.app_mode = None
        st.rerun()
    
    st.title("🗺️ Planificateur de Mission")
    st.info("💡 Votre outil de planification d'itinéraire sera chargé ici")
    st.markdown("**Note:** Intégrez votre code existant de planification (mission.py) dans cette section")
    
    # TODO: Intégrer le code de mission.py ici
    st.code("""
    # Votre code de planification existant sera intégré ici
    # Vous pouvez importer le fichier mission.py ou copier le code pertinent
    """, language="python")
# Amélioration du système de demandes de mission - Intégration Excel
# À ajouter dans firebase_config.py

class MissionRequestManager:
    """Gestionnaire amélioré des demandes de mission - Version Excel intégrée"""
    
    def __init__(self):
        self.db = initialize_firebase()
        self.requests_collection = self.db.collection('mission_requests')
        self.vehicles_collection = self.db.collection('vehicles')
        self.drivers_collection = self.db.collection('drivers')
    
    def create_request(self, request_data: Dict) -> str:
        """
        Crée une nouvelle demande de mission avec tous les champs Excel
        """
        # Générer un ID unique
        request_id = f"DM-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Calcul automatique du nombre de jours
        date_depart = request_data.get('date_depart')
        date_retour = request_data.get('date_retour')
        
        if isinstance(date_depart, str):
            date_depart = datetime.fromisoformat(date_depart)
        if isinstance(date_retour, str):
            date_retour = datetime.fromisoformat(date_retour)
        
        nombre_jours = (date_retour - date_depart).days + 1 if date_depart and date_retour else 0
        
        # Enrichir les données avec les nouveaux champs Excel
        request_data.update({
            'request_id': request_id,
            'status': 'pending',  # pending, approved, rejected, cancelled
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            
            # Champs Excel ajoutés
            'structure': request_data.get('structure', request_data.get('service_demandeur', '')),
            'action': request_data.get('action', request_data.get('motif_mission', '')),
            'porteur': request_data.get('porteur', request_data.get('nom_demandeur', '')),
            'date_expression_besoin': request_data.get('date_expression_besoin', datetime.now()),
            'nombre_jours': nombre_jours,
            'nombre_vehicules_valides': request_data.get('nombre_vehicules_valides', 1),
            'etat_mission': request_data.get('etat_mission', 'Planifié'),  # Planifié, En cours, Fait
            'perdu_m': request_data.get('perdu_m', False),  # Indicateur de perte
            'motif_perte': request_data.get('motif_perte', ''),  # Raison si mission perdue
            
            # Champs existants
            'assigned_vehicle': None,
            'assigned_driver': None,
            'admin_notes': '',
            
            # Nouveaux champs de validation
            'validated_by': None,
            'validated_at': None,
            'validation_notes': ''
        })
        
        # Enregistrer dans Firestore
        self.requests_collection.document(request_id).set(request_data)
        
        return request_id
    
    def update_mission_status(self, request_id: str, etat_mission: str):
        """Met à jour l'état de la mission (Planifié/En cours/Fait)"""
        self.requests_collection.document(request_id).update({
            'etat_mission': etat_mission,
            'updated_at': datetime.now(),
            'completed_at': datetime.now() if etat_mission == 'Fait' else None
        })
    
    def mark_as_lost(self, request_id: str, motif_perte: str):
        """Marque une mission comme perdue/annulée"""
        self.requests_collection.document(request_id).update({
            'perdu_m': True,
            'motif_perte': motif_perte,
            'status': 'cancelled',
            'updated_at': datetime.now()
        })
    
    def get_requests_by_structure(self, structure: str) -> List[Dict]:
        """Récupère les demandes par structure (comme dans Excel)"""
        requests = self.requests_collection.where('structure', '==', structure).stream()
        return [{'id': req.id, **req.to_dict()} for req in requests]
    
    def get_requests_by_period(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Récupère les demandes pour une période donnée"""
        requests = self.requests_collection.where(
            'date_depart', '>=', start_date
        ).where(
            'date_depart', '<=', end_date
        ).order_by('date_depart').stream()
        
        return [{'id': req.id, **req.to_dict()} for req in requests]
    
    def export_to_excel_format(self, requests: List[Dict]) -> pd.DataFrame:
        """Exporte les demandes au format Excel original"""
        import pandas as pd
        
        excel_data = []
        for req in requests:
            excel_data.append({
                'Structure': req.get('structure', ''),
                'Action': req.get('action', ''),
                'Destination': req.get('destination', ''),
                'Date expression besoin': req.get('date_expression_besoin', ''),
                'Porteur': req.get('porteur', ''),
                'DATE DEPART': req.get('date_depart', ''),
                'DATE RETOUR': req.get('date_retour', ''),
                'Nombre de jours': req.get('nombre_jours', 0),
                'Nombre de véhicules validés': req.get('nombre_vehicules_valides', 0),
                'Véhicules affectés': req.get('assigned_vehicle', ''),
                'Chauffeur(s) désigné(s) ou Utilisateur': req.get('assigned_driver', ''),
                'PERDU/M': 'OUI' if req.get('perdu_m') else '',
                'CR': req.get('compte_cr', ''),
                'Etat Mission': req.get('etat_mission', 'Planifié')
            })
        
        return pd.DataFrame(excel_data)
    
    def get_statistics_by_structure(self, start_date: datetime, end_date: datetime) -> Dict:
        """Génère des statistiques par structure (comme dans votre Excel)"""
        requests = self.get_requests_by_period(start_date, end_date)
        
        stats = {}
        for req in requests:
            structure = req.get('structure', 'Non spécifié')
            if structure not in stats:
                stats[structure] = {
                    'total_missions': 0,
                    'missions_realisees': 0,
                    'missions_planifiees': 0,
                    'missions_perdues': 0,
                    'total_jours': 0,
                    'total_vehicules': 0
                }
            
            stats[structure]['total_missions'] += 1
            stats[structure]['total_jours'] += req.get('nombre_jours', 0)
            stats[structure]['total_vehicules'] += req.get('nombre_vehicules_valides', 0)
            
            if req.get('perdu_m'):
                stats[structure]['missions_perdues'] += 1
            elif req.get('etat_mission') == 'Fait':
                stats[structure]['missions_realisees'] += 1
            elif req.get('etat_mission') == 'Planifié':
                stats[structure]['missions_planifiees'] += 1
        
        return stats
    
    def update_request_status_by_request_id(self, request_id: str, status: str):
        """Mise à jour rapide du statut par request_id"""
        docs = list(self.requests_collection.where('request_id', '==', request_id).stream())
        if docs:
            doc = docs[0]
            doc.reference.update({
                'status': status,
                'updated_at': datetime.now()
            })


# Nouvelles fonctions utilitaires pour l'interface admin

def calculate_mission_duration(date_depart, date_retour):
    """Calcule automatiquement le nombre de jours"""
    if isinstance(date_depart, str):
        date_depart = datetime.fromisoformat(date_depart)
    if isinstance(date_retour, str):
        date_retour = datetime.fromisoformat(date_retour)
    
    return (date_retour - date_depart).days + 1


def get_color_by_status(etat_mission: str) -> str:
    """Retourne une couleur selon l'état (comme dans Excel)"""
    colors = {
        'Planifié': '#FFF3CD',  # Jaune
        'En cours': '#D1ECF1',  # Bleu clair
        'Fait': '#D4EDDA',      # Vert
        'Annulé': '#F8D7DA'     # Rouge
    }
    return colors.get(etat_mission, '#FFFFFF')


def generate_monthly_report(year: int, month: int) -> pd.DataFrame:
    """Génère un rapport mensuel style Excel"""
    from firebase_config import MissionRequestManager
    
    mgr = MissionRequestManager()
    start_date = datetime(year, month, 1)
    
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    requests = mgr.get_requests_by_period(start_date, end_date)
    return mgr.export_to_excel_format(requests)


# Fonction pour l'import Excel vers Firebase
def import_excel_to_firebase(excel_file):
    """Importe un fichier Excel existant dans Firebase"""
    import pandas as pd
    from firebase_config import MissionRequestManager
    
    df = pd.read_excel(excel_file)
    mgr = MissionRequestManager()
    
    imported_count = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            request_data = {
                'structure': row.get('Structure', ''),
                'action': row.get('Action', ''),
                'destination': row.get('Destination', ''),
                'porteur': row.get('Porteur', ''),
                'date_expression_besoin': pd.to_datetime(row.get('Date expression besoin')),
                'date_depart': pd.to_datetime(row.get('DATE DEPART')),
                'date_retour': pd.to_datetime(row.get('DATE RETOUR')),
                'nombre_vehicules_valides': int(row.get('Nombre de véhicules validés', 1)),
                'compte_cr': row.get('CR', ''),
                'etat_mission': row.get('Etat Mission', 'Planifié'),
                'perdu_m': row.get('PERDU/M', '') == 'OUI',
                
                # Champs obligatoires
                'nom_demandeur': row.get('Porteur', ''),
                'email_demandeur': f"{row.get('Porteur', 'unknown')}@sonatel.sn".lower().replace(' ', '.'),
                'service_demandeur': row.get('Structure', ''),
                'motif_mission': row.get('Action', ''),
                'nb_passagers': 1,
                'type_vehicule': 'Indifférent',
                'avec_chauffeur': True
            }
            
            mgr.create_request(request_data)
            imported_count += 1
            
        except Exception as e:
            errors.append(f"Ligne {idx + 2}: {str(e)}")
    
    return {
        'imported': imported_count,
        'errors': errors
    }
