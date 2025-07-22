"""
Database CETMA con gestione robusta per container Docker
Versione corretta per evitare problemi di import e permessi
"""

import sqlite3
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Any

class CetmaBookingDatabase:
    """Gestisce le prenotazioni CETMA con fallback multi-livello"""
    
    def __init__(self, db_path: str = None):
        self.in_memory = False
        self.connection = None
        
        # Usa variabile ambiente se disponibile (Docker)
        if db_path is None:
            db_path = os.environ.get('DATABASE_PATH')
            
        if db_path is None:
            # Fallback a directory persistente
            data_dir = '/app/data_persistent'
            if not os.path.exists(data_dir):
                try:
                    os.makedirs(data_dir, exist_ok=True)
                except:
                    data_dir = tempfile.gettempdir()
            
            db_path = os.path.join(data_dir, "cetma_bookings.db")
        
        self.db_path = db_path
        
        # Tentativo creazione database con fallback
        success = self._init_database()
        if not success:
            print("⚠️ Fallback a database in memoria...")
            self._init_memory_database()
    
    def _init_database(self):
        """Inizializza database con gestione errori robusta"""
        try:
            # Assicura che la directory esista
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            
            # Test connessione
            conn = sqlite3.connect(self.db_path, timeout=10)
            self._create_table(conn)
            conn.close()
            
            print(f"✅ Database file: {self.db_path}")
            return True
            
        except Exception as e:
            print(f"❌ Errore database file ({e})")
            return False
    
    def _init_memory_database(self):
        """Inizializza database in memoria come fallback"""
        try:
            self.db_path = ":memory:"
            self.in_memory = True
            # Mantieni connessione aperta per memoria
            self.connection = sqlite3.connect(self.db_path)
            self._create_table(self.connection)
            print(f"✅ Database memoria attivo")
            
        except Exception as e:
            print(f"💥 Errore fatale database memoria: {e}")
            raise
        
    def _create_table(self, conn):
        """Crea la tabella bookings con gestione errori"""
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cetma_bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    visitor_name TEXT NOT NULL,
                    visitor_email TEXT NOT NULL,
                    visitor_phone TEXT NOT NULL,
                    booking_area TEXT NOT NULL,
                    booking_date TEXT NOT NULL,
                    booking_time TEXT NOT NULL,
                    booking_duration TEXT NOT NULL,
                    booking_purpose TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'confirmed'
                )
            ''')
            conn.commit()
            
        except Exception as e:
            print(f"❌ Errore creazione tabella: {e}")
            raise
    
    def _get_connection(self):
        """Restituisce connessione appropriata con retry"""
        if self.in_memory:
            return self.connection, False
        else:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    conn = sqlite3.connect(self.db_path, timeout=5)
                    return conn, True
                except Exception as e:
                    if attempt == max_retries - 1:
                        print(f"❌ Connessione fallita dopo {max_retries} tentativi: {e}")
                        raise
                    print(f"⚠️ Tentativo {attempt + 1} fallito, riprovo...")
    
    def save_booking(self, booking_data: Dict[str, Any]) -> int:
        """Salva una prenotazione con gestione robusta degli errori"""
        if not booking_data:
            raise ValueError("Dati prenotazione vuoti")
        
        try:
            conn, close_conn = self._get_connection()
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO cetma_bookings 
                (visitor_name, visitor_email, visitor_phone, 
                 booking_area, booking_date, booking_time, 
                 booking_duration, booking_purpose)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                booking_data.get('visitor_name', 'N/A'),
                booking_data.get('visitor_email', 'N/A'),
                booking_data.get('visitor_phone', 'N/A'),
                booking_data.get('booking_area', 'N/A'),
                booking_data.get('booking_date', 'N/A'),
                booking_data.get('booking_time', 'N/A'),
                booking_data.get('booking_duration', 'N/A'),
                booking_data.get('booking_purpose', 'N/A')
            ))
            
            booking_id = cursor.lastrowid
            conn.commit()
            
            if close_conn:
                conn.close()
            
            storage_type = "memoria" if self.in_memory else "file"
            print(f"✅ Prenotazione salvata: ID #{booking_id} ({storage_type})")
            print(f"   👤 {booking_data.get('visitor_name', 'N/A')}")
            print(f"   🏛️ {booking_data.get('booking_area', 'N/A')}")
            print(f"   📅 {booking_data.get('booking_date', 'N/A')} - {booking_data.get('booking_time', 'N/A')}")
            
            return booking_id
            
        except Exception as e:
            print(f"❌ Errore salvataggio prenotazione: {e}")
            print(f"   Dati: {booking_data}")
            raise
    
    def get_all_bookings(self) -> List[Dict[str, Any]]:
        """Recupera tutte le prenotazioni"""
        try:
            conn, close_conn = self._get_connection()
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM cetma_bookings 
                ORDER BY booking_date, booking_time
            ''')
            
            columns = [description[0] for description in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            if close_conn:
                conn.close()
                
            return results
            
        except Exception as e:
            print(f"❌ Errore recupero prenotazioni: {e}")
            return []
    
    def check_availability(self, date: str, area: str, time: str, duration: str = "1 ore") -> bool:
        """Controlla disponibilità (implementazione semplificata)"""
        try:
            bookings = self.get_all_bookings()
            
            # Controlla conflitti
            for booking in bookings:
                if (booking['booking_date'] == date and 
                    booking['booking_area'] == area and 
                    booking['booking_time'] == time):
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Errore controllo disponibilità: {e}")
            return True  # In caso di errore, permetti prenotazione
    
    def print_all_bookings(self):
        """Stampa tutte le prenotazioni per debug"""
        bookings = self.get_all_bookings()
        
        storage_type = "MEMORIA" if self.in_memory else "FILE"
        print(f"\n🗃️ DATABASE: {storage_type}")
        print(f"📁 Path: {self.db_path}")
        
        if not bookings:
            print("📋 Nessuna prenotazione trovata.")
            return
        
        print("\n" + "="*80)
        print("🏢 PRENOTAZIONI AREE CETMA")
        print("="*80)
        
        for booking in bookings:
            print(f"""
📅 Prenotazione #{booking['id']}
👤 Visitatore: {booking['visitor_name']}
📧 Email: {booking['visitor_email']}
📞 Telefono: {booking['visitor_phone']}
🏛️ Area: {booking['booking_area']}
📅 Data: {booking['booking_date']}
🕐 Orario: {booking['booking_time']}
⏱️ Durata: {booking['booking_duration']}
📝 Scopo: {booking['booking_purpose']}
📊 Status: {booking['status']}
⏰ Creata: {booking['created_at']}
{'-'*50}""")
    
    def __del__(self):
        """Cleanup connessioni"""
        if hasattr(self, 'connection') and self.connection:
            try:
                self.connection.close()
            except:
                pass


# Test standalone per verificare funzionalità
if __name__ == "__main__":
    print("🧪 TEST DATABASE CETMA ROBUSTO")
    print("=" * 50)
    
    # Test creazione database
    db = CetmaBookingDatabase()
    
    # Prenotazione di test
    sample_booking = {
        'visitor_name': 'Test Docker User',
        'visitor_email': 'test@docker.local',
        'visitor_phone': '3401234567',
        'booking_area': 'Dipartimento NED',
        'booking_date': '25/12/2025',
        'booking_time': '10:00',
        'booking_duration': '2 ore',
        'booking_purpose': 'Test salvataggio Docker'
    }
    
    try:
        booking_id = db.save_booking(sample_booking)
        print(f"\n🎉 Test salvataggio: SUCCESS (ID #{booking_id})")
        
        # Verifica lettura
        all_bookings = db.get_all_bookings()
        print(f"📊 Prenotazioni totali: {len(all_bookings)}")
        
        # Stampa dettagli
        db.print_all_bookings()
        
    except Exception as e:
        print(f"💥 Test fallito: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ TEST COMPLETATO")