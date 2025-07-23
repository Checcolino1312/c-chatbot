const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
// Middleware CORS specifico per Angular
app.use(cors({
  origin: ['http://localhost:4200', 'http://127.0.0.1:4200'],
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true
}));
app.use(express.json());

// Connessione al database SQLite (sola lettura)
// Il database è in ../data_persistent/ rispetto al backend
const dbPath = '/app/data_persistent/cetma_bookings.db';
const db = new sqlite3.Database(dbPath, sqlite3.OPEN_READONLY, (err) => {
  if (err) {
    console.error('Errore connessione database:', err.message);
  } else {
    console.log('Connesso al database SQLite (modalità sola lettura)');
  }
});

// Utilità per gestire le risposte
const sendResponse = (res, success, data = null, message = '', error = '') => {
  res.json({
    success,
    data,
    message,
    error
  });
};

// ROUTES - SOLO LETTURA

// GET /api/bookings - Recupera tutte le prenotazioni con filtri opzionali
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

  if (req.query.visitor_name) {
    conditions.push('visitor_name LIKE ?');
    params.push(`%${req.query.visitor_name}%`);
  }

  if (req.query.visitor_email) {
    conditions.push('visitor_email LIKE ?');
    params.push(`%${req.query.visitor_email}%`);
  }

  if (conditions.length > 0) {
    query += ' WHERE ' + conditions.join(' AND ');
  }

  // Ordinamento
  const sortBy = req.query.sort || 'booking_date';
  const sortOrder = req.query.order === 'asc' ? 'ASC' : 'DESC';
  
  if (['booking_date', 'booking_time', 'visitor_name', 'booking_area', 'status', 'created_at'].includes(sortBy)) {
    query += ` ORDER BY ${sortBy} ${sortOrder}`;
  } else {
    query += ' ORDER BY booking_date DESC, booking_time DESC';
  }

  // Paginazione
  const page = parseInt(req.query.page) || 1;
  const limit = parseInt(req.query.limit) || 100;
  const offset = (page - 1) * limit;

  if (req.query.page || req.query.limit) {
    query += ` LIMIT ${limit} OFFSET ${offset}`;
  }

  db.all(query, params, (err, rows) => {
    if (err) {
      console.error('Errore recupero prenotazioni:', err.message);
      sendResponse(res, false, null, '', 'Errore nel recupero delle prenotazioni');
    } else {
      // Se è richiesta la paginazione, ottieni anche il conteggio totale
      if (req.query.page || req.query.limit) {
        let countQuery = 'SELECT COUNT(*) as total FROM bookings';
        if (conditions.length > 0) {
          countQuery += ' WHERE ' + conditions.join(' AND ');
        }

        db.get(countQuery, params.slice(0, conditions.length), (err, countResult) => {
          if (err) {
            console.error('Errore conteggio prenotazioni:', err.message);
            sendResponse(res, true, rows, 'Prenotazioni recuperate con successo');
          } else {
            sendResponse(res, true, {
              bookings: rows,
              pagination: {
                page,
                limit,
                total: countResult.total,
                totalPages: Math.ceil(countResult.total / limit)
              }
            }, 'Prenotazioni recuperate con successo');
          }
        });
      } else {
        sendResponse(res, true, rows, 'Prenotazioni recuperate con successo');
      }
    }
  });
});

// GET /api/bookings/:id - Recupera una prenotazione specifica
app.get('/api/bookings/:id', (req, res) => {
  const id = parseInt(req.params.id);

  if (isNaN(id)) {
    return sendResponse(res, false, null, '', 'ID non valido');
  }

  db.get('SELECT * FROM bookings WHERE id = ?', [id], (err, row) => {
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

// GET /api/bookings/stats/summary - Statistiche riassuntive
app.get('/api/bookings/stats/summary', (req, res) => {
  const statsQuery = `
    SELECT 
      COUNT(*) as total,
      COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
      COUNT(CASE WHEN status = 'confirmed' THEN 1 END) as confirmed,
      COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled,
      COUNT(CASE WHEN booking_date = date('now') THEN 1 END) as today,
      COUNT(CASE WHEN booking_date > date('now') AND status != 'cancelled' THEN 1 END) as upcoming
    FROM bookings
  `;

  db.get(statsQuery, [], (err, stats) => {
    if (err) {
      console.error('Errore statistiche:', err.message);
      sendResponse(res, false, null, '', 'Errore nel recupero delle statistiche');
    } else {
      sendResponse(res, true, stats, 'Statistiche recuperate con successo');
    }
  });
});

// GET /api/bookings/stats/by-area - Prenotazioni per area
app.get('/api/bookings/stats/by-area', (req, res) => {
  const areaStatsQuery = `
    SELECT 
      booking_area,
      COUNT(*) as total,
      COUNT(CASE WHEN status = 'confirmed' THEN 1 END) as confirmed,
      COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
      COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled
    FROM bookings
    GROUP BY booking_area
    ORDER BY total DESC
  `;

  db.all(areaStatsQuery, [], (err, rows) => {
    if (err) {
      console.error('Errore statistiche per area:', err.message);
      sendResponse(res, false, null, '', 'Errore nel recupero delle statistiche per area');
    } else {
      sendResponse(res, true, rows, 'Statistiche per area recuperate con successo');
    }
  });
});

// GET /api/bookings/today - Prenotazioni di oggi
app.get('/api/bookings/today', (req, res) => {
  const todayQuery = `
    SELECT * FROM bookings 
    WHERE booking_date = date('now')
    ORDER BY booking_time ASC
  `;

  db.all(todayQuery, [], (err, rows) => {
    if (err) {
      console.error('Errore prenotazioni oggi:', err.message);
      sendResponse(res, false, null, '', 'Errore nel recupero delle prenotazioni di oggi');
    } else {
      sendResponse(res, true, rows, 'Prenotazioni di oggi recuperate con successo');
    }
  });
});

// GET /api/bookings/upcoming - Prossime prenotazioni
app.get('/api/bookings/upcoming', (req, res) => {
  const limit = parseInt(req.query.limit) || 10;
  
  const upcomingQuery = `
    SELECT * FROM bookings 
    WHERE booking_date > date('now') AND status != 'cancelled'
    ORDER BY booking_date ASC, booking_time ASC
    LIMIT ?
  `;

  db.all(upcomingQuery, [limit], (err, rows) => {
    if (err) {
      console.error('Errore prossime prenotazioni:', err.message);
      sendResponse(res, false, null, '', 'Errore nel recupero delle prossime prenotazioni');
    } else {
      sendResponse(res, true, rows, 'Prossime prenotazioni recuperate con successo');
    }
  });
});

// GET /api/bookings/search - Ricerca prenotazioni
app.get('/api/bookings/search', (req, res) => {
  const searchTerm = req.query.q;
  
  if (!searchTerm || searchTerm.trim().length < 2) {
    return sendResponse(res, false, null, '', 'Termine di ricerca troppo corto (minimo 2 caratteri)');
  }

  const searchQuery = `
    SELECT * FROM bookings 
    WHERE visitor_name LIKE ? 
       OR visitor_email LIKE ? 
       OR booking_purpose LIKE ?
       OR booking_area LIKE ?
    ORDER BY booking_date DESC
    LIMIT 50
  `;

  const searchPattern = `%${searchTerm.trim()}%`;
  const params = [searchPattern, searchPattern, searchPattern, searchPattern];

  db.all(searchQuery, params, (err, rows) => {
    if (err) {
      console.error('Errore ricerca:', err.message);
      sendResponse(res, false, null, '', 'Errore nella ricerca');
    } else {
      sendResponse(res, true, rows, `Trovate ${rows.length} prenotazioni`);
    }
  });
});

// GET /api/bookings/range/:start/:end - Prenotazioni in un intervallo di date
app.get('/api/bookings/range/:start/:end', (req, res) => {
  const startDate = req.params.start;
  const endDate = req.params.end;

  // Validazione date
  if (!startDate.match(/^\d{4}-\d{2}-\d{2}$/) || !endDate.match(/^\d{4}-\d{2}-\d{2}$/)) {
    return sendResponse(res, false, null, '', 'Formato date non valido (usa YYYY-MM-DD)');
  }

  if (new Date(startDate) > new Date(endDate)) {
    return sendResponse(res, false, null, '', 'La data di inizio deve essere precedente alla data di fine');
  }

  const rangeQuery = `
    SELECT * FROM bookings 
    WHERE booking_date BETWEEN ? AND ?
    ORDER BY booking_date ASC, booking_time ASC
  `;

  db.all(rangeQuery, [startDate, endDate], (err, rows) => {
    if (err) {
      console.error('Errore intervallo date:', err.message);
      sendResponse(res, false, null, '', 'Errore nel recupero delle prenotazioni per intervallo');
    } else {
      sendResponse(res, true, rows, `Recuperate ${rows.length} prenotazioni dal ${startDate} al ${endDate}`);
    }
  });
});

// GET /api/areas - Lista delle aree disponibili
app.get('/api/areas', (req, res) => {
  const areasQuery = `
    SELECT DISTINCT booking_area, COUNT(*) as booking_count
    FROM bookings 
    GROUP BY booking_area 
    ORDER BY booking_count DESC
  `;

  db.all(areasQuery, [], (err, rows) => {
    if (err) {
      console.error('Errore aree:', err.message);
      sendResponse(res, false, null, '', 'Errore nel recupero delle aree');
    } else {
      sendResponse(res, true, rows, 'Aree recuperate con successo');
    }
  });
});

// Gestione errori 404
app.use('*', (req, res) => {
  sendResponse(res, false, null, '', 'Endpoint non trovato');
});

// Gestione errori generali
app.use((err, req, res, next) => {
  console.error('Errore server:', err);
  sendResponse(res, false, null, '', 'Errore interno del server');
});

// Avvio server
app.listen(PORT, () => {
  console.log(`🚀 Server API (sola lettura) in esecuzione su porta ${PORT}`);
  console.log(`📂 Database: ${dbPath}`);
  console.log('📋 Endpoints disponibili:');
  console.log('   GET /api/bookings - Tutte le prenotazioni');
  console.log('   GET /api/bookings/:id - Prenotazione specifica');
  console.log('   GET /api/bookings/today - Prenotazioni di oggi');
  console.log('   GET /api/bookings/upcoming - Prossime prenotazioni');
  console.log('   GET /api/bookings/stats/summary - Statistiche generali');
  console.log('   GET /api/bookings/stats/by-area - Statistiche per area');
  console.log('   GET /api/bookings/search?q=termine - Ricerca prenotazioni');
  console.log('   GET /api/bookings/range/2025-07-23/2025-07-30 - Prenotazioni in intervallo');
  console.log('   GET /api/areas - Lista aree disponibili');
});

// Gestione chiusura applicazione
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