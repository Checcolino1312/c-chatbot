"""
Database CETMA con fallback in memoria per problemi OneDrive/Windows
Risolve errori di permessi su directory sincronizzate
"""

import sqlite3
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Any

class CetmaBookingDatabase:
    """Gestisce le prenotazioni CETMA con fallback in memoria"""
    
    def __init__(self, db_path: str = None):
        self.in_memory = False
        
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(current_dir, "cetma_bookings.db")
        else:
            self.db_path = db_path
            
        # Prova prima con file, poi con memoria
        try:
            self._init_file_database()
            print(f"✅ Database su file: {self.db_path}")
        except Exception as e:
            print(f"⚠️ Impossibile creare database su file: {e}")
            print(f"🔄 Fallback a database in memoria...")
            self._init_memory_database()
    
    def _init_file_database(self):
        """Inizializza database su file"""
        conn = sqlite3.connect(self.db_path)
        self._create_table(conn)
        conn.close()
        
    def _init_memory_database(self):
        """Inizializza database in memoria"""
        self.db_path = ":memory:"
        self.in_memory = True
        # Per database in memoria, manteniamo la connessione aperta
        self._memory_conn = sqlite3.connect(self.db_path)
        self._create_table(self._memory_conn)
        print(f"✅ Database in memoria attivo")
        
    def _create_table(self, conn):
        """Crea la tabella bookings"""
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
    
    def _get_connection(self):
        """Restituisce connessione appropriata"""
        if self.in_memory:
            return self._memory_conn
        else:
            return sqlite3.connect(self.db_path)
    
    def save_booking(self, booking_data: Dict[str, Any]) -> int:
        """Salva una prenotazione"""
        if self.in_memory:
            conn = self._memory_conn
            close_conn = False
        else:
            conn = sqlite3.connect(self.db_path)
            close_conn = True
            
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO cetma_bookings 
                (visitor_name, visitor_email, visitor_phone, 
                 booking_area, booking_date, booking_time, 
                 booking_duration, booking_purpose)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                booking_data.get('visitor_name'),
                booking_data.get('visitor_email'),
                booking_data.get('visitor_phone'),
                booking_data.get('booking_area'),
                booking_data.get('booking_date'),
                booking_data.get('booking_time'),
                booking_data.get('booking_duration'),
                booking_data.get('booking_purpose')
            ))
            
            booking_id = cursor.lastrowid
            conn.commit()
            
            if close_conn:
                conn.close()
                
            print(f"✅ Prenotazione salvata con ID: {booking_id} ({'memoria' if self.in_memory else 'file'})")
            return booking_id
            
        except Exception as e:
            print(f"❌ Errore salvataggio: {e}")
            if close_conn:
                conn.close()
            raise
    
    def get_all_bookings(self) -> List[Dict[str, Any]]:
        """Recupera tutte le prenotazioni"""
        if self.in_memory:
            conn = self._memory_conn
            close_conn = False
        else:
            conn = sqlite3.connect(self.db_path)
            close_conn = True
            
        try:
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
            print(f"❌ Errore recupero: {e}")
            if close_conn:
                conn.close()
            return []
    
    def print_all_bookings(self):
        """Stampa tutte le prenotazioni"""
        bookings = self.get_all_bookings()
        
        storage_type = "MEMORIA" if self.in_memory else "FILE"
        print(f"\n🗃️ DATABASE: {storage_type}")
        
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
        """Chiude connessione in memoria se necessario"""
        if hasattr(self, '_memory_conn') and self.in_memory:
            try:
                self._memory_conn.close()
            except:
                pass


if __name__ == "__main__":
    print("🧪 TEST DATABASE CETMA CON FALLBACK")
    print("=" * 50)
    
    # Test
    db = CetmaBookingDatabase()
    
    # Prenotazione di esempio
    sample_booking = {
        'visitor_name': 'Dr. Mario Rossi',
        'visitor_email': 'mario.rossi@università.it',
        'visitor_phone': '3401234567',
        'booking_area': 'Dipartimento NED',
        'booking_date': '20/12/2025',
        'booking_time': '10:00',
        'booking_duration': '2 ore',
        'booking_purpose': 'Riunione di ricerca'
    }
    
    booking_id = db.save_booking(sample_booking)
    db.print_all_bookings()
    
    print("\n🎉 TEST COMPLETATO!")