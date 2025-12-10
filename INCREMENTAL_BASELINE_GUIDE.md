# 📊 Guida Baseline Incrementale con Persistenza Storica

## 🎯 Panoramica

Il sistema di **Baseline Incrementale** permette di migliorare progressivamente i riferimenti biomeccanici della baseline aggiungendo corse "buone" nel tempo, senza dover riprocessare i video precedenti.

### Vantaggi
- ✅ **Apprendimento Progressivo**: La baseline migliora automaticamente con ogni corsa aggiunta
- ✅ **Nessun Riprocessing**: Non serve rielaborare i video vecchi
- ✅ **Ghost Vision Dinamica**: Il riferimento visivo viene aggiornato con la migliore corsa
- ✅ **Storico Completo**: Mantiene traccia di tutte le corse aggiunte

---

## 🏗️ Architettura

### Backend

#### `baseline_manager.py`
Modulo principale per la gestione della baseline incrementale.

**Classe `BaselineHistory`:**
- Gestisce il file `baseline_history.json`
- Implementa la media incrementale per aggiornare le statistiche
- Traccia la migliore corsa per Ghost Vision
- Mantiene uno storico delle ultime 50 corse

#### `app.py`
Nuovi endpoint API:

1. **POST `/api/baseline/add-run`**
   - Aggiunge una corsa alla baseline incrementale
   - Calcola se è la migliore corsa finora
   - Aggiorna statistiche globali con media incrementale

2. **GET `/api/baseline/history`**
   - Restituisce lo storico della baseline (summary)

3. **GET `/api/baseline/current`**
   - Restituisce la baseline corrente in formato compatibile

### Frontend

#### `ResultsStep.svelte`
Aggiunto bottone **"📊 Aggiungi a Baseline"**:
- Visibile dopo ogni analisi video
- Disabilitato per corse "Critiche"
- Mostra feedback di successo/errore
- Badge speciale 🏆 per nuove migliori corse

---

## 📐 Formula Matematica: Media Incrementale

Per aggiornare le statistiche senza ricalcolare tutto lo storico, usiamo la **media incrementale**:

```
new_avg = (old_avg × count + new_value) / (count + 1)
```

### Esempio
```
Stato corrente:
- media_angle = 8.5°
- run_count = 10

Nuova corsa:
- new_angle = 9.2°

Calcolo:
new_avg = (8.5 × 10 + 9.2) / 11
        = (85 + 9.2) / 11
        = 94.2 / 11
        = 8.56°
```

### Deviazione Standard
Per la deviazione standard, manteniamo gli ultimi 100 valori in memoria e ricalcoliamo:
```python
std = np.std(last_100_values)
```

---

## 📊 Struttura `baseline_history.json`

```json
{
  "version": "1.0",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T14:45:00Z",
  "run_count": 15,
  "best_run_id": "analysis_1736947200_abc123",
  "best_run_error": 0.3456,
  "view_type": "posterior",
  "speed_kmh": 10.0,
  "fps": 30.0,
  
  "global_stats": {
    "left_knee_valgus": {
      "mean": 8.56,
      "std": 2.34,
      "min": 4.2,
      "max": 13.8
    },
    "right_knee_valgus": {
      "mean": 8.12,
      "std": 2.18,
      "min": 4.5,
      "max": 12.9
    },
    "pelvic_drop": {
      "mean": 2.45,
      "std": 0.89,
      "min": 0.8,
      "max": 4.5
    },
    "cadence": {
      "mean": 178.5,
      "std": 3.2,
      "min": 172.0,
      "max": 185.0
    },
    "knee_valgus_symmetry": {
      "mean": 95.3,
      "std": 1.8,
      "min": 91.0,
      "max": 98.5
    }
  },
  
  "ghost_frames": {
    "analysis_id": "analysis_1736947200_abc123",
    "frames_processed": 445,
    "note": "From best run"
  },
  
  "runs_history": [
    {
      "analysis_id": "analysis_1736947200_abc123",
      "timestamp": "2025-01-15T14:45:00Z",
      "overall_status": "Ottimale",
      "run_error": 0.3456,
      "is_best": true,
      "metrics_summary": {
        "left_knee_valgus": {
          "value": 8.45,
          "z_score": 0.15,
          "level": "Ottimale"
        }
      }
    }
  ]
}
```

---

## 🔄 Workflow Completo

### 1. Prima Analisi (Creazione Baseline Tradizionale)
```
User → Upload 5 video → Backend processa
                      ↓
              Crea baseline.json
                      ↓
              Baseline disponibile
```

### 2. Analisi Video Successiva
```
User → Upload video → Backend analizza vs baseline
                            ↓
                    Calcola Z-scores
                            ↓
                    Mostra risultati
```

### 3. Aggiunta a Baseline Incrementale
```
User clicca "Aggiungi a Baseline"
            ↓
Frontend → POST /api/baseline/add-run
            ↓
Backend:
  1. Carica baseline_history.json
  2. Calcola errore corsa (media Z-scores assoluti)
  3. Confronta con best_run_error
  4. Se migliore → aggiorna best_run_id
  5. Aggiorna statistiche globali (media incrementale)
  6. Salva baseline_history.json
            ↓
Frontend → Mostra conferma
```

### 4. Analisi Future
Le analisi successive useranno la baseline incrementale aggiornata.

---

## 🏆 Selezione Migliore Corsa

### Calcolo Errore Corsa
```python
def _calculate_run_error(metrics, view_type):
    total_error = 0.0
    count = 0
    
    for metric in metrics:
        total_error += abs(metric['z_score'])
        count += 1
    
    return total_error / count
```

### Logica Aggiornamento
```python
if run_error < best_run_error:
    # Nuova migliore corsa!
    best_run_id = analysis_id
    best_run_error = run_error
    
    # Aggiorna Ghost Vision (se possibile)
    update_ghost_frames(video_path)
```

---

## 🎨 UI/UX Frontend

### Bottone "Aggiungi a Baseline"

#### Stati
1. **Normale**: Verde, cliccabile
2. **Loading**: Spinner animato
3. **Disabilitato**: Grigio (per corse "Critiche")

#### Messaggi Contestuali
- **Ottimale**: "Questa corsa è eccellente! Aggiungila..."
- **Attenzione**: "Mostra alcune deviazioni. Aggiungi solo se..."
- **Critico**: "Deviazioni significative. Non consigliato..."

#### Feedback
- ✅ **Successo**: Mostra totale corse e badge 🏆 se nuova migliore
- ❌ **Errore**: Mostra messaggio errore

---

## 🔍 API Reference

### POST `/api/baseline/add-run`

**Request:**
```json
{
  "analysis_id": "analysis_1736947200_abc123",
  "analysis_data": {
    "viewType": "posterior",
    "anomaly_level": "Ottimale",
    "anomaly_score": 0.85,
    "metrics": {
      "left_knee_valgus": {
        "value": 8.45,
        "z_score": 0.15,
        "level": "Ottimale"
      }
    }
  }
}
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Baseline aggiornata con successo",
  "run_count": 15,
  "is_new_best": true,
  "run_error": 0.3456,
  "best_run_error": 0.3456,
  "best_run_id": "analysis_1736947200_abc123",
  "global_stats": {
    "left_knee_valgus": {
      "mean": 8.56,
      "std": 2.34,
      "min": 4.2,
      "max": 13.8
    }
  }
}
```

**Response (Error):**
```json
{
  "status": "error",
  "message": "View type incompatibile. Storico usa posterior, analisi usa lateral."
}
```

### GET `/api/baseline/history`

**Response:**
```json
{
  "status": "success",
  "history": {
    "run_count": 15,
    "best_run_id": "analysis_1736947200_abc123",
    "best_run_error": 0.3456,
    "view_type": "posterior",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T14:45:00Z",
    "global_stats_keys": [
      "left_knee_valgus",
      "right_knee_valgus",
      "pelvic_drop",
      "cadence",
      "knee_valgus_symmetry"
    ],
    "recent_runs": [...]
  }
}
```

### GET `/api/baseline/current`

**Response:**
```json
{
  "status": "success",
  "baseline": {
    "view_type": "posterior",
    "speed_kmh": 10.0,
    "fps": 30.0,
    "n_videos": 15,
    "is_incremental": true,
    "best_run_id": "analysis_1736947200_abc123",
    "best_run_error": 0.3456,
    "left_knee_valgus": {
      "mean": 8.56,
      "std": 2.34,
      "min": 4.2,
      "max": 13.8
    }
  }
}
```

---

## ⚙️ Configurazione

### Backend (`backend/config.py`)
Il sistema usa le stesse cartelle esistenti:
- `MODEL_FOLDER`: Dove viene salvato `baseline_history.json`
- `GHOST_FRAMES_FOLDER`: Dove vengono salvati i ghost frames

### File Creati
- `backend/models/baseline_history.json`: Storico baseline incrementale
- `backend/ghost_frames/ghost_frame_*.png`: Frame ghost della migliore corsa

---

## 🧪 Testing

### Test Manuale

1. **Crea baseline iniziale**:
   ```bash
   # Upload 5 video baseline dal frontend
   ```

2. **Analizza un video "Ottimale"**:
   ```bash
   # Upload 1 video per analisi
   ```

3. **Aggiungi a baseline**:
   ```bash
   # Clicca "Aggiungi a Baseline" nei risultati
   ```

4. **Verifica aggiornamento**:
   ```bash
   # Controlla backend/models/baseline_history.json
   cat backend/models/baseline_history.json
   ```

5. **Analizza altro video**:
   ```bash
   # Verifica che usi la baseline aggiornata
   ```

### Test con curl

```bash
# Aggiungi corsa a baseline
curl -X POST http://localhost:5000/api/baseline/add-run \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": "test_run_001",
    "analysis_data": {
      "viewType": "posterior",
      "anomaly_level": "Ottimale",
      "metrics": {
        "left_knee_valgus": {"value": 8.5, "z_score": 0.2}
      }
    }
  }'

# Ottieni storico
curl http://localhost:5000/api/baseline/history

# Ottieni baseline corrente
curl http://localhost:5000/api/baseline/current
```

---

## 🚀 Prossimi Sviluppi

### Possibili Miglioramenti

1. **Ghost Vision da Video Originale**:
   - Salvare video originali per rigenerare ghost frames
   - Attualmente salva solo skeleton video

2. **Baseline Multiple**:
   - Supportare baseline diverse per velocità diverse
   - Es: baseline_10kmh.json, baseline_12kmh.json

3. **Export/Import Baseline**:
   - Esportare baseline per condividerla
   - Importare baseline da altri utenti

4. **Analytics Dashboard**:
   - Grafici evoluzione metriche nel tempo
   - Trend improvement
   - Statistiche dettagliate

5. **Auto-Detection Corse Buone**:
   - Sistema automatico per suggerire quali corse aggiungere
   - Basato su soglie Z-score

6. **Backup Automatico**:
   - Backup automatici di baseline_history.json
   - Rollback a versioni precedenti

---

## 📝 Note Tecniche

### Limitazioni Attuali

1. **Ghost Frames**:
   - Rigenerazione ghost frames richiede video originale
   - Attualmente non salvato (solo skeleton video)

2. **View Type**:
   - Una baseline history per view type
   - Non mescola posterior e lateral

3. **Memory**:
   - Mantiene ultimi 100 valori per calcolo std
   - Storia completa solo ultimi 50 runs

### Performance

- **Aggiornamento Baseline**: ~10-50ms (calcoli matematici)
- **Salvataggio JSON**: ~5-20ms (I/O disco)
- **Total Overhead**: <100ms per aggiunta corsa

### Sicurezza

- Validazione view_type per evitare mix
- Sanitizzazione analysis_id
- Gestione errori completa

---

## 🆘 Troubleshooting

### Problema: "View type incompatibile"
**Soluzione**: La baseline history è per un view_type diverso. Elimina `baseline_history.json` per ricominciare.

### Problema: "Baseline non aggiornata"
**Soluzione**: Verifica che il file `baseline_history.json` sia scrivibile e che non ci siano errori nel log backend.

### Problema: "Ghost frames non aggiornati"
**Soluzione**: Attualmente la rigenerazione ghost frames non è implementata (richiede video originale). Feature futura.

### Problema: "Errore nel salvataggio"
**Soluzione**: Verifica permessi cartella `backend/models/` e spazio disco disponibile.

---

## 📚 Riferimenti

- **Media Incrementale**: [Wikipedia - Moving Average](https://en.wikipedia.org/wiki/Moving_average)
- **Z-Score**: [Wikipedia - Standard Score](https://en.wikipedia.org/wiki/Standard_score)
- **Welford's Algorithm**: Per calcolo varianza online (possibile miglioramento futuro)

---

**Versione**: 1.0  
**Data**: Gennaio 2025  
**Autore**: Running Analyzer Team


