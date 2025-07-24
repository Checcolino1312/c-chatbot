const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors({
  origin: ['http://localhost:4200', 'http://127.0.0.1:4200'],
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true
}));
app.use(express.json());

// Database SQLite con SCRITTURA abilitata
const dbPath = '/app/data_persistent/cetma_bookings.db';
const db = new sqlite3.Database(dbPath, sqlite3.OPEN_READWRITE, (err) => {
  if (err) {
    console.error('Errore connessione database:', err.message);
  } else {
    console.log('✅ Connesso al database SQLite (modalità lettura/scrittura)');
  }
});

// Utility
const sendResponse = (res, success, data = null, message = '', error = '') => {
  res.json({ success, data, message, error });
};

// ========== OPERAZIONI LETTURA (esistenti) ==========
app.get('/api/bookings', (req, res) => {
  let query = 'SELECT * FROM cetma_bookings';
  const params = [];
  const conditions = [];

  // Filtri opzionali
  if (req.query.date) {
    conditions.push('booking_date = ?');
    params.push(req.query.date);
  }
  if (req.query.area) {
    conditions.push('booking_area = ?');
    params.push(req.query.area);
  }
  if (req.query.status) {
    conditions.push('status = ?');
    params.push(req.query.status);
  }

  if (conditions.length > 0) {
    query += ' WHERE ' + conditions.join(' AND ');
  }
  query += ' ORDER BY booking_date DESC, booking_time DESC';

  db.all(query, params, (err, rows) => {
    if (err) {
      console.error('Errore recupero prenotazioni:', err.message);
      sendResponse(res, false, null, '', 'Errore nel recupero delle prenotazioni');
    } else {
      sendResponse(res, true, rows, 'Prenotazioni recuperate con successo');
    }
  });
});

app.get('/api/bookings/:id', (req, res) => {
  const id = parseInt(req.params.id);
  if (isNaN(id)) {
    return sendResponse(res, false, null, '', 'ID non valido');
  }

  db.get('SELECT * FROM cetma_bookings WHERE id = ?', [id], (err, row) => {
    if (err) {
      console.error('Errore recupero prenotazione:', err.message);
      sendResponse(res, false, null, '', 'Errore nel recupero della prenotazione');
    } else if (!row) {
      sendResponse(res, false, null, '', 'Prenotazione non trovata');
    } else {
      sendResponse(res, true, row, 'Prenotazione recuperata con successo');
    }
  });
});

// ========== NUOVE OPERAZIONI SCRITTURA ==========

// PUT /api/bookings/:id - AGGIORNA prenotazione completa
app.put('/api/bookings/:id', (req, res) => {
  const id = parseInt(req.params.id);
  if (isNaN(id)) {
    return sendResponse(res, false, null, '', 'ID non valido');
  }

  const {
    visitor_name,
    visitor_email,
    visitor_phone,
    booking_area,
    booking_date,
    booking_time,
    booking_duration,
    booking_purpose,
    status
  } = req.body;

  // Validazione base
  if (!visitor_name || !visitor_email || !booking_area || !booking_date) {
    return sendResponse(res, false, null, '', 'Campi obbligatori mancanti');
  }

  const updateQuery = `
    UPDATE cetma_bookings 
    SET visitor_name = ?, visitor_email = ?, visitor_phone = ?, 
        booking_area = ?, booking_date = ?, booking_time = ?, 
        booking_duration = ?, booking_purpose = ?, status = ?,
        updated_at = datetime('now')
    WHERE id = ?
  `;

  db.run(updateQuery, [
    visitor_name, visitor_email, visitor_phone,
    booking_area, booking_date, booking_time,
    booking_duration, booking_purpose, status || 'pending',
    id
  ], function(err) {
    if (err) {
      console.error('Errore aggiornamento prenotazione:', err.message);
      sendResponse(res, false, null, '', 'Errore durante l\'aggiornamento');
    } else if (this.changes === 0) {
      sendResponse(res, false, null, '', 'Prenotazione non trovata');
    } else {
      // Recupera la prenotazione aggiornata
      db.get('SELECT * FROM cetma_bookings WHERE id = ?', [id], (err, row) => {
        if (err) {
          sendResponse(res, false, null, '', 'Errore nel recupero della prenotazione aggiornata');
        } else {
          sendResponse(res, true, row, 'Prenotazione aggiornata con successo');
        }
      });
    }
  });
});

// PATCH /api/bookings/:id/status - AGGIORNA solo status
app.patch('/api/bookings/:id/status', (req, res) => {
  const id = parseInt(req.params.id);
  const { status } = req.body;

  if (isNaN(id)) {
    return sendResponse(res, false, null, '', 'ID non valido');
  }

  if (!status || !['pending', 'confirmed', 'cancelled'].includes(status)) {
    return sendResponse(res, false, null, '', 'Status non valido');
  }

  const updateQuery = `
    UPDATE cetma_bookings 
    SET status = ?, updated_at = datetime('now')
    WHERE id = ?
  `;

  db.run(updateQuery, [status, id], function(err) {
    if (err) {
      console.error('Errore aggiornamento status:', err.message);
      sendResponse(res, false, null, '', 'Errore durante l\'aggiornamento dello status');
    } else if (this.changes === 0) {
      sendResponse(res, false, null, '', 'Prenotazione non trovata');
    } else {
      // Recupera la prenotazione aggiornata
      db.get('SELECT * FROM cetma_bookings WHERE id = ?', [id], (err, row) => {
        if (err) {
          sendResponse(res, false, null, '', 'Errore nel recupero della prenotazione aggiornata');
        } else {
          sendResponse(res, true, row, 'Status aggiornato con successo');
        }
      });
    }
  });
});

// DELETE /api/bookings/:id - ELIMINA prenotazione
app.delete('/api/bookings/:id', (req, res) => {
  const id = parseInt(req.params.id);
  if (isNaN(id)) {
    return sendResponse(res, false, null, '', 'ID non valido');
  }

  // Prima controlla se la prenotazione esiste
  db.get('SELECT * FROM cetma_bookings WHERE id = ?', [id], (err, row) => {
    if (err) {
      console.error('Errore verifica prenotazione:', err.message);
      return sendResponse(res, false, null, '', 'Errore durante la verifica');
    } else if (!row) {
      return sendResponse(res, false, null, '', 'Prenotazione non trovata');
    } else {
      // Elimina la prenotazione
      db.run('DELETE FROM cetma_bookings WHERE id = ?', [id], function(err) {
        if (err) {
          console.error('Errore eliminazione prenotazione:', err.message);
          sendResponse(res, false, null, '', 'Errore durante l\'eliminazione');
        } else {
          sendResponse(res, true, null, 'Prenotazione eliminata con successo');
        }
      });
    }
  });
});

// Gestione errori 404
app.use('*', (req, res) => {
  sendResponse(res, false, null, '', 'Endpoint non trovato');
});

// Avvio server
app.listen(PORT, () => {
  console.log(`🚀 Server CRUD completo in esecuzione su porta ${PORT}`);
  console.log(`📂 Database: ${dbPath}`);
  console.log('📋 Endpoints CRUD disponibili:');
  console.log('   GET    /api/bookings - Lista prenotazioni');
  console.log('   GET    /api/bookings/:id - Prenotazione specifica');
  console.log('   PUT    /api/bookings/:id - Aggiorna prenotazione');
  console.log('   PATCH  /api/bookings/:id/status - Aggiorna status');
  console.log('   DELETE /api/bookings/:id - Elimina prenotazione');
});

// Chiusura database
process.on('SIGINT', () => {
  console.log('\n🔌 Chiusura connessione database...');
  db.close((err) => {
    if (err) {
      console.error('Errore chiusura database:', err.message);
    } else {
      console.log('✅ Database chiuso correttamente');
    }
    process.exit(0);
  });
});