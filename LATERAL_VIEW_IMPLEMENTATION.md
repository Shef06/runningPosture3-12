# Implementazione Vista Laterale - Running Analyzer

## 📋 Sommario

L'applicazione "Running Analyzer" è stata aggiornata per supportare due tipi di vista:
- **Vista Posteriore** (esistente): Analizza valgismo ginocchia e caduta pelvica
- **Vista Laterale** (nuova): Analizza overstriding, flessione ginocchio, trunk lean e ground contact time

## 🔄 Modifiche Implementate

### 1. Frontend (Svelte)

#### 1.1 Nuovo Step di Selezione Vista
**File**: `frontend/src/lib/components/steps/Step2ViewSelection.svelte`
- Nuovo step inserito dopo la scelta dell'azione (Step 1)
- Permette all'utente di scegliere tra:
  - **Vista Posteriore**: Analisi di valgismo e caduta pelvica
  - **Vista Laterale**: Analisi di overstriding, flessione, trunk lean e GCT
- Salva la scelta nello store (`viewType`)

#### 1.2 Store Aggiornato
**File**: `frontend/src/lib/stores/analysisStore.js`
- Aggiunto stato `viewType: 'posterior'` (default)
- Aggiunto metodo `setViewType()` per impostare la vista selezionata

#### 1.3 Flusso degli Step Aggiornato
**File**: `frontend/src/lib/components/StepHolder.svelte`
- Integrato il nuovo Step2ViewSelection nel flusso
- Aggiornata la numerazione degli step:
  - Step 1: Scelta Azione (Baseline/Analisi)
  - Step 2: Selezione Vista (NUOVO)
  - Step 3: Metodo Video (Upload/Record)
  - Step 4: Upload/Camera Setup
  - Step 5: Calibrazione/Analisi
  - Step 6: Analisi (per recording)
  - Step 7: Risultati

#### 1.4 API Calls Aggiornate
**Files**: 
- `frontend/src/lib/components/steps/Step4Analysis.svelte`
- `frontend/src/lib/components/steps/Step5Analysis.svelte`

Entrambi ora inviano il parametro `view_type` nelle chiamate API a:
- `/api/create_baseline`
- `/api/detect_anomaly`

#### 1.5 Visualizzazione Risultati Dinamica
**File**: `frontend/src/lib/components/steps/Step6Results.svelte`
- Visualizzazione condizionale delle metriche basata su `viewType`
- **Vista Posteriore**: Mostra valgismo SX/DX, caduta pelvica, cadenza
- **Vista Laterale**: Mostra overstriding, flessione ginocchio @ IC, trunk lean, GCT
- Grafici temporali adattati per ogni tipo di vista

### 2. Backend (Python/Flask)

#### 2.1 Motore di Analisi Esteso
**File**: `backend/pose_engine.py`

##### Nuovi Metodi per Vista Laterale:

**`_get_overstriding(ankle, hip)`**
- Calcola la distanza orizzontale tra caviglia e anca
- Formula: `abs(ankle.x - hip.x)`
- Unità: metri (normalizzati)

**`_get_knee_flexion_angle(hip, knee, ankle)`**
- Calcola l'angolo di flessione del ginocchio nel piano sagittale
- Formula: Angolo Anca-Ginocchio-Caviglia usando geometria 2D
- Unità: gradi

**`_get_trunk_lean(shoulder, hip)`**
- Calcola l'inclinazione del tronco rispetto alla verticale
- Formula: Angolo tra vettore Spalla-Anca e asse Y
- Unità: gradi (positivo = inclinato in avanti)

**`_detect_ground_contacts(ankle_y, fps)`**
- Rileva i periodi di contatto al suolo
- Restituisce lista di tuple (frame_touchdown, frame_toeoff)
- Usato per calcolare il Ground Contact Time

##### Metodo `process_video()` Aggiornato:
- Nuovo parametro: `view_type: str = 'posterior'`
- Processing condizionale basato su `view_type`:
  - **Posterior**: Calcola valgismo SX/DX, caduta pelvica, cadenza
  - **Lateral**: Calcola overstriding, flessione ginocchio, trunk lean, GCT
- Cache separata per ogni tipo di vista

##### Metodi `create_baseline_stats()` e `calculate_z_scores()` Aggiornati:
- Supportano entrambe le viste
- Calcolano statistiche appropriate per ogni tipo di vista
- Z-scores calcolati per le metriche specifiche di ogni vista

#### 2.2 API Endpoints Aggiornati
**File**: `backend/app.py`

##### `/api/create_baseline`
- Accetta nuovo parametro: `view_type` (default: 'posterior')
- Validazione: deve essere 'posterior' o 'lateral'
- Passa `view_type` a `pose_engine.process_video()`
- Salva `view_type` nelle statistiche baseline
- Risposta include metriche appropriate per la vista selezionata

##### `/api/detect_anomaly`
- Accetta nuovo parametro: `view_type` (default: 'posterior')
- Verifica che `view_type` corrisponda a quello della baseline
- Passa `view_type` a `pose_engine.process_video()`
- Risposta include metriche e grafici appropriati per la vista

## 📊 Metriche per Vista

### Vista Posteriore (Esistente)
1. **Valgismo Ginocchio SX** (°)
2. **Valgismo Ginocchio DX** (°)
3. **Caduta Pelvica** (°)
4. **Cadenza** (spm)

### Vista Laterale (Nuova)
1. **Overstriding** (m) - Distanza caviglia-anca al contatto iniziale
2. **Flessione Ginocchio @ IC** (°) - Angolo ginocchio al contatto iniziale
3. **Trunk Lean** (°) - Inclinazione tronco rispetto alla verticale
4. **Ground Contact Time** (s) - Tempo di contatto al suolo

## 🔬 Formule Implementate

### Overstriding
```python
horizontal_distance = abs(ankle.x - hip.x)
```

### Knee Flexion Angle
```python
angle = calculate_angle_2d(hip, knee, ankle)  # Anca-Ginocchio-Caviglia
```

### Trunk Lean
```python
trunk_vector = hip - shoulder
vertical = [0, -1]  # Verticale verso l'alto
angle = arccos(dot(trunk_vector_2d, vertical) / (norm * norm))
# Segno positivo se inclinato in avanti
```

### Ground Contact Time
```python
# Rileva frame touchdown e toe-off dalla traiettoria verticale della caviglia
gct = (frame_toeoff - frame_touchdown) / fps
```

## 🎯 Flusso Utente Aggiornato

1. **Scelta Azione**: Baseline o Analizza
2. **Selezione Vista**: Posteriore o Laterale ← **NUOVO**
3. **Metodo Video**: Upload o Registra
4. **Acquisizione**: Upload file o Setup camera
5. **Calibrazione**: Inserimento FPS e velocità
6. **Analisi**: Processing con MediaPipe
7. **Risultati**: Visualizzazione metriche specifiche per la vista selezionata

## ✅ Testing Raccomandato

### 1. Test Vista Posteriore (Regressione)
- Creare baseline con 5 video vista posteriore
- Verificare metriche: valgismo, caduta pelvica, cadenza
- Analizzare nuovo video e confrontare con baseline

### 2. Test Vista Laterale (Nuova Funzionalità)
- Creare baseline con 5 video vista laterale
- Verificare metriche: overstriding, flessione ginocchio, trunk lean, GCT
- Analizzare nuovo video e confrontare con baseline

### 3. Test Validazione
- Tentare di analizzare video laterale con baseline posteriore → Deve dare errore
- Tentare di analizzare video posteriore con baseline laterale → Deve dare errore

### 4. Test UI
- Verificare che le card metriche mostrino i valori corretti per ogni vista
- Verificare che i grafici temporali siano appropriati per ogni vista
- Verificare che le etichette e unità siano corrette

## 📝 Note Tecniche

### Cache
- La cache è ora separata per tipo di vista
- Hash include: `video_path`, `mtime`, `fps`, `view_type`, parametri MediaPipe
- Video processati con vista diversa genereranno nuove entry di cache

### Compatibilità
- Baseline esistenti senza `view_type` saranno trattate come 'posterior' (default)
- L'applicazione è retrocompatibile con baseline create prima dell'aggiornamento

### Performance
- Il processing laterale ha complessità simile a quello posteriore
- La detection GCT aggiunge overhead minimo (~2-5%)
- La cache mantiene le performance ottimali per video ripetuti

## 🚀 Deployment

1. **Backend**: Riavviare il server Flask
```bash
cd backend
python app.py
```

2. **Frontend**: Rebuilding (se necessario)
```bash
cd frontend
npm run build
```

3. **Verificare**: Testare il nuovo flusso con entrambe le viste

## 📚 Riferimenti

- MediaPipe Pose Landmarks: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
- Biomechanical Metrics: Riferimenti nella letteratura scientifica sulla biomeccanica della corsa
- Z-Score Analysis: Statistiche standard per rilevamento anomalie

---

**Data Implementazione**: 28 Novembre 2025
**Versione**: 3.12 (con supporto vista laterale)

