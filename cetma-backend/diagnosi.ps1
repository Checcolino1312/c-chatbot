# diagnosi.ps1 - Script Diagnosi CETMA per Windows
# Salva questo file come "diagnosi.ps1" e eseguilo con: .\diagnosi.ps1

Write-Host "🔍 DIAGNOSI SISTEMA PRENOTAZIONI CETMA" -ForegroundColor Yellow
Write-Host "======================================" -ForegroundColor Yellow
Write-Host ""

# 1. Directory corrente
Write-Host "📍 1. DIRECTORY CORRENTE:" -ForegroundColor Cyan
Write-Host "   $(Get-Location)" -ForegroundColor White
Write-Host ""

# 2. Database principale
Write-Host "📊 2. DATABASE PRINCIPALE:" -ForegroundColor Cyan
if (Test-Path "cetma_bookings.db") {
    $db = Get-Item "cetma_bookings.db"
    Write-Host "   ✅ TROVATO: cetma_bookings.db" -ForegroundColor Green
    Write-Host "   📏 Dimensione: $([math]::Round($db.Length/1KB, 2)) KB" -ForegroundColor White
    Write-Host "   📅 Modificato: $($db.LastWriteTime)" -ForegroundColor White
} else {
    Write-Host "   ❌ NON TROVATO: cetma_bookings.db" -ForegroundColor Red
}
Write-Host ""

# 3. Directory exports
Write-Host "📁 3. DIRECTORY EXPORTS:" -ForegroundColor Cyan
if (Test-Path "exports" -PathType Container) {
    Write-Host "   ✅ TROVATA: Directory exports" -ForegroundColor Green
    $exportFiles = Get-ChildItem "exports" -ErrorAction SilentlyContinue
    if ($exportFiles) {
        Write-Host "   📄 Contenuto:" -ForegroundColor White
        $exportFiles | ForEach-Object { 
            Write-Host "      • $($_.Name) ($([math]::Round($_.Length/1KB, 2)) KB)" -ForegroundColor Gray
        }
    } else {
        Write-Host "   📭 Directory vuota" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ NON TROVATA: Directory exports" -ForegroundColor Red
}
Write-Host ""

# 4. File di backup specifici
Write-Host "📄 4. FILE DI BACKUP:" -ForegroundColor Cyan
$backupFiles = @(
    "exports\prenotazioni_backup.txt",
    "exports\cetma_prenotazioni.csv",
    "exports\cetma_prenotazioni.html", 
    "exports\cetma_prenotazioni.json"
)

foreach ($file in $backupFiles) {
    if (Test-Path $file) {
        $fileInfo = Get-Item $file
        Write-Host "   ✅ $file ($([math]::Round($fileInfo.Length/1KB, 2)) KB)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $file" -ForegroundColor Red
    }
}
Write-Host ""

# 5. Container Docker
Write-Host "🐳 5. CONTAINER DOCKER:" -ForegroundColor Cyan
try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Write-Host "   ✅ Docker installato: $dockerVersion" -ForegroundColor Green
        
        # Container attivi
        $containers = docker ps --format "{{.Names}}" 2>$null | Where-Object { $_ -match "cetma" }
        if ($containers) {
            Write-Host "   🟢 Container CETMA attivi:" -ForegroundColor Green
            $containers | ForEach-Object { Write-Host "      • $_" -ForegroundColor Gray }
        } else {
            Write-Host "   🔴 Nessun container CETMA attivo" -ForegroundColor Red
            Write-Host "   💡 Prova: docker-compose up -d" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "   ❌ Docker non disponibile" -ForegroundColor Red
}
Write-Host ""

# 6. File Python
Write-Host "🐍 6. SCRIPT PYTHON:" -ForegroundColor Cyan
$pythonFiles = @("database.py", "export_bookings.py", "actions\actions.py")
foreach ($file in $pythonFiles) {
    if (Test-Path $file) {
        Write-Host "   ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $file" -ForegroundColor Red
    }
}
Write-Host ""

# 7. Ricerca altri DB
Write-Host "🔍 7. ALTRI FILE DATABASE:" -ForegroundColor Cyan
$allDbFiles = Get-ChildItem -Recurse -Filter "*.db" -ErrorAction SilentlyContinue
if ($allDbFiles) {
    Write-Host "   📊 Database trovati:" -ForegroundColor Green
    $allDbFiles | ForEach-Object {
        Write-Host "      • $($_.FullName) ($([math]::Round($_.Length/1KB, 2)) KB)" -ForegroundColor Gray
    }
} else {
    Write-Host "   ❌ Nessun file .db trovato" -ForegroundColor Red
}
Write-Host ""

# 8. VERDETTO FINALE
Write-Host "🎯 VERDETTO FINALE:" -ForegroundColor Yellow
Write-Host "==================" -ForegroundColor Yellow

if (Test-Path "cetma_bookings.db") {
    $dbSize = (Get-Item "cetma_bookings.db").Length
    if ($dbSize -gt 1024) {
        Write-Host "✅ PERFETTO! Database principale esiste e contiene dati" -ForegroundColor Green
        Write-Host "   🔧 PROSSIMO PASSO: Verifica contenuto con SQLite" -ForegroundColor Cyan
        Write-Host "   💻 COMANDO: sqlite3 cetma_bookings.db `"SELECT * FROM cetma_bookings;`"" -ForegroundColor White
    } else {
        Write-Host "⚠️ Database esiste ma è vuoto o molto piccolo" -ForegroundColor Yellow
        Write-Host "   🔧 PROSSIMO PASSO: Test con prenotazione di prova" -ForegroundColor Cyan
    }
} elseif (Test-Path "exports" -and (Get-ChildItem "exports" -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️ Database principale mancante, ma backup disponibili" -ForegroundColor Yellow
    Write-Host "   🔧 PROSSIMO PASSO: Controlla file nella directory exports" -ForegroundColor Cyan
} else {
    Write-Host "❌ NESSUN FILE DI PRENOTAZIONE TROVATO" -ForegroundColor Red
    Write-Host "   🔧 PROSSIMI PASSI:" -ForegroundColor Cyan
    Write-Host "      1. Avvia i container: docker-compose up -d" -ForegroundColor White
    Write-Host "      2. Fai una prenotazione di test via web" -ForegroundColor White
    Write-Host "      3. Controlla di nuovo i file" -ForegroundColor White
}

Write-Host ""
Write-Host "🚀 COMANDI RAPIDI:" -ForegroundColor Yellow
Write-Host "   • Avvia sistema: docker-compose up -d" -ForegroundColor White
Write-Host "   • Log errori: docker logs rasa-action-server-cetma" -ForegroundColor White
Write-Host "   • Esporta dati: docker exec -it rasa-action-server-cetma python export_bookings_docker.py" -ForegroundColor White
Write-Host "   • Test Python: python database.py" -ForegroundColor White
Write-Host ""
Write-Host "Diagnosi completata! 🏁" -ForegroundColor Yellow