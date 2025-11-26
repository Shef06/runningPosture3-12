# Running Analyzer - Approccio Geometrico/Statistico

## 🎯 Obiettivo
Sostituito l'approccio Deep Learning (TensorFlow/LSTM) con un approccio **geometrico/statistico** basato su SciPy/NumPy, più leggero, trasparente e deterministico.

## 📋 Modifiche Implementate

### Backend

#### 1. **requirements.txt**
- ❌ Rimosso: `tensorflow==2.15.0`
- ✅ Aggiunto: `scipy==1.11.4`

#### 2. **pose_engine.py** (NUOVO)
Modulo core che sostituisce la logica LSTM con calcoli geometrici:

**Metriche Calcolate:**
- **Valgismo Ginocchio SX/DX**: Angolo tra anca-ginocchio-caviglia
- **Caduta Pelvica**: Inclinazione del bacino nel piano frontale
- **Cadenza**: Passi al minuto rilevati con `scipy.signal.find_peaks`

**Funzioni Principali:**
- `_get_angle_2d(a, b, c)`: Calcolo angolo geometrico 2D
- `_get_pelvic_drop(l_hip, r_hip)`: Calcolo inclinazione pelvica
- `_get_knee_valgus(hip, knee, ankle)`: Calcolo valgismo
- `_detect_cadence(ankle_y, fps)`: Rilevamento cadenza con peak detection
- `process_video(video_path, fps)`: Processa un video e estrae serie temporali
- `create_baseline_stats(videos_data)`: Crea statistiche (μ, σ, min, max) da 5 video
- `calculate_z_scores(video_data, baseline)`: Calcola Z-Score e livelli di anomalia

**Z-Score Thresholds:**
- |Z| < 1.0: ✅ **Ottimale** (verde)
- 1.0 ≤ |Z| < 2.0: ⚠️ **Attenzione** (arancione)
- |Z| ≥ 2.0: 🚨 **Critico** (rosso)

#### 3. **app.py** (RISCRITTO)
Endpoint semplificati senza dipendenze da TensorFlow:

**POST /api/create_baseline:**
1. Riceve 5 video
2. Usa `PoseEngine` per processarli
3. Calcola statistiche aggregate (Media, StdDev, Min, Max)
4. Salva `baseline.json` (no modello .h5)

**POST /api/detect_anomaly:**
1. Riceve 1 video
2. Carica `baseline.json`
3. Processa video con `PoseEngine`
4. Calcola Z-Scores confrontando con baseline
5. Restituisce report con stato (Ottimale/Attenzione/Critico) e grafici

**Backup:**
- Vecchio app.py salvato come `app_old_lstm.py`

### Frontend

#### 4. **Step6Results.svelte** (RISCRITTO)
Nuova visualizzazione per approccio statistico:

**Baseline View:**
- Griglia con metriche di riferimento
- Mostra: Media ± StdDev e Range (Min-Max)

**Analysis View:**
- Confronto metrica per metrica con badge colorati
- Ogni card mostra:
  - Valore attuale
  - Baseline (μ ± σ)
  - Z-Score con colore
  - Livello (Ottimale/Attenzione/Critico)
- Grafici temporali per ogni metrica

#### 5. **analysisStore.js**
Già semplice, nessuna modifica necessaria (gestisce solo caricamento JSON).

## 🚀 Test del Nuovo Flusso

### 1. Installazione Dipendenze

```bash
cd backend
pip install -r requirements.txt
```

### 2. Avvio Backend

```bash
cd backend
python app.py
```

**Output Atteso:**
```
============================================================
  🏃 RUNNING ANALYZER - Backend Server
  Approccio: Geometrico/Statistico (No Deep Learning)
============================================================
Upload folder: backend/uploads
Model folder: backend/models
Baseline path: backend/models/baseline.json
============================================================
```

### 3. Test Endpoint Health

```bash
curl http://localhost:5000/api/health
```

**Risposta Attesa:**
```json
{
  "status": "success",
  "message": "Running Analyzer Server attivo"
}
```

### 4. Test Creazione Baseline

**Requisiti:**
- 5 video di corsa (vista posteriore)
- Velocità tapis roulant (km/h)
- FPS del video

**Tramite Frontend:**
1. Apri http://localhost:5000
2. Seleziona "Crea Baseline"
3. Carica 5 video
4. Inserisci velocità e FPS
5. Avvia analisi

**Log Backend (esempio):**
```
=== Creazione Baseline ===
Video salvati: ['video1.mp4', 'video2.mp4', ...]
📊 Parametri baseline: Velocità=10.0 km/h, FPS=30.0
Fase 1: Processing video con PoseEngine...
Processing video 1/5: video1.mp4
Video: 450 frame, 30.00 FPS
Processing completato: 450 frame, 445 con pose rilevata
Cadenza rilevata: SX=178.5 spm, DX=180.2 spm, Media=179.3 spm
...
Fase 2: Creazione statistiche baseline...
=== Statistiche Baseline ===
Valgismo Ginocchio SX: μ=8.45° ± 3.21°
Valgismo Ginocchio DX: μ=7.89° ± 2.98°
Caduta Pelvica: μ=2.34° ± 1.12°
Cadenza: μ=178.2 ± 4.5 spm
Salvataggio baseline in: backend/models/baseline.json
✅ Baseline creata con successo!
```

**File Generato:**
`backend/models/baseline.json` contenente:
```json
{
  "left_knee_valgus": {
    "mean": 8.45,
    "std": 3.21,
    "min": 2.1,
    "max": 15.8
  },
  "right_knee_valgus": { ... },
  "pelvic_drop": { ... },
  "cadence": { ... },
  "speed_kmh": 10.0,
  "fps": 30.0,
  "n_videos": 5,
  "total_frames": 2250,
  "created_at": "2025-11-24T..."
}
```

### 5. Test Analisi Video

**Requisiti:**
- 1 video di corsa (stessa velocità della baseline)
- Baseline già creata

**Tramite Frontend:**
1. Seleziona "Analizza Video"
2. Carica 1 video
3. Inserisci velocità e FPS (devono corrispondere alla baseline ±0.5 km/h)
4. Avvia analisi

**Log Backend (esempio):**
```
=== Analisi Video ===
Video: test_run.mp4
📊 Parametri analisi: Velocità=10.0 km/h, FPS=30.0
Caricamento baseline...
📊 Baseline: Velocità=10.0 km/h, FPS=30.0
Fase 1: Processing video con PoseEngine...
Video: 300 frame, 30.00 FPS
Processing completato: 300 frame, 297 con pose rilevata
...
Fase 2: Calcolo Z-Scores...
=== Calcolo Z-Scores ===
Z-Score Valgismo SX: 0.85 -> Ottimale
Z-Score Valgismo DX: 1.42 -> Attenzione
Z-Score Caduta Pelvica: 0.34 -> Ottimale
Z-Score Cadenza: -0.12 -> Ottimale
Stato Generale: Attenzione
✅ Analisi completata! Stato: Attenzione
```

**Risposta JSON:**
```json
{
  "status": "success",
  "anomaly_level": "Attenzione",
  "anomaly_color": "#f59e0b",
  "anomaly_score": 1.42,
  "metrics": {
    "left_knee_valgus": {
      "value": 11.18,
      "z_score": 0.85,
      "level": "Ottimale",
      "color": "#10b981",
      "baseline_mean": 8.45,
      "baseline_std": 3.21,
      "unit": "°"
    },
    "right_knee_valgus": {
      "value": 12.12,
      "z_score": 1.42,
      "level": "Attenzione",
      "color": "#f59e0b",
      ...
    },
    ...
  },
  "charts": {
    "timeline": [0, 1, 2, ..., 299],
    "left_knee_valgus": [8.2, 8.5, 9.1, ...],
    "right_knee_valgus": [...],
    "pelvic_drop": [...]
  }
}
```

## 📊 Visualizzazione Frontend

### Baseline Creata
- ✅ Icona successo
- Griglia 2 colonne con 4 metriche:
  - Valgismo Ginocchio SX
  - Valgismo Ginocchio DX
  - Caduta Pelvica
  - Cadenza
- Per ogni metrica:
  - Media
  - ± StdDev
  - Range (Min - Max)

### Analisi Completata
- Badge colorato con stato generale
- Z-Score massimo
- Interpretazione testuale
- Griglia 2 colonne con confronti:
  - Ogni metrica ha:
    - Badge livello (verde/arancione/rosso)
    - Valore attuale (blu)
    - Baseline (μ ± σ)
    - Z-Score (colorato)
- Grafici temporali per ogni metrica

## 🎨 Design
- Mantiene Glassmorphism scuro
- Badge colorati per feedback immediato
- Layout responsive (2 colonne, 1 su mobile)
- Z-Score evidenziato con colori

## ✅ Vantaggi Approccio Geometrico

1. **Leggero**: No TensorFlow (risparmio ~500MB)
2. **Trasparente**: Calcoli deterministici e comprensibili
3. **Veloce**: No training (5-10 sec vs 2-3 min)
4. **Interpretabile**: Z-Score e soglie chiare
5. **Deterministico**: Stesso input → stesso output

## 🔍 Verifica Successo

**Checklist:**
- [ ] Backend avvia senza errori TensorFlow
- [ ] Endpoint /api/health risponde
- [ ] Creazione baseline con 5 video funziona
- [ ] File baseline.json viene creato
- [ ] Analisi video singolo funziona
- [ ] Z-Scores calcolati correttamente
- [ ] Frontend mostra risultati con badge colorati
- [ ] Grafici temporali visualizzati

## 📁 File Modificati

```
backend/
├── requirements.txt          ✅ MODIFICATO (scipy, no tensorflow)
├── pose_engine.py           ✅ NUOVO (logica geometrica)
├── app.py                   ✅ RISCRITTO (endpoint statistici)
└── app_old_lstm.py          📦 BACKUP (vecchia versione)

frontend/src/lib/
├── stores/analysisStore.js   ✅ OK (già semplice)
└── components/steps/
    └── Step6Results.svelte   ✅ RISCRITTO (nuova visualizzazione)
```

## 🐛 Troubleshooting

### Errore: ModuleNotFoundError: No module named 'scipy'
```bash
pip install scipy==1.11.4
```

### Errore: baseline.json non trovato
Creare prima la baseline con 5 video.

### Warning: Pochi picchi rilevati per calcolo cadenza
Video troppo corto o movimento insufficiente. Usare video di almeno 10 secondi.

### Errore: Velocità non corrisponde alla baseline
Verificare che velocità e FPS dell'analisi corrispondano alla baseline (±0.5 km/h).

## 📚 Riferimenti

- **Vista**: Frontal Plane, Posterior View (vista posteriore)
- **Metriche**: Valgismo ginocchio, Caduta pelvica, Cadenza
- **Statistica**: Z-Score = (X - μ) / σ
- **Peak Detection**: `scipy.signal.find_peaks`
- **MediaPipe**: Pose estimation 3D world landmarks

---

**✅ Implementazione completata! Pronto per il test.**

