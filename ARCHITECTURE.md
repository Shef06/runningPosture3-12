# 🏗 Architettura Tecnica - Jump Analyzer Pro

## Overview

Sistema full-stack per l'analisi biomeccanica della corsa basato su Computer Vision e Deep Learning.

## Stack Tecnologico Completo

### Backend (Python)
- **Flask 3.0.0** - Web framework per API REST
- **Flask-CORS 4.0.0** - Gestione Cross-Origin Resource Sharing
- **TensorFlow 2.15.0** - Framework Deep Learning
- **OpenCV 4.8.1** - Elaborazione video e immagini
- **MediaPipe 0.10.8** - Estrazione pose 3D
- **NumPy 1.24.3** - Calcoli numerici e array

### Frontend (JavaScript/TypeScript)
- **Svelte 4.2.7** - Framework UI reattivo
- **SvelteKit 2.0.0** - Meta-framework per routing e SSR
- **Vite 5.0.3** - Build tool e dev server

## Architettura di Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    BROWSER (Client)                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           Frontend Svelte (Port 3000)                  │  │
│  │  ┌──────────────┐  ┌──────────────────────────────┐  │  │
│  │  │ +page.svelte │  │  Components:                  │  │  │
│  │  │              │  │  - BaselineUploader.svelte    │  │  │
│  │  │              │  │  - AnalysisUploader.svelte    │  │  │
│  │  └──────────────┘  └──────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend Flask (Port 5000)                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    app.py (Flask)                      │  │
│  │  ┌─────────────────────┐  ┌──────────────────────┐   │  │
│  │  │ POST /api/create    │  │ POST /api/detect     │   │  │
│  │  │      _baseline      │  │      _anomaly        │   │  │
│  │  └─────────────────────┘  └──────────────────────┘   │  │
│  └───────────────────────────────────────────────────────┘  │
│                              │                               │
│  ┌───────────────────────────┼──────────────────────────┐  │
│  │         Processing Pipeline                           │  │
│  │  ┌───────────────┐  ┌─────────────────┐  ┌────────┐ │  │
│  │  │  MediaPipe    │→ │ Feature Eng.    │→ │ LSTM   │ │  │
│  │  │  (Keypoints)  │  │ (Angles Calc)   │  │ AutoEnc│ │  │
│  │  └───────────────┘  └─────────────────┘  └────────┘ │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Flusso di Dati

### 1. Creazione Baseline

```
Video Upload (5x)
    │
    ▼
┌─────────────────────────┐
│  keypoint_extractor.py  │
│  - MediaPipe Pose       │
│  - Extract 3D World     │
│    Landmarks (33x4)     │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ feature_engineering.py  │
│  - Calculate Angles:    │
│    • Knee Valgus (L/R)  │
│    • Pelvic Drop        │
│    • Trunk Lean         │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│  lstm_autoencoder.py    │
│  - Prepare Sequences    │
│  - Train LSTM AE        │
│  - Save Model (.h5)     │
└─────────────────────────┘
```

### 2. Analisi Anomalia

```
Video Upload (1x)
    │
    ▼
MediaPipe → Angles → LSTM → Reconstruction → MSE Score
                             Error
```

## Moduli Backend Dettagliati

### 1. config.py
**Responsabilità**: Configurazione centralizzata

```python
- UPLOAD_FOLDER: Dove salvare video temporanei
- MODEL_FOLDER: Dove salvare modelli addestrati
- MEDIAPIPE_MODEL_COMPLEXITY: 0-2 (velocità vs accuratezza)
- LSTM_UNITS: 64 (dimensione hidden state)
- LATENT_DIM: 32 (bottleneck)
- EPOCHS: 50
- BATCH_SIZE: 32
```

### 2. keypoint_extractor.py
**Classe**: `KeypointExtractor`

**Metodi principali**:
- `extract_from_video(video_path)`: Frame-by-frame extraction
- `extract_from_multiple_videos(video_paths)`: Batch processing

**Output**: `np.ndarray` shape `(n_frames, 33, 4)`
- 33 landmark MediaPipe
- 4 coordinate: [x, y, z, visibility]
- Coordinate in metri (world coordinates)

### 3. feature_engineering.py
**Classe**: `BiomechanicalFeatures`

**Metodi principali**:
- `calculate_angle_3d(a, b, c)`: Angolo tra 3 punti usando prodotto scalare
- `calculate_knee_valgus_angle()`: Hip-Knee-Ankle angle
- `calculate_pelvic_drop()`: Angolo linea bi-iliaca
- `calculate_trunk_lateral_lean()`: Shoulder-Hip center angle
- `extract_all_features()`: Processa intera sequenza

**Output**: `np.ndarray` shape `(n_frames, 4)`

### 4. lstm_autoencoder.py
**Classe**: `LSTMAutoencoder`

**Architettura**:
```
Input: (batch, 30, 4)
    ↓
Encoder:
  LSTM(64) → LSTM(32)
    ↓
Latent Space: (batch, 32)
    ↓
RepeatVector(30)
    ↓
Decoder:
  LSTM(32) → LSTM(64) → TimeDistributed(Dense(4))
    ↓
Output: (batch, 30, 4)
```

**Metodi principali**:
- `build_model()`: Costruisce architettura Keras
- `prepare_sequences()`: Sliding window di 30 frame
- `train()`: Addestramento con early stopping
- `calculate_reconstruction_error()`: MSE per anomaly detection
- `save_model()` / `load_model()`: Persistenza

### 5. app.py
**Framework**: Flask

**Endpoints**:

#### POST `/api/create_baseline`
- Input: FormData con 5 video (key: `videos`)
- Processo:
  1. Salva video temporanei
  2. Estrazione keypoint (tutti i 5 video)
  3. Calcolo angoli (concatenati)
  4. Addestramento LSTM AE
  5. Salvataggio modello
  6. Cleanup video temporanei
- Output: JSON con stats addestramento

#### POST `/api/detect_anomaly`
- Input: FormData con 1 video (key: `video`)
- Processo:
  1. Salva video temporaneo
  2. Carica modello baseline
  3. Estrazione keypoint
  4. Calcolo angoli
  5. Inferenza LSTM AE
  6. Calcolo MSE
  7. Classificazione livello
  8. Cleanup
- Output: JSON con score e interpretazione

## Moduli Frontend Dettagliati

### 1. +page.svelte
**Ruolo**: Pagina principale, composizione componenti

**Layout**:
```html
<header>Jump Analyzer Pro</header>
<main>
  <BaselineUploader />
  <AnalysisUploader />
</main>
<footer>Credits</footer>
```

### 2. BaselineUploader.svelte
**Stato Reattivo**:
```javascript
let files = [];           // Array di File objects
let loading = false;      // UI loading state
let message = null;       // Feedback message
let messageType = null;   // 'success' | 'error'
```

**Funzioni**:
- `handleFileSelect()`: Valida 5 video
- `createBaseline()`: POST a `/api/create_baseline`

**UI Features**:
- Input multiplo file
- Lista file con dimensioni
- Progress indicator
- Alert feedback

### 3. AnalysisUploader.svelte
**Stato Reattivo**:
```javascript
let file = null;          // File object
let loading = false;
let result = null;        // Response da API
let videoUrl = null;      // Blob URL per preview
```

**Funzioni**:
- `handleFileSelect()`: Crea preview video
- `analyzeVideo()`: POST a `/api/detect_anomaly`
- `resetAnalysis()`: Pulisce stato

**UI Features**:
- Video preview player
- Risultati visualizzati con:
  - Score numerico grande
  - Badge colorato (green→red)
  - Interpretazione testuale
  - Dettagli tecnici collapsible

### 4. styles.css
**Design System**:
```css
--primary-bg: #2c3e50      (dark blue)
--secondary-bg: #34495e    (lighter dark)
--accent-color: #3498db    (blue)
--success-color: #2ecc71   (green)
--warning-color: #f39c12   (orange)
--error-color: #e74c3c     (red)
```

**Layout**:
- Grid responsivo 2:1 (video:results)
- Breakpoint @968px → stacking verticale
- Box-shadow e border-radius consistenti
- Animazioni smooth (slideIn, spin)

## Modello LSTM Autoencoder

### Perché LSTM?
- Cattura dipendenze temporali nei movimenti
- Pattern ciclici della corsa (step cycle)
- Memoria a breve e lungo termine

### Perché Autoencoder?
- Apprendimento non supervisionato
- Impara la "normalità" (baseline)
- Anomalie = alta ricostruzione error
- Non richiede labeling di anomalie

### Training Strategy
1. **Solo dati normali**: Impara a ricostruire pattern ottimali
2. **MSE Loss**: Penalizza ricostruzioni imprecise
3. **Early Stopping**: Monitora val_loss, patience=10
4. **Sequence Length=30**: ~1 secondo a 30fps, cattura 1 step

### Anomaly Detection Logic
```python
anomaly_score = MSE(input_sequence, reconstructed_sequence)

if score < 0.01:   return "Ottimale"
if score < 0.05:   return "Buono"
if score < 0.1:    return "Moderato"
if score < 0.2:    return "Attenzione"
else:              return "Critico"
```

## Feature Engineering Rationale

### Perché Angoli invece di Coordinate Raw?

1. **Invarianza alla Scala**: Gli angoli sono indipendenti dalla distanza dalla camera
2. **Invarianza alla Posizione**: Non importa dove si trova l'atleta nel frame
3. **Significato Biomeccanico**: Gli angoli hanno interpretazione clinica diretta
4. **Riduzione Dimensionalità**: 33x3=99 coord → 4 angoli (25x meno dati)

### Angoli Selezionati

1. **Knee Valgus (Valgismo)**: 
   - Indicatore di collasso mediale del ginocchio
   - Fattore di rischio per infortuni ACL
   - Target principale per correzione tecnica

2. **Pelvic Drop (Caduta Pelvica)**:
   - Stabilità del core
   - Forza glutei mediali
   - Efficienza energetica

3. **Trunk Lateral Lean (Inclinazione Tronco)**:
   - Compensazione posturale
   - Asimmetrie lato destro/sinistro
   - Equilibrio dinamico

## Performance e Ottimizzazioni

### Backend
- **MediaPipe su CPU**: ~30 FPS (abbastanza per offline analysis)
- **Batch Processing**: Processa tutti i 5 video in sequenza
- **Memoria**: ~2-4GB durante training (TensorFlow)

### Frontend
- **Lazy Loading**: Componenti caricati on-demand
- **Blob URLs**: Video preview senza re-upload
- **Fetch API**: Nativo, no librerie esterne
- **CSS Animations**: Hardware-accelerated

### Possibili Miglioramenti Futuri
1. **GPU Acceleration**: TensorFlow GPU per training più veloce
2. **WebWorkers**: Processing video in background
3. **WebRTC**: Analisi in tempo reale da webcam
4. **Database**: SQLite per storico analisi
5. **Grafici**: Chart.js per trend temporali
6. **Multi-utente**: Autenticazione e profili separati

## Sicurezza

### Current
- File validation (estensioni permesse)
- Secure filename (werkzeug.secure_filename)
- Temporary file cleanup
- CORS configurato per sviluppo

### Production TODO
- [ ] HTTPS/TLS
- [ ] Rate limiting
- [ ] File size limits (già configurato: 500MB)
- [ ] Autenticazione utenti
- [ ] Sanitizzazione input
- [ ] Logging e monitoring

## Testing Strategy

### Unit Tests (TODO)
```python
# backend/tests/test_features.py
def test_angle_calculation()
def test_keypoint_extraction()
def test_autoencoder_training()
```

### Integration Tests (TODO)
```python
# backend/tests/test_api.py
def test_baseline_creation_endpoint()
def test_anomaly_detection_endpoint()
```

### E2E Tests (TODO)
```javascript
// frontend/tests/e2e.spec.js
test('complete baseline creation flow')
test('video analysis flow')
```

## Deployment

### Development
- Backend: `python app.py` (Flask dev server)
- Frontend: `npm run dev` (Vite dev server)

### Production (TODO)
- Backend: Gunicorn + Nginx
- Frontend: Static build su CDN
- Database: PostgreSQL per persistenza
- Containerization: Docker + Docker Compose

## Riferimenti

- [MediaPipe Pose](https://google.github.io/mediapipe/solutions/pose.html)
- [TensorFlow LSTM](https://www.tensorflow.org/api_docs/python/tf/keras/layers/LSTM)
- [Svelte Documentation](https://svelte.dev/docs)
- [Anomaly Detection with Autoencoders](https://keras.io/examples/timeseries/timeseries_anomaly_detection/)

---

**Versione**: 1.0.0  
**Last Updated**: Novembre 2025

