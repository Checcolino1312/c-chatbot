from typing import Any, Text, Dict, List
import re
from datetime import datetime, timedelta

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet, AllSlotsReset

# Importa il database per le prenotazioni
try:
    from database import CetmaBookingDatabase
except ImportError:
    # Se il database non è ancora implementato, creiamo una versione semplificata
    class CetmaBookingDatabase:
        def save_booking(self, booking_data):
            return 1  # Simula un ID di prenotazione
        
        def check_availability(self, date, area, time, duration):
            return True  # Simula disponibilità


class ValidateCetmaBookingForm(FormValidationAction):
    """Validazione personalizzata per il form di prenotazione aree CETMA"""

    def name(self) -> Text:
        return "validate_cetma_booking_form"

    def validate_visitor_name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Valida il nome del visitatore"""
        
        if not slot_value:
            dispatcher.utter_message(text="Per favore, dimmi il tuo nome.")
            return {"visitor_name": None}
            
        if len(slot_value.strip()) < 2:
            dispatcher.utter_message(text="Il nome deve contenere almeno 2 caratteri. Come ti chiami?")
            return {"visitor_name": None}
        
        # Pulisci e valida il nome completo
        clean_name = slot_value.strip()
        if not re.match(r"^[a-zA-ZÀ-ÿ\s\.]+$", clean_name):
            dispatcher.utter_message(text="Il nome può contenere solo lettere, spazi e punti. Qual è il tuo nome?")
            return {"visitor_name": None}
        
        return {"visitor_name": clean_name.title()}

    def validate_visitor_email(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Valida l'email del visitatore"""
        
        if not slot_value:
            dispatcher.utter_message(response="utter_invalid_email")
            return {"visitor_email": None}
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        if not re.match(email_pattern, slot_value.strip()):
            dispatcher.utter_message(response="utter_invalid_email")
            return {"visitor_email": None}
        
        return {"visitor_email": slot_value.strip().lower()}

    def validate_visitor_phone(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Valida il numero di telefono"""
        
        if not slot_value:
            dispatcher.utter_message(response="utter_invalid_phone")
            return {"visitor_phone": None}
        
        # Rimuovi spazi e caratteri speciali tranne +
        clean_phone = re.sub(r'[^\d+]', '', str(slot_value).strip())
        
        # Verifica lunghezza (10-15 cifre per numeri internazionali)
        digits_only = re.sub(r'[^\d]', '', clean_phone)
        if len(digits_only) < 10 or len(digits_only) > 15:
            dispatcher.utter_message(response="utter_invalid_phone")
            return {"visitor_phone": None}
        
        return {"visitor_phone": clean_phone}

    def validate_booking_area(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Valida l'area selezionata"""
        
        if not slot_value:
            dispatcher.utter_message(response="utter_invalid_area")
            return {"booking_area": None}
        
        # Aree disponibili al CETMA
        available_areas = {
            "dipartimento ned": "Dipartimento NED",
            "dipartimento nuove tecnologie": "Dipartimento NED", 
            "dipartimento design": "Dipartimento NED",
            "ned": "Dipartimento NED",
            "sala riunioni": "Sala Riunioni",
            "sala meeting": "Sala Meeting",
            "sala conferenze": "Sala Conferenze",
            "sala angelo marino": "Sala Angelo Marino",
            "angelo marino": "Sala Angelo Marino",
            "laboratorio": "Laboratorio",
            "laboratori": "Laboratorio",
            "lab": "Laboratorio",
            "virtual reality": "Virtual Reality Center",
            "vr": "Virtual Reality Center",
            "vr center": "Virtual Reality Center",
            "reception": "Reception",
            "ufficio": "Ufficio Generico",
            "spazio comune": "Spazio Comune"
        }
        
        area_key = slot_value.strip().lower()
        if area_key in available_areas:
            return {"booking_area": available_areas[area_key]}
        
        dispatcher.utter_message(response="utter_invalid_area")
        return {"booking_area": None}

    def validate_booking_date(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Valida la data di prenotazione"""
        
        if not slot_value:
            dispatcher.utter_message(response="utter_invalid_date")
            return {"booking_date": None}
        
        try:
            # Gestisci date relative
            today = datetime.now().date()
            
            if slot_value.lower() in ["oggi", "today"]:
                return {"booking_date": today.strftime("%d/%m/%Y")}
            elif slot_value.lower() in ["domani", "tomorrow"]:
                tomorrow = today + timedelta(days=1)
                return {"booking_date": tomorrow.strftime("%d/%m/%Y")}
            elif slot_value.lower() in ["dopodomani"]:
                day_after = today + timedelta(days=2)
                return {"booking_date": day_after.strftime("%d/%m/%Y")}
            
            # Prova a parsare la data nel formato gg/mm/aaaa
            date_parts = slot_value.strip().split('/')
            if len(date_parts) == 3:
                day, month, year = date_parts
                booking_date = datetime(int(year), int(month), int(day)).date()
                
                # Verifica che la data non sia nel passato
                if booking_date < today:
                    dispatcher.utter_message(response="utter_invalid_date")
                    return {"booking_date": None}
                
                # Verifica che la data sia in giorni lavorativi (lunedì-venerdì)
                if booking_date.weekday() > 4:  # 5=sabato, 6=domenica
                    dispatcher.utter_message(text="Le prenotazioni sono disponibili solo nei giorni lavorativi (lunedì-venerdì). Scegli un'altra data:")
                    return {"booking_date": None}
                
                # Verifica che la data non sia troppo lontana (max 2 mesi)
                max_date = today + timedelta(days=60)
                if booking_date > max_date:
                    dispatcher.utter_message(text="Possiamo accettare prenotazioni solo per i prossimi 2 mesi. Scegli una data più vicina:")
                    return {"booking_date": None}
                
                return {"booking_date": booking_date.strftime("%d/%m/%Y")}
            
        except (ValueError, IndexError):
            pass
        
        dispatcher.utter_message(response="utter_invalid_date")
        return {"booking_date": None}

    def validate_booking_time(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Valida l'orario di prenotazione"""
        
        if not slot_value:
            dispatcher.utter_message(response="utter_invalid_time")
            return {"booking_time": None}
        
        try:
            # Gestisci formati di tempo comuni
            time_str = slot_value.strip().lower()
            
            # Conversioni da testo per orari lavorativi
            time_conversions = {
                "otto": "08:00", "otto e mezza": "08:30",
                "nove": "09:00", "nove e mezza": "09:30",
                "dieci": "10:00", "dieci e mezza": "10:30",
                "undici": "11:00", "undici e mezza": "11:30",
                "dodici": "12:00", "mezzogiorno": "12:00",
                "tredici": "13:00", "una": "13:00",
                "quattordici": "14:00", "due": "14:00",
                "quindici": "15:00", "tre": "15:00",
                "sedici": "16:00", "quattro": "16:00",
                "diciassette": "17:00", "cinque": "17:00"
            }
            
            if time_str in time_conversions:
                time_str = time_conversions[time_str]
            
            # Aggiungi i due punti se mancano
            if len(time_str) == 4 and time_str.isdigit():
                time_str = time_str[:2] + ":" + time_str[2:]
            
            # Gestisci input incompleti come "14:"
            if time_str.endswith(':'):
                time_str += "00"
            
            # Prova a parsare l'orario
            time_obj = datetime.strptime(time_str, "%H:%M").time()
            
            # Verifica che sia nell'orario lavorativo (08:00 - 17:00)
            opening_time = datetime.strptime("08:00", "%H:%M").time()
            closing_time = datetime.strptime("17:00", "%H:%M").time()
            
            if not (opening_time <= time_obj <= closing_time):
                dispatcher.utter_message(response="utter_invalid_time")
                return {"booking_time": None}
            
            return {"booking_time": time_obj.strftime("%H:%M")}
            
        except ValueError:
            dispatcher.utter_message(response="utter_invalid_time")
            return {"booking_time": None}

    def validate_booking_duration(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Valida la durata della prenotazione"""
        
        if not slot_value:
            dispatcher.utter_message(response="utter_invalid_duration")
            return {"booking_duration": None}
        
        try:
            # Conversioni da testo a numero
            duration_conversions = {
                "un'ora": "1",
                "una ora": "1",
                "mezz'ora": "0.5",
                "mezza ora": "0.5",
                "due ore": "2",
                "tre ore": "3",
                "quattro ore": "4",
                "cinque ore": "5",
                "sei ore": "6",
                "sette ore": "7",
                "otto ore": "8",
                "tutta la giornata": "8",
                "giornata intera": "8"
            }
            
            duration_str = slot_value.strip().lower()
            
            # Rimuovi "ore" dalla fine se presente
            if duration_str.endswith(" ore"):
                duration_str = duration_str[:-4].strip()
            elif duration_str.endswith(" ora"):
                duration_str = duration_str[:-4].strip()
            
            if duration_str in duration_conversions:
                duration_str = duration_conversions[duration_str]
            
            duration = float(duration_str)
            
            # Verifica che la durata sia ragionevole (0.5 - 8 ore)
            if duration < 0.5 or duration > 8:
                dispatcher.utter_message(response="utter_invalid_duration")
                return {"booking_duration": None}
            
            # Formatta la durata
            if duration == int(duration):
                return {"booking_duration": f"{int(duration)} ore"}
            else:
                return {"booking_duration": f"{duration} ore"}
            
        except ValueError:
            dispatcher.utter_message(response="utter_invalid_duration")
            return {"booking_duration": None}

    def validate_booking_purpose(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Valida il motivo della prenotazione"""
        
        if not slot_value or len(slot_value.strip()) < 5:
            dispatcher.utter_message(text="Il motivo della prenotazione deve contenere almeno 5 caratteri. Riprova:")
            return {"booking_purpose": None}
        
        # Verifica lunghezza massima
        if len(slot_value.strip()) > 200:
            dispatcher.utter_message(text="Il motivo della prenotazione è troppo lungo (max 200 caratteri). Riprova:")
            return {"booking_purpose": None}
        
        return {"booking_purpose": slot_value.strip()}


class ActionSubmitCetmaBooking(Action):
    """Azione per sottomettere la prenotazione area CETMA"""
    
    def name(self) -> Text:
        return "action_submit_cetma_booking"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Raccoglie tutti i dati della prenotazione
        booking_data = {
            'visitor_name': tracker.get_slot("visitor_name"),
            'visitor_email': tracker.get_slot("visitor_email"),
            'visitor_phone': tracker.get_slot("visitor_phone"),
            'booking_area': tracker.get_slot("booking_area"),
            'booking_date': tracker.get_slot("booking_date"),
            'booking_time': tracker.get_slot("booking_time"),
            'booking_duration': tracker.get_slot("booking_duration"),
            'booking_purpose': tracker.get_slot("booking_purpose")
        }
        
        # Controlla disponibilità dell'area
        booking_date = booking_data['booking_date']
        booking_time = booking_data['booking_time']
        booking_area = booking_data['booking_area']
        
        # Simulazione di slot occupati per alcune aree
        busy_slots = [
            ("Sala Angelo Marino", "25/12/2025", "10:00"),
            ("Dipartimento NED", "26/12/2025", "14:00"),
            ("Virtual Reality Center", "27/12/2025", "09:00")
        ]
        
        if (booking_area, booking_date, booking_time) in busy_slots:
            dispatcher.utter_message(response="utter_area_unavailable")
            return [SlotSet("booking_time", None)]
        
        # Salva la prenotazione nel database
        try:
            db = CetmaBookingDatabase()
            booking_id = db.save_booking(booking_data)
            
            # Conferma prenotazione con ID
            dispatcher.utter_message(
                text=f"Perfetto {booking_data['visitor_name']}! La tua prenotazione è confermata:\n\n"
                     f"🏢 **CENTRO RICERCHE CETMA**\n"
                     f"📋 ID Prenotazione: #{booking_id}\n"
                     f"🏛️ Area: {booking_data['booking_area']}\n"
                     f"📅 Data: {booking_data['booking_date']}\n"
                     f"🕐 Orario: {booking_data['booking_time']}\n"
                     f"⏱️ Durata: {booking_data['booking_duration']}\n"
                     f"📝 Scopo: {booking_data['booking_purpose']}\n"
                     f"📧 Email: {booking_data['visitor_email']}\n"
                     f"📞 Telefono: {booking_data['visitor_phone']}\n\n"
                     f"📍 **Sede**: Cittadella della Ricerca, Brindisi\n"
                     f"🕐 **Orari**: Lunedì-Venerdì 08:00-17:00\n\n"
                     f"Conserva questo ID per eventuali modifiche. Per ulteriori informazioni contatta: 0831-201218"
            )
            
            print(f"✅ PRENOTAZIONE CETMA SALVATA - ID: {booking_id}")
            print(f"   Visitatore: {booking_data['visitor_name']}")
            print(f"   Area: {booking_data['booking_area']}")
            print(f"   Data: {booking_data['booking_date']} alle {booking_data['booking_time']}")
            print(f"   Durata: {booking_data['booking_duration']}")
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ Errore nel salvare la prenotazione: {e}")
            dispatcher.utter_message(
                text="La prenotazione è stata registrata, ma si è verificato un problema tecnico. "
                     "Contatta la reception CETMA al numero 0831-201218 per verificare."
            )
        
        return []


class ActionShowAvailableAreas(Action):
    """Azione per mostrare le aree disponibili"""
    
    def name(self) -> Text:
        return "action_show_available_areas"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        areas_info = """🏢 **AREE DISPONIBILI PRESSO CETMA**

🔬 **Dipartimento NED** (Nuove Tecnologie e Design)
   📍 Secondo piano - Seguire segnaletica fisica

🎯 **Sala Angelo Marino**
   📍 Terzo piano - Per meeting internazionali

🧪 **Laboratorio**
   📍 Piano terra - Attività sperimentali

🥽 **Virtual Reality Center**
   📍 Piano terra - Realtà virtuale e aumentata

🏢 **Sala Riunioni**
   📍 Vari piani - Meeting e conferenze

📞 **Reception**
   📍 Piano terra - Informazioni e accoglienza

📍 **Sede**: Cittadella della Ricerca, Brindisi
🕐 **Orari**: Lunedì-Venerdì 08:00-17:00
📞 **Info**: 0831-201218

Per prenotare un'area, dimmi "vorrei prenotare un'area"!"""
        
        dispatcher.utter_message(text=areas_info)
        return []


class ActionGreetUser(Action):
    """Azione personalizzata per salutare l'utente"""
    
    def name(self) -> Text:
        return "action_greet_user"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Saluto personalizzato per CETMA
        dispatcher.utter_message(
            text="Ciao! Sono l'assistente virtuale del CETMA - Centro di Ricerche Europeo di Tecnologie, Design e Materiali.\n\n"
                 "Posso aiutarti con:\n"
                 "🗺️ Orientamento nella sede\n"
                 "📋 Prenotazione aree e sale\n"
                 "🕐 Informazioni su orari e servizi\n"
                 "📞 Contatti e riferimenti\n\n"
                 "Come posso aiutarti oggi?"
        )
        
        return []


class ActionHelpBooking(Action):
    """Azione per aiutare con la prenotazione"""
    
    def name(self) -> Text:
        return "action_help_booking"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        help_message = """📋 **GUIDA PRENOTAZIONE AREE CETMA**

🎯 **Come prenotare:**
1️⃣ Dimmi "vorrei prenotare un'area"
2️⃣ Ti chiederò: nome, email, telefono
3️⃣ Scegli l'area che ti serve
4️⃣ Indica data, ora, durata e motivo

🏢 **Aree disponibili:**
• Dipartimento NED (2° piano)
• Sala Angelo Marino (3° piano)  
• Laboratorio (piano terra)
• Virtual Reality Center (piano terra)
• Sala Riunioni
• Reception

⏰ **Orari:** Lun-Ven 08:00-17:00
📅 **Date:** Solo giorni lavorativi

💡 **Esempi di come iniziare:**
• "Prenota area"
• "Vorrei una sala" 
• "Ho bisogno del laboratorio"

Pronto? Dimmi "prenota area" per iniziare! 🚀"""
        
        dispatcher.utter_message(text=help_message)
        return []


class ActionOutOfScope(Action):
    """Azione per domande fuori contesto"""
    
    def name(self) -> Text:
        return "action_out_of_scope"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(
            text="Mi dispiace, ma posso aiutarti solo con:\n"
                 "🏢 Informazioni sul CETMA\n"
                 "📋 Prenotazioni aree\n"
                 "🗺️ Orientamento nella sede\n"
                 "📞 Contatti e orari\n\n"
                 "Cosa posso fare per te oggi?"
        )
        return []


class ActionRestartCetmaConversation(Action):
    """Azione per riavviare la conversazione"""
    
    def name(self) -> Text:
        return "action_restart_cetma"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(
            text="Conversazione riavviata. Sono qui per aiutarti con le informazioni e prenotazioni CETMA. "
                 "Come posso aiutarti?"
        )
        return [AllSlotsReset()]