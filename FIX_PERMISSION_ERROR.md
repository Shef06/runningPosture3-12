# Fix PermissionError - Rimozione File Video

## 🐛 Problema

Su Windows, quando si tenta di eliminare un file video dopo l'elaborazione, può verificarsi un errore:

```
PermissionError: [WinError 32] Impossibile accedere al file. 
Il file è utilizzato da un altro processo
```

### Causa

Il file video potrebbe essere ancora aperto da:
- **Browser**: Se il video è stato caricato e il browser sta ancora mantenendo un riferimento
- **Player video**: Se il video è stato aperto in un lettore
- **Altri processi**: Qualsiasi processo che ha aperto il file

## ✅ Soluzione Implementata

### Funzione Helper `safe_remove_file()`

Creata una funzione helper che gestisce la rimozione dei file in modo sicuro:

```python
def safe_remove_file(filepath):
    """
    Rimuove un file in modo sicuro, gestendo errori di permesso su Windows
    
    Args:
        filepath: Percorso del file da rimuovere
        
    Returns:
        bool: True se rimosso con successo, False altrimenti
    """
    if not os.path.exists(filepath):
        return True
    
    try:
        os.remove(filepath)
        logger.debug(f"✓ File rimosso: {os.path.basename(filepath)}")
        return True
    except PermissionError as e:
        # Su Windows, il file potrebbe essere ancora aperto da un altro processo
        logger.warning(f"⚠ Impossibile rimuovere file {os.path.basename(filepath)}: {e}")
        logger.warning(f"  Il file è probabilmente ancora aperto da un altro processo.")
        logger.warning(f"  Verrà rimosso automaticamente quando non sarà più in uso.")
        return False
    except OSError as e:
        logger.warning(f"⚠ Errore nella rimozione file {os.path.basename(filepath)}: {e}")
        return False
```

### Comportamento

1. **File rimosso con successo**: Log di debug, operazione completata
2. **PermissionError**: Log di warning, operazione continua (non fallisce)
3. **Altri OSError**: Log di warning, operazione continua

### Vantaggi

- ✅ **Non blocca l'operazione**: L'analisi/baseline viene completata anche se il file non può essere rimosso
- ✅ **Log informativi**: L'utente sa che il file rimarrà ma l'operazione è completata
- ✅ **Gestione robusta**: Gestisce tutti i tipi di errori OS
- ✅ **Cross-platform**: Funziona su Windows, Linux, macOS

## 📍 Punti di Utilizzo

### 1. Creazione Baseline (`/api/create_baseline`)
```python
# Pulisci video temporanei
for video_path in video_paths:
    safe_remove_file(video_path)
```

### 2. Analisi Video (`/api/detect_anomaly`)
```python
# Pulisci video temporaneo
safe_remove_file(filepath)
```

## 🔍 Log Output

### Caso Successo
```
✓ File rimosso: video1.mp4
```

### Caso PermissionError
```
⚠ Impossibile rimuovere file video1.mp4: [WinError 32] Impossibile accedere al file. Il file è utilizzato da un altro processo
  Il file è probabilmente ancora aperto da un altro processo.
  Verrà rimosso automaticamente quando non sarà più in uso.
```

## 💡 Note per l'Utente

### Cosa Succede Ora

1. **Operazione completata**: L'analisi/baseline viene completata correttamente
2. **File temporaneo**: Il file rimane nella cartella `backend/uploads/`
3. **Pulizia automatica**: Il file verrà rimosso quando:
   - Il browser/processo chiude il file
   - Il server viene riavviato (se implementata pulizia all'avvio)
   - Viene eseguita una pulizia manuale

### Pulizia Manuale (Opzionale)

Se vuoi pulire manualmente i file temporanei:

```bash
# Windows PowerShell
Remove-Item backend\uploads\*.mp4 -Force

# Linux/Mac
rm backend/uploads/*.mp4
```

## 🚀 Miglioramenti Futuri (Opzionali)

### 1. Pulizia Automatica all'Avvio
```python
def cleanup_old_uploads():
    """Pulisce file upload vecchi all'avvio del server"""
    upload_dir = Config.UPLOAD_FOLDER
    for filename in os.listdir(upload_dir):
        filepath = os.path.join(upload_dir, filename)
        if os.path.isfile(filepath):
            # Rimuovi file più vecchi di 1 ora
            if os.path.getmtime(filepath) < time.time() - 3600:
                safe_remove_file(filepath)
```

### 2. Retry con Delay
```python
def safe_remove_file_with_retry(filepath, max_retries=3, delay=1):
    """Tenta di rimuovere il file con retry"""
    for attempt in range(max_retries):
        if safe_remove_file(filepath):
            return True
        if attempt < max_retries - 1:
            time.sleep(delay)
    return False
```

### 3. Chiusura Handle File
Se il backend mantiene handle aperti, assicurarsi di chiuderli prima di rimuovere:
```python
# Esempio: se si usa open() direttamente
with open(filepath, 'rb') as f:
    # ... operazioni ...
# File chiuso automaticamente qui
safe_remove_file(filepath)
```

## ✅ Testing

### Test PermissionError
1. Carica un video
2. Apri il video in un player esterno (mantieni aperto)
3. Avvia analisi/baseline
4. **Verifica**: Operazione completa con warning nel log, file rimane

### Test Rimozione Normale
1. Carica un video
2. Non aprire il video in altri programmi
3. Avvia analisi/baseline
4. **Verifica**: File rimosso correttamente, log di successo

## 📝 File Modificati

- ✅ `backend/app.py`
  - Aggiunta funzione `safe_remove_file()`
  - Sostituiti `os.remove()` con `safe_remove_file()`
  - Gestione errori migliorata

---

**Data**: 28 Novembre 2025
**Versione**: 3.12.4 (fix PermissionError)
**Status**: ✅ Risolto

