"""
Configuration Firebase et Backend pour la gestion des missions
"""

import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
from datetime import datetime, timedelta
import streamlit as st
import json
from typing import Dict, List, Optional
import os

try:
    FIREBASE_CONFIG = st.secrets.get("firebase", {})
except Exception:
    FIREBASE_CONFIG = {
        "apiKey": os.getenv("FIREBASE_API_KEY", ""),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
        "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", ""),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
        "appId": os.getenv("FIREBASE_APP_ID", ""),
        "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID", "")
    }

# Initialisation Firebase (à faire une seule fois)
def initialize_firebase():
    if not firebase_admin._apps:
        cred_dict = {
            "type": st.secrets["firebase_admin"]["type"],
            "project_id": st.secrets["firebase_admin"]["project_id"],
            "private_key_id": st.secrets["firebase_admin"]["private_key_id"],
            "private_key": st.secrets["firebase_admin"]["private_key"].replace('\\n', '\n'),
            "client_email": st.secrets["firebase_admin"]["client_email"],
            "client_id": st.secrets["firebase_admin"]["client_id"],
            "auth_uri": st.secrets["firebase_admin"]["auth_uri"],
            "token_uri": st.secrets["firebase_admin"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase_admin"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["firebase_admin"]["client_x509_cert_url"]
        }
        cred = credentials.Certificate(cred_dict)
        
        options = {}
        bucket = FIREBASE_CONFIG.get("storageBucket")
        if bucket:
            options["storageBucket"] = bucket
        firebase_admin.initialize_app(cred, options or None)
    return firestore.client()

# ==========================================
# GESTION DES DEMANDES DE MISSION
# ==========================================

class MissionRequestManager:
    """Gestionnaire des demandes de mission"""
    
    def __init__(self):
        self.db = initialize_firebase()
        self.requests_collection = self.db.collection('mission_requests')
        self.vehicles_collection = self.db.collection('vehicles')
        self.drivers_collection = self.db.collection('drivers')
    
    def create_request(self, request_data: Dict) -> str:
        """
        Crée une nouvelle demande de mission
        
        Args:
            request_data: Dictionnaire contenant les informations de la demande
        
        Returns:
            request_id: ID unique de la demande
        """
        # Générer un ID unique
        request_id = f"DM-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Enrichir les données
        request_data.update({
            'request_id': request_id,
            'status': 'pending',  # pending, approved, rejected, cancelled
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'assigned_vehicle': None,
            'assigned_driver': None,
            'admin_notes': ''
        })
        
        # Enregistrer dans Firestore
        self.requests_collection.document(request_id).set(request_data)
        
        return request_id
    
    def get_request(self, request_id: str) -> Optional[Dict]:
        """Récupère une demande par son ID"""
        doc = self.requests_collection.document(request_id).get()
        return doc.to_dict() if doc.exists else None
    
    def get_user_requests(self, user_email: str) -> List[Dict]:
        """Récupère toutes les demandes d'un utilisateur"""
        requests = self.requests_collection.where('email_demandeur', '==', user_email).stream()
        return [{'id': req.id, **req.to_dict()} for req in requests]
    
    def get_all_requests(self, status: Optional[str] = None) -> List[Dict]:
        """Récupère toutes les demandes (avec filtre optionnel par statut)"""
        query = self.requests_collection
        
        if status:
            query = query.where('status', '==', status)
        
        requests = query.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        return [{'id': req.id, **req.to_dict()} for req in requests]
    
    def update_request_status(self, request_id: str, status: str, admin_notes: str = ''):
        """Met à jour le statut d'une demande"""
        self.requests_collection.document(request_id).update({
            'status': status,
            'admin_notes': admin_notes,
            'updated_at': datetime.now()
        })
    
    def assign_vehicle_driver(self, request_id: str, vehicle_id: str, driver_id: str):
        """Assigne un véhicule et un chauffeur à une demande"""
        self.requests_collection.document(request_id).update({
            'assigned_vehicle': vehicle_id,
            'assigned_driver': driver_id,
            'status': 'approved',
            'updated_at': datetime.now()
        })
    
    def cancel_request(self, request_id: str, reason: str = ''):
        """Annule une demande"""
        self.requests_collection.document(request_id).update({
            'status': 'cancelled',
            'cancellation_reason': reason,
            'updated_at': datetime.now()
        })

    def upload_attachment(self, request_id: str, uploaded_file) -> Dict:
        project_id = None
        try:
            project_id = st.secrets.get('firebase_admin', {}).get('project_id')
        except Exception:
            project_id = (FIREBASE_CONFIG or {}).get('projectId')
        bucket_name = (FIREBASE_CONFIG or {}).get('storageBucket') or (f"{project_id}.appspot.com" if project_id else None)
        if not bucket_name:
            raise ValueError("Firebase Storage non configuré: définissez 'firebase.storageBucket' dans secrets.")
        try:
            b = storage.bucket(bucket_name)
            req_doc = self.requests_collection.document(request_id).get()
            req_data = req_doc.to_dict() if req_doc.exists else {}
            uid_or_email = (req_data.get('user_uid') or req_data.get('email_demandeur') or 'unknown').replace('@','_').replace('/','_')
            ext = os.path.splitext(uploaded_file.name)[1]
            path = f"mission_docs/{uid_or_email}/{datetime.now().strftime('%Y%m%d-%H%M%S')}{ext}"
            blob = b.blob(path)
            data = uploaded_file.getvalue() if hasattr(uploaded_file, 'getvalue') else uploaded_file.read()
            blob.upload_from_string(data, content_type=getattr(uploaded_file, 'type', None))
            url = blob.generate_signed_url(expiration=timedelta(days=365))
            att = {"name": uploaded_file.name, "path": path, "url": url}
            doc_ref = self.requests_collection.document(request_id)
            doc = doc_ref.get()
            attachments = []
            if doc.exists:
                attachments = (doc.to_dict() or {}).get('attachments', []) or []
            attachments.append(att)
            doc_ref.update({'attachments': attachments, 'updated_at': datetime.now()})
            return att
        except Exception as e:
            raise RuntimeError(f"Upload Storage échoué pour le bucket '{bucket_name}': {e}")

    def auto_assign(self, request_id: str) -> Optional[Dict]:
        """Calcule une recommandation d'affectation sans créer de mission.
        Écrit les champs 'recommended_driver' et 'recommended_vehicle' sur la demande.
        """
        req = self.get_request(request_id)
        if not req:
            return None
        start_date = req.get('date_depart')
        end_date = req.get('date_retour')
        v_type = req.get('type_vehicule')
        veh_mgr = VehicleManager()
        drv_mgr = DriverManager()
        stats_mgr = StatisticsManager()
        vehicles = veh_mgr.get_available_vehicles(start_date, end_date)
        drivers = drv_mgr.get_available_drivers(start_date, end_date)
        if v_type and v_type != 'Indifférent':
            vehicles = [v for v in vehicles if v.get('type') == v_type]
        report = stats_mgr.get_monthly_report(datetime.now().year, datetime.now().month)
        dstats = report.get('driver_stats', {}) if isinstance(report, dict) else {}
        def missions_count(did):
            s = dstats.get(did) or {}
            return int(s.get('missions', s.get('missaions', 0) or 0))
        drivers_sorted = sorted(drivers, key=lambda d: missions_count(d.get('id')))
        vehicle = vehicles[0] if vehicles else None
        driver = drivers_sorted[0] if drivers_sorted else None
        if not vehicle or not driver:
            return None
        # Écrire la recommandation sur la demande, sans l'approuver ni créer la mission
        self.requests_collection.document(request_id).update({
            'recommended_vehicle': vehicle.get('id'),
            'recommended_driver': driver.get('id'),
            'updated_at': datetime.now()
        })
        return {'driver_id': driver.get('id'), 'vehicle_id': vehicle.get('id')}

    def manual_assign_and_create_mission(self, request_id: str, vehicle_id: str, driver_id: str) -> str:
        cal = CalendarManager()
        req = self.get_request(request_id)
        self.assign_vehicle_driver(request_id, vehicle_id, driver_id)
        return cal.create_mission({
            'request_id': request_id,
            'motif_mission': req.get('motif_mission','') if req else '',
            'start_date': req.get('date_depart') if req else datetime.now(),
            'end_date': req.get('date_retour') if req else datetime.now(),
            'driver_id': driver_id,
            'vehicle_id': vehicle_id
        })

# ==========================================
# GESTION DES VÉHICULES
# ==========================================

class VehicleManager:
    """Gestionnaire des véhicules"""
    
    def __init__(self):
        self.db = initialize_firebase()
        self.vehicles_collection = self.db.collection('vehicles')
        self.missions_collection = self.db.collection('active_missions')
        self.drivers_collection = self.db.collection('drivers')
    
    def get_all_vehicles(self) -> List[Dict]:
        """Récupère tous les véhicules"""
        vehicles = self.vehicles_collection.stream()
        return [{'id': v.id, **v.to_dict()} for v in vehicles]
    
    def get_available_vehicles(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Récupère les véhicules disponibles pour une période donnée
        
        Args:
            start_date: Date de début
            end_date: Date de fin
        
        Returns:
            Liste des véhicules disponibles
        """
        all_vehicles = self.get_all_vehicles()
        
        # Récupérer les missions actives pendant cette période
        active_missions = self.missions_collection.where(
            'start_date', '<=', end_date
        ).where(
            'end_date', '>=', start_date
        ).stream()
        
        # Véhicules occupés
        occupied_vehicle_ids = {m.to_dict().get('vehicle_id') for m in active_missions}
        
        # Filtrer les véhicules disponibles
        available = [v for v in all_vehicles if v['id'] not in occupied_vehicle_ids]
        
        return available
    
    def add_vehicle(self, vehicle_data: Dict):
        """Ajoute un nouveau véhicule"""
        vehicle_id = f"VH-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        vehicle_data.update({
            'vehicle_id': vehicle_id,
            'created_at': datetime.now(),
            'status': 'active'  # active, maintenance, inactive
        })
        self.vehicles_collection.document(vehicle_id).set(vehicle_data)
        return vehicle_id
    
    def update_vehicle_status(self, vehicle_id: str, status: str):
        """Met à jour le statut d'un véhicule"""
        self.vehicles_collection.document(vehicle_id).update({
            'status': status,
            'updated_at': datetime.now()
        })

    def assign_driver(self, vehicle_id: str, driver_id: str):
        # Clear previous driver assignment on this vehicle, if any
        try:
            vdoc = self.vehicles_collection.document(vehicle_id).get()
            prev_driver = None
            if vdoc.exists:
                prev_driver = (vdoc.to_dict() or {}).get('assigned_driver')
        except Exception:
            prev_driver = None

        self.vehicles_collection.document(vehicle_id).update({
            'assigned_driver': driver_id,
            'updated_at': datetime.now()
        })
        self.drivers_collection.document(driver_id).update({
            'assigned_vehicle': vehicle_id,
            'updated_at': datetime.now()
        })
        if prev_driver and prev_driver != driver_id:
            try:
                self.drivers_collection.document(prev_driver).update({
                    'assigned_vehicle': None,
                    'updated_at': datetime.now()
                })
            except Exception:
                pass

# ==========================================
# GESTION DES CHAUFFEURS
# ==========================================

class DriverManager:
    """Gestionnaire des chauffeurs"""
    
    def __init__(self):
        self.db = initialize_firebase()
        self.drivers_collection = self.db.collection('drivers')
        self.missions_collection = self.db.collection('active_missions')
    
    def get_all_drivers(self) -> List[Dict]:
        """Récupère tous les chauffeurs"""
        drivers = self.drivers_collection.stream()
        return [{'id': d.id, **d.to_dict()} for d in drivers]
    
    def get_available_drivers(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Récupère les chauffeurs disponibles pour une période donnée"""
        all_drivers = self.get_all_drivers()
        
        # Récupérer les missions actives
        active_missions = self.missions_collection.where(
            'start_date', '<=', end_date
        ).where(
            'end_date', '>=', start_date
        ).stream()
        
        # Chauffeurs occupés
        occupied_driver_ids = {m.to_dict().get('driver_id') for m in active_missions}
        
        # Filtrer les chauffeurs disponibles
        available = [d for d in all_drivers if d['id'] not in occupied_driver_ids and d.get('status') == 'active']
        
        return available
    
    def add_driver(self, driver_data: Dict):
        """Ajoute un nouveau chauffeur"""
        driver_id = f"DR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        driver_data.update({
            'driver_id': driver_id,
            'created_at': datetime.now(),
            'status': 'active',  # active, on_leave, inactive
            'total_missions': 0
        })
        self.drivers_collection.document(driver_id).set(driver_data)
        return driver_id
    
    def update_driver_status(self, driver_id: str, status: str):
        """Met à jour le statut d'un chauffeur"""
        self.drivers_collection.document(driver_id).update({
            'status': status,
            'updated_at': datetime.now()
        })
    
    def get_driver_statistics(self, driver_id: str) -> Dict:
        """Récupère les statistiques d'un chauffeur"""
        driver = self.drivers_collection.document(driver_id).get()
        if not driver.exists:
            return {}
        
        driver_data = driver.to_dict()
        
        # Récupérer les missions du chauffeur
        missions = self.missions_collection.where('driver_id', '==', driver_id).stream()
        missions_list = [m.to_dict() for m in missions]
        
        return {
            'driver_info': driver_data,
            'total_missions': len(missions_list),
            'missions_this_month': len([m for m in missions_list if m['start_date'].month == datetime.now().month]),
            'total_km': sum(m.get('distance_km', 0) for m in missions_list)
        }

# ==========================================
# GESTION DU CALENDRIER
# ==========================================

class CalendarManager:
    """Gestionnaire du calendrier des missions"""
    
    def __init__(self):
        self.db = initialize_firebase()
        self.missions_collection = self.db.collection('active_missions')
    
    def get_missions_in_period(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Récupère toutes les missions dans une période donnée"""
        missions = self.missions_collection.where(
            'start_date', '>=', start_date
        ).where(
            'start_date', '<=', end_date
        ).stream()
        
        return [{'id': m.id, **m.to_dict()} for m in missions]

    def update_mission_assignment_by_request(self, request_id: str, driver_id: str, vehicle_id: str) -> bool:
        """Met à jour chauffeur et véhicule pour la mission liée à une demande."""
        missions = list(self.missions_collection.where('request_id', '==', request_id).stream())
        if not missions:
            return False
        for m in missions:
            try:
                self.missions_collection.document(m.id).update({
                    'driver_id': driver_id,
                    'vehicle_id': vehicle_id,
                    'updated_at': datetime.now()
                })
            except Exception:
                pass
        return True
    def check_availability(self, start_date: datetime, end_date: datetime) -> Dict:
        """
        Vérifie la disponibilité pour une période
        
        Returns:
            Dict avec les véhicules et chauffeurs disponibles
        """
        vehicle_mgr = VehicleManager()
        driver_mgr = DriverManager()
        
        available_vehicles = vehicle_mgr.get_available_vehicles(start_date, end_date)
        available_drivers = driver_mgr.get_available_drivers(start_date, end_date)
        
        return {
            'available': len(available_vehicles) > 0 and len(available_drivers) > 0,
            'vehicles_count': len(available_vehicles),
            'drivers_count': len(available_drivers),
            'vehicles': available_vehicles,
            'drivers': available_drivers
        }
    
    def create_mission(self, mission_data: Dict):
        """Crée une mission active (après approbation)"""
        mission_id = f"MS-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        mission_data.update({
            'mission_id': mission_id,
            'created_at': datetime.now(),
            'status': 'active'
        })
        self.missions_collection.document(mission_id).set(mission_data)
        return mission_id
    
    def complete_mission(self, mission_id: str, completion_notes: str = ''):
        """Marque une mission comme terminée"""
        self.missions_collection.document(mission_id).update({
            'status': 'completed',
            'completed_at': datetime.now(),
            'completion_notes': completion_notes
        })

    def cleanup_orphan_missions(self) -> int:
        reqs = self.db.collection('mission_requests')
        missions = list(self.missions_collection.stream())
        deleted = 0
        for m in missions:
            data = m.to_dict() or {}
            rid = data.get('request_id')
            if not rid:
                continue
            try:
                rdoc = reqs.document(rid).get()
                if not rdoc.exists:
                    self.missions_collection.document(m.id).delete()
                    deleted += 1
            except Exception:
                pass
        return deleted

# ==========================================
# NOTIFICATIONS
# ==========================================

class NotificationManager:
    """Gestionnaire des notifications"""
    
    def __init__(self):
        self.db = initialize_firebase()
        self.notifications_collection = self.db.collection('notifications')
    
    def send_notification(self, user_email: str, title: str, message: str, notification_type: str = 'info'):
        """
        Envoie une notification à un utilisateur
        
        Args:
            user_email: Email de l'utilisateur
            title: Titre de la notification
            message: Message de la notification
            notification_type: Type (info, success, warning, error)
        """
        notification_data = {
            'user_email': user_email,
            'title': title,
            'message': message,
            'type': notification_type,
            'read': False,
            'created_at': datetime.now()
        }
        self.notifications_collection.add(notification_data)
    
    def get_user_notifications(self, user_email: str, unread_only: bool = False) -> List[Dict]:
        """Récupère les notifications d'un utilisateur"""
        query = self.notifications_collection.where('user_email', '==', user_email)
        
        if unread_only:
            query = query.where('read', '==', False)
        
        notifications = query.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        return [{'id': n.id, **n.to_dict()} for n in notifications]
    
    def mark_as_read(self, notification_id: str):
        """Marque une notification comme lue"""
        self.notifications_collection.document(notification_id).update({'read': True})

# ==========================================
# STATISTIQUES
# ==========================================

class StatisticsManager:
    """Gestionnaire des statistiques"""
    
    def __init__(self):
        self.db = initialize_firebase()
        self.requests_collection = self.db.collection('mission_requests')
        self.missions_collection = self.db.collection('active_missions')
        self.drivers_collection = self.db.collection('drivers')
        self.vehicles_collection = self.db.collection('vehicles')
    
    def get_dashboard_stats(self) -> Dict:
        """Récupère les statistiques pour le tableau de bord admin"""
        # Demandes en attente
        pending_requests = len(list(self.requests_collection.where('status', '==', 'pending').stream()))
        
        # Missions actives
        active_missions = len(list(self.missions_collection.where('status', '==', 'active').stream()))
        
        # Total véhicules
        total_vehicles = len(list(self.vehicles_collection.stream()))
        
        # Total chauffeurs
        total_drivers = len(list(self.drivers_collection.stream()))
        
        # Statistiques du mois (basées sur start_date dans le mois en cours)
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)
        if now.month == 12:
            end_of_month = datetime(now.year + 1, 1, 1)
        else:
            end_of_month = datetime(now.year, now.month + 1, 1)
        missions_this_month = len(list(
            self.missions_collection.where('start_date', '>=', start_of_month).where('start_date', '<', end_of_month).stream()
        ))
        
        return {
            'pending_requests': pending_requests,
            'active_missions': active_missions,
            'total_vehicles': total_vehicles,
            'total_drivers': total_drivers,
            'missions_this_month': missions_this_month
        }
    
    def get_monthly_report(self, year: int, month: int) -> Dict:
        """Génère un rapport mensuel basé sur 'start_date'"""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        missions = list(self.missions_collection.where(
            'start_date', '>=', start_date
        ).where(
            'start_date', '<', end_date
        ).stream())
        missions_data = [m.to_dict() for m in missions]
        
        # Statistiques
        total_missions = len(missions_data)
        total_km = sum(m.get('distance_km', 0) for m in missions_data)
        
        # Par chauffeur
        driver_stats = {}
        for mission in missions_data:
            driver_id = mission.get('driver_id')
            if driver_id:
                if driver_id not in driver_stats:
                    driver_stats[driver_id] = {'missions': 0, 'km': 0}
                driver_stats[driver_id]['missions'] += 1
                driver_stats[driver_id]['km'] += mission.get('distance_km', 0)
        
        return {
            'period': f"{month}/{year}",
            'total_missions': total_missions,
            'total_km': total_km,
            'driver_stats': driver_stats
        }

# ==========================================
# FONCTION D'AIDE POUR STREAMLIT
# ==========================================

@st.cache_resource
def get_managers():
    """Retourne les gestionnaires initialisés (cachés pour performance)"""
    return {
        'requests': MissionRequestManager(),
        'vehicles': VehicleManager(),
        'drivers': DriverManager(),
        'calendar': CalendarManager(),
        'notifications': NotificationManager(),
        'statistics': StatisticsManager()
    }
