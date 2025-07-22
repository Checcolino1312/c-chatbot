#!/usr/bin/env python3
"""
Esportatore prenotazioni CETMA per ambiente Docker
Salva i file in directory condivise con l'host
"""

import csv
import json
from datetime import datetime
import os

def export_to_csv(bookings, filename="/app/exports/cetma_prenotazioni.csv"):
    """Esporta prenotazioni in CSV"""
    try:
        # Assicurati che la directory esista
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if not bookings:
                csvfile.write("Nessuna prenotazione trovata\n")
                return filename
            
            # Intestazioni colonne
            fieldnames = [
                'ID', 'Nome', 'Email', 'Telefono', 'Area', 
                'Data', 'Orario', 'Durata', 'Motivo', 'Creata il', 'Status'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Scrivi i dati
            for booking in bookings:
                writer.writerow({
                    'ID': booking.get('id', 'N/A'),
                    'Nome': booking.get('visitor_name', 'N/A'),
                    'Email': booking.get('visitor_email', 'N/A'),
                    'Telefono': booking.get('visitor_phone', 'N/A'),
                    'Area': booking.get('booking_area', 'N/A'),
                    'Data': booking.get('booking_date', 'N/A'),
                    'Orario': booking.get('booking_time', 'N/A'),
                    'Durata': booking.get('booking_duration', 'N/A'),
                    'Motivo': booking.get('booking_purpose', 'N/A'),
                    'Creata il': booking.get('created_at', 'N/A'),
                    'Status': booking.get('status', 'confirmed')
                })
        
        print(f"✅ CSV creato: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Errore creazione CSV: {e}")
        return None

def export_to_json(bookings, filename="/app/exports/cetma_prenotazioni.json"):
    """Esporta prenotazioni in JSON (più semplice del Excel per Docker)"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        export_data = {
            "generato_il": datetime.now().isoformat(),
            "totale_prenotazioni": len(bookings),
            "prenotazioni": bookings
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ JSON creato: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Errore creazione JSON: {e}")
        return None

def create_summary_html(bookings, filename="/app/exports/cetma_prenotazioni.html"):
    """Crea un riassunto HTML semplice"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prenotazioni CETMA</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5; 
        }}
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
        }}
        h1 {{ 
            color: #366092; 
            text-align: center; 
            margin-bottom: 10px; 
        }}
        .subtitle {{ 
            text-align: center; 
            color: #666; 
            margin-bottom: 30px; 
        }}
        table {{ 
            border-collapse: collapse; 
            width: 100%; 
            margin-top: 20px; 
            font-size: 14px; 
        }}
        th, td {{ 
            border: 1px solid #ddd; 
            padding: 12px 8px; 
            text-align: left; 
        }}
        th {{ 
            background-color: #366092; 
            color: white; 
            font-weight: bold; 
            position: sticky; 
            top: 0; 
        }}
        tr:nth-child(even) {{ 
            background-color: #f8f9fa; 
        }}
        tr:hover {{ 
            background-color: #e3f2fd; 
        }}
        .stats {{ 
            background: linear-gradient(135deg, #366092, #4a90c2); 
            color: white; 
            padding: 20px; 
            border-radius: 8px; 
            margin-bottom: 30px; 
            text-align: center; 
        }}
        .no-data {{ 
            text-align: center; 
            color: #666; 
            font-style: italic; 
            padding: 40px; 
        }}
        .area-tag {{ 
            background-color: #e3f2fd; 
            padding: 4px 8px; 
            border-radius: 12px; 
            font-size: 12px; 
            white-space: nowrap; 
        }}
        @media (max-width: 768px) {{
            .container {{ padding: 15px; }}
            table {{ font-size: 12px; }}
            th, td {{ padding: 8px 4px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏢 Centro Ricerche CETMA</h1>
        <p class="subtitle">Sistema Gestione Prenotazioni Aree</p>
        
        <div class="stats">
            <h2 style="margin: 0 0 10px 0;">📊 Dashboard Prenotazioni</h2>
            <p style="margin: 0;"><strong>{len(bookings)}</strong> prenotazioni totali</p>
            <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 14px;">
                Aggiornato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}
            </p>
        </div>
"""
        
        if not bookings:
            html_content += '<div class="no-data">❌ Nessuna prenotazione trovata.</div>'
        else:
            html_content += """
        <div style="overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>👤 Visitatore</th>
                        <th>🏛️ Area</th>
                        <th>📅 Data</th>
                        <th>🕐 Orario</th>
                        <th>⏱️ Durata</th>
                        <th>📧 Email</th>
                        <th>📞 Telefono</th>
                        <th>📝 Motivo</th>
                        <th>📊 Status</th>
                    </tr>
                </thead>
                <tbody>
"""
            for booking in bookings:
                html_content += f"""
                    <tr>
                        <td><strong>#{booking.get('id', 'N/A')}</strong></td>
                        <td>{booking.get('visitor_name', 'N/A')}</td>
                        <td><span class="area-tag">{booking.get('booking_area', 'N/A')}</span></td>
                        <td>{booking.get('booking_date', 'N/A')}</td>
                        <td>{booking.get('booking_time', 'N/A')}</td>
                        <td>{booking.get('booking_duration', 'N/A')}</td>
                        <td><a href="mailto:{booking.get('visitor_email', '')}">{booking.get('visitor_email', 'N/A')}</a></td>
                        <td><a href="tel:{booking.get('visitor_phone', '')}">{booking.get('visitor_phone', 'N/A')}</a></td>
                        <td>{booking.get('booking_purpose', 'N/A')}</td>
                        <td>✅ {booking.get('status', 'confirmed').title()}</td>
                    </tr>
"""
        
        html_content += """
                </tbody>
            </table>
        </div>
        """
        
        html_content += """
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666; font-size: 12px;">
            <p>🏢 CETMA - Centro di Ricerche Europeo di Tecnologie Design e Materiali</p>
            <p>📍 Cittadella della Ricerca, Brindisi | 📞 0831-201218</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML creato: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Errore creazione HTML: {e}")
        return None

def main():
    """Funzione principale per Docker"""
    print("📋 ESPORTATORE PRENOTAZIONI CETMA (Docker)")
    print("=" * 55)
    
    try:
        # Importa database
        from database import CetmaBookingDatabase
        
        # Ottieni prenotazioni
        db = CetmaBookingDatabase()
        bookings = db.get_all_bookings()
        
        print(f"📊 Trovate {len(bookings)} prenotazioni")
        print(f"💾 Database tipo: {'MEMORIA' if getattr(db, 'in_memory', False) else 'FILE'}")
        
        # Esporta in directory condivisa
        files_created = []
        
        # CSV
        csv_file = export_to_csv(bookings)
        if csv_file:
            files_created.append(csv_file)
        
        # JSON (più semplice del Excel per Docker)
        json_file = export_to_json(bookings)
        if json_file:
            files_created.append(json_file)
        
        # HTML
        html_file = create_summary_html(bookings)
        if html_file:
            files_created.append(html_file)
        
        # Riepilogo
        print(f"\n🎉 ESPORTAZIONE COMPLETATA!")
        print(f"📁 File creati in /app/exports/ (disponibili sull'host):")
        for file in files_created:
            container_path = file
            host_path = file.replace('/app/exports/', './exports/')
            print(f"   • {os.path.basename(file)}")
            print(f"     Container: {container_path}")
            print(f"     Host: {host_path}")
        
        if files_created:
            print(f"\n💡 Per accedere ai file dall'host:")
            print(f"   • CSV: Apri con Excel/LibreOffice")
            print(f"   • HTML: Apri nel browser")
            print(f"   • JSON: Per sviluppatori/script")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()