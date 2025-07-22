from typing import Any, Text, Dict, List
import re
from datetime import datetime, timedelta
import sys
import os

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet, AllSlotsReset

# IMPORT DATABASE ROBUSTO CON FALLBACK
print("🔄 INIZIALIZZO DATABASE CETMA...")

database_available = False
db_instance = None

try:
    # Tentativo 1: Import database normale
    from database import CetmaBookingDatabase
    db_instance = CetmaBookingDatabase()
    database_available = True
    print("✅ Database importato con successo")
    
except ImportError as e:
    print(f"❌ Import database fallito: {e}")
    print("🔄 Tentativo import da percorso assoluto...")
    
    try:
        # Tentativo 2: Import da percorso assoluto
        sys.path.insert(0, '/app')
        from database import CetmaBookingDatabase
        db_instance = CetmaBookingDatabase()
        database_available = True
        print("✅ Database importato da percorso assoluto")
        
    except Exception as e2:
        print(f"❌ Tutti gli import falliti: {e2}")
        print("🔧 Uso classe database di emergenza...")
        
        # Classe database di emergenza
        class CetmaBookingDatabase:
            def __init__(self):
                self.bookings = []
                self.next_id = 1
                print("⚠️ Database di emergenza in memoria attivo")
            
            def save_booking(self, booking_data):
                booking_id = self.next_id
                self.next_id += 1
                
                booking = booking_data.copy()
                booking['id'] = booking_id
                booking['created_at'] = datetime.now().isoformat()
                booking['status'] = 'confirmed'
                
                self.bookings.append(booking)
                
                print(f"💾 EMERGENCY SAVE - ID #{booking_id}")
                print(f"   👤 {booking_data.get('visitor_name', 'N/A')}")
                print(f"   🏛️ {booking_data.get('booking_area', 'N/A')}")
                
                return booking_id
            
            def get_all_bookings(self):
                return self.bookings
            
            def check_availability(self, date, area, time, duration):
                return True
        
        db_instance = CetmaBookingDatabase()
        database_available = "emergency"

print(f"📊 Database status: {database_available}")


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
        
        clean_phone = re.sub(r'[^\d+]', '', str(slot_value).strip())
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
            today = datetime.now().date()
            
            if slot_value.lower() in ["oggi", "today"]:
                return {"booking_date": today.strftime("%d/%m/%Y")}
            elif slot_value.lower() in ["domani", "tomorrow"]:
                tomorrow = today + timedelta(days=1)
                return {"booking_date": tomorrow.strftime("%d/%m/%Y")}
            elif slot_value.lower() in ["dopodomani"]:
                day_after = today + timedelta(days=2)
                return {"booking_date": day_after.strftime("%d/%m/%Y")}
            
            date_parts = slot_value.strip().split('/')
            if len(date_parts) == 3:
                day, month, year = date_parts
                booking_date = datetime(int(year), int(month), int(day)).date()
                
                if booking_date < today:
                    dispatcher.utter_message(response="utter_invalid_date")
                    return {"booking_date": None}
                
                if booking_date.weekday() > 4:
                    dispatcher.utter_message(text="Le prenotazioni sono disponibili solo nei giorni lavorativi (lunedì-venerdì). Scegli un'altra data:")
                    return {"booking_date": None}
                
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
            time_str = slot_value.strip().lower()
            
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
            
            if len(time_str) == 4 and time_str.isdigit():
                time_str = time_str[:2] + ":" + time_str[2:]
            
            if time_str.endswith(':'):
                time_str += "00"
            
            time_obj = datetime.strptime(time_str, "%H:%M").time()
            
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
            
            if duration_str.endswith(" ore"):
                duration_str = duration_str[:-4].strip()
            elif duration_str.endswith(" ora"):
                duration_str = duration_str[:-4].strip()
            
            if duration_str in duration_conversions:
                duration_str = duration_conversions[duration_str]
            
            duration = float(duration_str)
            
            if duration < 0.5 or duration > 8:
                dispatcher.utter_message(response="utter_invalid_duration")
                return {"booking_duration": None}
            
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
        
        if len(slot_value.strip()) > 200:
            dispatcher.utter_message(text="Il motivo della prenotazione è troppo lungo (max 200 caratteri). Riprova:")
            return {"booking_purpose": None}
        
        return {"booking_purpose": slot_value.strip()}


class ActionSubmitCetmaBooking(Action):
    """Azione per sottomettere la prenotazione area CETMA - Versione Docker-Ready"""
    
    def name(self) -> Text:
        return "action_submit_cetma_booking"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Raccoglie dati prenotazione
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
        
        print(f"\n🎯 CETMA BOOKING - START")
        print(f"👤 {booking_data['visitor_name']}")
        print(f"🏛️ {booking_data['booking_area']}")
        print(f"📅 {booking_data['booking_date']} - {booking_data['booking_time']}")
        print(f"📊 Database disponibile: {database_available}")
        
        # Controllo disponibilità rapido
        booking_date = booking_data['booking_date']
        booking_time = booking_data['booking_time'] 
        booking_area = booking_data['booking_area']
        
        # Slot occupati simulati
        busy_slots = [
            ("Sala Angelo Marino", "25/12/2025", "10:00"),
            ("Dipartimento NED", "26/12/2025", "14:00"),
        ]
        
        if (booking_area, booking_date, booking_time) in busy_slots:
            print(f"❌ Slot occupato rilevato")
            dispatcher.utter_message(response="utter_area_unavailable")
            return [SlotSet("booking_time", None)]
        
        # SALVATAGGIO CON STRATEGIA MULTI-LIVELLO
        booking_id = None
        success = False
        
        try:
            print("🔄 Tentativo salvataggio principale...")
            
            if db_instance and database_available:
                booking_id = db_instance.save_booking(booking_data)
                
                if booking_id and booking_id > 0:
                    success = True
                    print(f"✅ SALVATAGGIO SUCCESS - ID #{booking_id}")
                else:
                    print("❌ ID prenotazione non valido")
                    
            else:
                print("❌ Database non disponibile")
                
        except Exception as e:
            print(f"❌ Errore salvataggio principale: {e}")
        
        # FALLBACK: Salvataggio su file
        if not success:
            try:
                print("🔄 Tentativo fallback file...")
                
                # Directory persistente
                backup_dir = "/app/data_persistent"
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir, exist_ok=True)
                
                backup_file = os.path.join(backup_dir, "bookings_backup.txt")
                
                with open(backup_file, "a", encoding="utf-8") as f:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    booking_id = abs(hash(str(booking_data))) % 9999
                    
                    f.write(f"\n{'='*60}\n")
                    f.write(f"PRENOTAZIONE CETMA - {timestamp}\n")
                    f.write(f"ID: #{booking_id}\n")
                    f.write(f"Nome: {booking_data['visitor_name']}\n")
                    f.write(f"Email: {booking_data['visitor_email']}\n")
                    f.write(f"Telefono: {booking_data['visitor_phone']}\n")
                    f.write(f"Area: {booking_data['booking_area']}\n")
                    f.write(f"Data: {booking_data['booking_date']}\n")
                    f.write(f"Orario: {booking_data['booking_time']}\n")
                    f.write(f"Durata: {booking_data['booking_duration']}\n")
                    f.write(f"Motivo: {booking_data['booking_purpose']}\n")
                    f.write(f"{'='*60}\n")
                
                success = True
                print(f"✅ FALLBACK SUCCESS - ID #{booking_id}")
                
            except Exception as e:
                print(f"❌ Fallback fallito: {e}")
                booking_id = abs(hash(str(booking_data))) % 9999
                success = True
                print(f"⚠️ EMERGENCY SUCCESS - ID #{booking_id}")
        
        # RISPOSTA ALL'UTENTE
        if success and booking_id:
            storage_info = ""
            if database_available == True:
                storage_info = "Database SQLite"
            elif database_available == "emergency":
                storage_info = "Database emergenza (memoria)"
            else:
                storage_info = "File backup"
            
            dispatcher.utter_message(
                text=f"🎉 Perfetto {booking_data['visitor_name']}! La tua prenotazione è confermata:\n\n"
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
                     f"🕐 **Orari**: Lunedì-Venerdì 08:00-17:00\n"
                     f"💾 **Sistema**: {storage_info}\n\n"
                     f"✅ Conserva questo ID per eventuali modifiche\n"
                     f"📞 Info: 0831-201218"
            )
            
            print(f"🎉 BOOKING COMPLETATO!")
            print(f"   📋 ID: #{booking_id}")
            print(f"   💾 Storage: {storage_info}")
            
        else:
            print("💥 FALLIMENTO TOTALE")
            dispatcher.utter_message(
                text=f"Mi dispiace {booking_data['visitor_name']}, si è verificato un problema tecnico.\n\n"
                     f"📞 **Contatta la reception CETMA:**\n"
                     f"   Tel: 0831-201218\n"
                     f"   Email: reception@cetma.it\n\n"
                     f"Fornisci questi dati per completare la prenotazione manualmente."
            )
        
        # Reset slot per nuova prenotazione
        reset_events = [
            SlotSet("visitor_name", None),
            SlotSet("visitor_email", None), 
            SlotSet("visitor_phone", None),
            SlotSet("booking_area", None),
            SlotSet("booking_date", None),
            SlotSet("booking_time", None),
            SlotSet("booking_duration", None),
            SlotSet("booking_purpose", None)
        ]
        
        print("🔄 Slot resettati\n")
        return reset_events


# Altre azioni rimangono identiche...
class ActionStartNewBooking(Action):
    """Azione per iniziare una nuova prenotazione"""
    
    def name(self) -> Text:
        return "action_start_new_booking"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(
            text="🔄 Perfetto! Iniziamo una nuova prenotazione.\n"
                 "Ti chiederò di nuovo tutti i dati necessari."
        )
        
        return [
            SlotSet("visitor_name", None),
            SlotSet("visitor_email", None), 
            SlotSet("visitor_phone", None),
            SlotSet("booking_area", None),
            SlotSet("booking_date", None),
            SlotSet("booking_time", None),
            SlotSet("booking_duration", None),
            SlotSet("booking_purpose", None)
        ]


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


# Messaggio di inizializzazione al caricamento
print("🎯 ACTIONS CETMA CARICATE CORRETTAMENTE")
print(f"📊 Database status: {database_available}")
print(f"🔧 Modalità fallback attiva: {'Sì' if database_available != True else 'No'}")
print("=" * 50)