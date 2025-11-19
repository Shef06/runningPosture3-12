# 🧪 Guida al Testing - Jump Analyzer Pro

## Test di Base

### 1. Verifica Installazione Backend

```bash
cd backend
venv\Scripts\activate
python -c "import flask, tensorflow, cv2, mediapipe; print('Tutte le librerie importate con successo!')"
```

**Output Atteso**: `Tutte le librerie importate con successo!`

### 2. Test Server Flask

```bash
python app.py
```

**Output Atteso**:
```
Server Flask avviato su http://localhost:5000
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### 3. Test Health Endpoint

Apri browser: http://localhost:5000/api/health

**Response Attesa**:
```json
{
  "status": "success",
  "message": "Server attivo e funzionante"
}
```

### 4. Verifica Installazione Frontend

```bash
cd frontend
npm run dev
```

**Output Atteso**:
```
VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

### 5. Test UI

Apri browser: http://localhost:3000

**Verifica**:
- [ ] Header "Jump Analyzer Pro" visibile
- [ ] Sezione "Crea Baseline Biomeccanica" presente
- [ ] Sezione "Analizza Corsa" presente
- [ ] Pulsanti funzionanti (anche se disabilitati inizialmente)
- [ ] Nessun errore nella console (F12)

## Test Funzionali Completi

### Test 1: Creazione Baseline

**Requisiti**:
- 5 video di test (formato .mp4 consigliato)
- Ogni video dovrebbe mostrare una persona in movimento frontale

**Steps**:
1. Apri http://localhost:3000
2. Clicca su "Clicca per selezionare 5 video"
3. Seleziona 5 video
4. Verifica che tutti e 5 appaiano nella lista
5. Clicca "🚀 Crea Baseline"
6. Attendi completamento (può richiedere 2-5 minuti)

**Output Atteso**:
- Progress indicator durante elaborazione
- Messaggio verde di successo
- Dettagli: "X frames processati, Loss finale: Y"

**Verifica Backend**:
```bash
# Controlla che il modello sia stato salvato
ls backend/models/
# Dovrebbe apparire:
# - baseline_model.h5
# - baseline_model_metadata.npy
```

### Test 2: Analisi Anomalia

**Requisiti**:
- 1 video di test (diverso da quelli usati per baseline)
- Baseline già creata (Test 1 completato)

**Steps**:
1. Nella sezione "Analizza Corsa"
2. Clicca "📹 Seleziona Video"
3. Scegli un video
4. Verifica preview video appaia
5. Clicca "🔍 Analizza Corsa"
6. Attendi elaborazione (30-60 secondi)

**Output Atteso**:
- Progress indicator durante analisi
- Sezione "Risultati Analisi" popolata con:
  - Anomaly Score (numero decimale)
  - Badge colorato con livello (Ottimale/Buono/Moderato/Attenzione/Critico)
  - Interpretazione testuale
  - Dettagli tecnici (frames, features)

### Test 3: Validazione Errori

#### Test 3a: Baseline con meno di 5 video
**Steps**: Seleziona solo 3 video, clicca "Crea Baseline"  
**Atteso**: Messaggio errore rosso "Seleziona esattamente 5 video..."

#### Test 3b: Analisi senza baseline
**Steps**: 
1. Rinomina/elimina `backend/models/baseline_model.h5`
2. Prova ad analizzare un video
**Atteso**: Messaggio errore "Modello baseline non trovato. Crea prima una baseline."

#### Test 3c: File non video
**Steps**: Prova a caricare un file .txt o .jpg  
**Atteso**: Messaggio errore o validazione browser

## Test API con cURL/PowerShell

### Test API Baseline (PowerShell)

```powershell
# Prepara i file (modifica i path)
$videos = @(
    "C:\path\to\video1.mp4",
    "C:\path\to\video2.mp4",
    "C:\path\to\video3.mp4",
    "C:\path\to\video4.mp4",
    "C:\path\to\video5.mp4"
)

# Crea form
$form = @{}
foreach ($video in $videos) {
    $form["videos"] = Get-Item $video
}

# Invia richiesta
$response = Invoke-WebRequest -Uri http://localhost:5000/api/create_baseline -Method POST -Form $form
$response.Content
```

### Test API Analisi (PowerShell)

```powershell
$file = Get-Item "C:\path\to\test_video.mp4"
$form = @{ video = $file }
$response = Invoke-WebRequest -Uri http://localhost:5000/api/detect_anomaly -Method POST -Form $form
$response.Content
```

## Test Performance

### Benchmark Estrazione Keypoint

Crea file `test_keypoint_speed.py` in backend:

```python
import time
from keypoint_extractor import KeypointExtractor

extractor = KeypointExtractor()

video_path = "path/to/test_video.mp4"
start = time.time()
keypoints = extractor.extract_from_video(video_path)
end = time.time()

if keypoints is not None:
    fps = keypoints.shape[0] / (end - start)
    print(f"Processati {keypoints.shape[0]} frames in {end-start:.2f}s")
    print(f"FPS: {fps:.2f}")
else:
    print("Errore estrazione")
```

**Run**: `python test_keypoint_speed.py`

**Target**: > 20 FPS su CPU moderna

### Benchmark Training

Misura tempo per creare baseline (annotare in log):
- Estrazione keypoint da 5 video: X minuti
- Calcolo angoli: Y secondi
- Training LSTM: Z minuti
- **Totale**: ~2-5 minuti atteso

## Test Stress

### Test Upload File Grandi

```python
# Crea video test grande (se necessario)
# Prova upload video 400MB
# Verifica che MAX_CONTENT_LENGTH sia rispettato
```

### Test Multipli Utenti Simultanei

Apri 3 browser tabs contemporaneamente e prova operazioni parallele:
- [ ] Backend gestisce richieste multiple
- [ ] Non ci sono race conditions sui file
- [ ] Ogni richiesta riceve risposta corretta

## Test Cross-Browser

### Verifica Frontend su:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (se su Mac)

**Funzionalità da testare**:
- File upload
- Video preview
- Fetch API
- CSS grid layout
- Animazioni

## Test Mobile Responsive

### Resize browser a 768px width

**Verifica**:
- [ ] Grid passa da 2 colonne a 1 colonna
- [ ] Pulsanti e testi leggibili
- [ ] Nessun overflow orizzontale
- [ ] Touch-friendly (pulsanti grandi abbastanza)

## Checklist Test Completa

### Backend
- [ ] Flask server starts without errors
- [ ] Health endpoint risponde
- [ ] MediaPipe importa correttamente
- [ ] TensorFlow importa correttamente
- [ ] Video upload funziona
- [ ] Keypoint extraction funziona
- [ ] Angle calculation funziona
- [ ] LSTM training funziona
- [ ] Model save/load funziona
- [ ] Anomaly detection funziona
- [ ] File cleanup funziona
- [ ] Error handling appropriato

### Frontend
- [ ] Dev server starts without errors
- [ ] Page loads without console errors
- [ ] BaselineUploader renders
- [ ] AnalysisUploader renders
- [ ] File input funziona
- [ ] File validation funziona
- [ ] Fetch API funziona
- [ ] Loading states funzionano
- [ ] Success messages funzionano
- [ ] Error messages funzionano
- [ ] Video preview funziona
- [ ] Results display funziona
- [ ] Responsive design funziona

### Integration
- [ ] CORS configurato correttamente
- [ ] Frontend → Backend communication
- [ ] File upload end-to-end
- [ ] Baseline creation end-to-end
- [ ] Anomaly detection end-to-end
- [ ] Error propagation frontend ← backend

### UX
- [ ] Loading feedback chiaro
- [ ] Error messages informativi
- [ ] Success confirmation
- [ ] Disabled states logici
- [ ] Hover effects funzionano
- [ ] Animations smooth
- [ ] Colors accessibili
- [ ] Font leggibili

## Debugging Tools

### Backend Debug Mode

In `app.py`, assicurati che debug sia True:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

Questo abilita:
- Auto-reload su modifiche
- Traceback dettagliati
- Debug toolbar (se installata)

### Frontend Dev Tools

In Vite, usa:
```bash
npm run dev -- --debug
```

### Logging Dettagliato

Aggiungi in `app.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)
```

## Performance Monitoring

### Tempo per Operazione

Annota tempi medi:
- [ ] Video upload: < 5s per 100MB
- [ ] Keypoint extraction: ~20-30 FPS
- [ ] Angle calculation: < 1s per 1000 frames
- [ ] LSTM inference: < 5s per video
- [ ] Baseline training: 2-5 minuti per 5 video

### Resource Usage

Monitor durante uso intensivo:
- [ ] CPU usage
- [ ] RAM usage (atteso: 2-4GB durante training)
- [ ] Disk I/O (per video grandi)

## Acceptance Criteria

Il sistema è considerato funzionante se:

✅ **Tutti i test funzionali passano**  
✅ **Nessun errore critico in console**  
✅ **Performance entro target**  
✅ **UI responsiva e intuitiva**  
✅ **Error handling graceful**  
✅ **Documentazione accurata**  

---

**Pronto per il deploy dopo aver passato tutti i test!** 🎯

