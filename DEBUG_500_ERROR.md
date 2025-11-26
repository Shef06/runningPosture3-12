# 🐛 Debug: Errore 500 nella Creazione Baseline

## ❌ Problema

Errore 500 (INTERNAL SERVER ERROR) quando si tenta di creare la baseline.

## 🔍 Diagnostica

### Step 1: Controlla i Log del Server

**IMPORTANTE**: I log del server Flask mostrano l'errore esatto. Cerca:

```bash
# Nel terminale dove gira il server Flask, cerca:
❌ Errore nella creazione baseline: ...
⚠ Errore nell'elaborazione video ...
```

### Step 2: Verifica Setup

```python
# Test rapido in Python
from pose_engine import PoseEngine
import os

# Verifica directory
print("MODEL_FOLDER:", os.path.exists("backend/models"))
print("UPLOAD_FOLDER:", os.path.exists("backend/uploads"))

# Test PoseEngine
engine = PoseEngine()
print("PoseEngine creato OK")
```

### Step 3: Test Singolo Video

```python
# Test processing singolo video
from pose_engine import PoseEngine

engine = PoseEngine()
result = engine.process_video('path/to/video.mp4', fps=30)
print(result)
```

## 🔧 Modifiche Implementate per Debug

### 1. Logging Dettagliato
- Log all'inizio di ogni fase
- Log per ogni video processato
- Log per ogni errore con stack trace completo

### 2. Gestione Errori Migliorata
- Try/except in `process_single_video`
- Raccoglimento errori invece di crash immediato
- Messaggi di errore dettagliati nel JSON di risposta

### 3. Verifiche Aggiuntive
- Verifica esistenza video prima del processing
- Verifica dimensione video (non vuoto)
- Verifica directory models prima di salvare

## 📋 Checklist Debug

1. **Server Flask in esecuzione?**
   ```bash
   curl http://localhost:5000/api/health
   ```

2. **Video validi?**
   - Formato supportato (.mp4, .avi, .mov, .mkv, .webm)
   - Dimensione > 0
   - Leggibili da OpenCV

3. **Directory esistenti?**
   - `backend/models/` deve esistere
   - `backend/uploads/` deve esistere
   - Permessi di scrittura

4. **Dipendenze installate?**
   ```bash
   pip install -r requirements.txt
   ```

5. **MediaPipe funziona?**
   ```python
   import mediapipe as mp
   pose = mp.solutions.pose.Pose()
   print("MediaPipe OK")
   ```

## 🧪 Test Manuale

### Test 1: Health Check
```bash
curl http://localhost:5000/api/health
```
**Atteso**: `{"status": "success", ...}`

### Test 2: Creazione Baseline (cURL)
```bash
curl -X POST http://localhost:5000/api/create_baseline \
  -F "videos=@video1.mp4" \
  -F "videos=@video2.mp4" \
  -F "videos=@video3.mp4" \
  -F "videos=@video4.mp4" \
  -F "videos=@video5.mp4" \
  -F "speed=10.0" \
  -F "fps=30"
```

**Controlla risposta JSON** per messaggio di errore dettagliato.

## 📊 Log Attesi (Successo)

```
📥 Richiesta creazione baseline ricevuta
=== Creazione Baseline ===
Video salvati: ['video1.mp4', 'video2.mp4', ...]
📊 Parametri baseline: Velocità=10.0 km/h, FPS=30.0
Fase 1: Processing video con PoseEngine (parallelo)...
Processing video 1/5: video1.mp4
=== Inizio processing video: ...
✓ Completato video 1/5: video1.mp4
...
Fase 2: Creazione statistiche baseline...
  ✓ Statistiche calcolate: 4 metriche
Fase 3: Salvataggio baseline in: ...
  ✓ Baseline salvata con successo
✅ Baseline creata con successo!
```

## 📊 Log Attesi (Errore)

```
📥 Richiesta creazione baseline ricevuta
=== Creazione Baseline ===
...
⚠ Errore nell'elaborazione video 1/5: TypeError: ...
❌ Fallimento processing: 0/5 video processati. Errori: ...
```

**Copia l'errore completo** dai log per debug.

## 🔄 Prossimi Passi

1. **Copia i log completi** del server quando provi a creare la baseline
2. **Condividi l'errore specifico** (tipo, messaggio, stack trace)
3. **Verifica i video** siano validi e leggibili
4. **Testa con un singolo video** per isolare il problema

---

**Con i log dettagliati, possiamo identificare esattamente dove fallisce!**

