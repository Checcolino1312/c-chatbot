"""
Database semplificato per le prenotazioni CETMA
da inserire nel file database.py nella root del progetto
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

class CetmaBookingDatabase:
    """Gestisce le prenotazioni delle aree CETMA in un database SQLite"""
    
    def __init__(self, db_path: str = "cetma_bookings.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Crea la tabella se non esiste"""
        conn = sqlite3.connect(self.db_path)
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
        conn.close()
    
    def save_booking(self, booking_data: Dict[str, Any]) -> int:
        """Salva una prenotazione nel database"""
        conn = sqlite3.connect(self.db_path)
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
        conn.close()
        
        return booking_id
    
    def get_all_bookings(self) -> List[Dict[str, Any]]:
        """Recupera tutte le prenotazioni"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM cetma_bookings 
            ORDER BY booking_date, booking_time
        ''')
        
        columns = [description[0] for description in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        conn.close()
        return results
    
    def check_availability(self, date: str, area: str, time: str, duration: str) -> bool:
        """Controlla disponibilità di un'area"""
        # Simulazione semplice - in produzione implementare logica completa
        return True
    
    def print_all_bookings(self):
        """Stampa tutte le prenotazioni"""
        bookings = self.get_all_bookings()
        
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


if __name__ == "__main__":
    # Test del database
    db = CetmaBookingDatabase()
    
    # Esempio di prenotazione
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
    
    # Salva la prenotazione di esempio
    booking_id = db.save_booking(sample_booking)
    print(f"✅ Prenotazione CETMA salvata con ID: {booking_id}")
    
    # Mostra tutte le prenotazioni
    db.print_all_bookings()