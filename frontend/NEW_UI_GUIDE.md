# 🎨 Guida alla Nuova UI - Jump Analyzer Pro

## Overview

La nuova interfaccia utente è stata completamente ridisegnata con un flusso a step guidato (wizard) che accompagna l'utente attraverso il processo di analisi biomeccanica.

## Layout

```
┌──────────────────────────────────────────────────────┐
│              Jump Analyzer Pro Header                 │
├──────────────────────────┬───────────────────────────┤
│                          │                           │
│      VIDEO HOLDER        │      STEP HOLDER          │
│      (a sinistra)        │      (a destra)           │
│                          │                           │
│  - Preview Video         │  Step 1: Scelta Azione    │
│  - Player Video          │  Step 2: Metodo Video     │
│  - Webcam Live           │  Step 3: Calibrazione     │
│  - Recording             │  Step 4: Analisi          │
│                          │  Step 5: Recording        │
│                          │  Step 6: Risultati        │
│                          │                           │
└──────────────────────────┴───────────────────────────┘
```

## Flussi Disponibili

### Flusso 1: Genera Nuova Baseline

**Step 1:** Scelta Azione
- Utente seleziona "Genera Nuova Baseline"

**Step 2:** Metodo di Acquisizione
- **Opzione A:** Carica Video
- **Opzione B:** Registra Video

#### Se Opzione A (Carica Video):
**Step 3:** Upload + Calibrazione
- Upload file video
- Inserimento parametri: FPS, Altezza (cm), Massa (kg)

**Step 4:** Analisi
- Conferma parametri
- Avvia creazione baseline

**Step 6:** Risultati
- Mostra dettagli baseline creata

#### Se Opzione B (Registra Video):
**Step 3:** Calibrazione Telecamera
- Selezione webcam
- Preview nel VideoHolder

**Step 4:** Calibrazione Parametri
- Inserimento: FPS, Altezza, Massa

**Step 5:** Registrazione + Analisi
- Pulsante "Avvia Registrazione" (REC)
- Pulsante "Ferma Registrazione"
- Avvia creazione baseline

**Step 6:** Risultati
- Mostra dettagli baseline creata

### Flusso 2: Analizza Video

**Step 1:** Scelta Azione
- Utente seleziona "Analizza Video"

**Step 2:** Metodo di Acquisizione
- **Opzione A:** Carica Video
- **Opzione B:** Registra Video

#### Flussi identici a "Genera Baseline" ma:
- Step 4/5: "Avvia Analisi" invece di "Crea Baseline"
- Step 6: Mostra Anomaly Score e interpretazione

## Componenti Principali

### 1. VideoHolder (Sinistra)

**Responsabilità:**
- Mostra video caricato
- Mostra preview webcam
- Mostra registrazione in corso (REC indicator)
- Player per playback

**Stati:**
- Placeholder (iniziale)
- Video caricato (da file)
- Webcam live (preview)
- Video registrato (playback)

### 2. StepHolder (Destra)

**Responsabilità:**
- Gestisce flusso a step
- Mostra step corrente
- Indicatore "Step X / 6"
- Pulsante "Ricomincia"

**Sub-componenti:**
- Step1MainChoice
- Step2VideoMethod
- Step3CameraSetup
- Step3Calibration
- Step4Calibration
- Step4Analysis
- Step5Analysis
- Step6Results

## State Management

### Store Svelte: `analysisStore`

**Stati principali:**
```javascript
{
  mainFlow: 'baseline' | 'analyze',
  currentStep: 1-6,
  videoMethod: 'upload' | 'record',
  videoFile: File | null,
  videoUrl: string | null,
  recordedBlob: Blob | null,
  selectedCamera: string,
  availableCameras: [],
  fps: number,
  height: number (cm),
  mass: number (kg),
  results: Object,
  loading: boolean,
  error: string,
  message: string
}
```

**Azioni:**
- `setMainFlow(flow)`
- `setVideoMethod(method)`
- `setVideoFile(file)`
- `setRecordedBlob(blob)`
- `setCalibration(fps, height, mass)`
- `setResults(results)`
- `nextStep() / prevStep()`
- etc.

## Comunicazione Eventi

Tra StepHolder e VideoHolder tramite Custom Events:

```javascript
// Da Step3CameraSetup → VideoHolder
window.dispatchEvent(new CustomEvent('changecamera', { detail: deviceId }))

// Da Step5Analysis → VideoHolder
window.dispatchEvent(new CustomEvent('startrecording'))
window.dispatchEvent(new CustomEvent('stoprecording'))
```

## Parametri Aggiuntivi

La nuova UI raccoglie parametri extra:

1. **FPS**: Frame per secondo del video
2. **Altezza**: Altezza atleta in cm
3. **Massa**: Massa atleta in kg

Questi vengono inviati all'API backend con `FormData`.

## API Backend (da aggiornare)

Gli endpoint dovranno accettare i nuovi parametri:

```javascript
// POST /api/create_baseline
formData.append('videos', file) // 5x
formData.append('fps', fps)
formData.append('height', height)
formData.append('mass', mass)

// POST /api/detect_anomaly
formData.append('video', file)
formData.append('fps', fps)
formData.append('height', height)
formData.append('mass', mass)
```

## Funzionalità Webcam

### MediaRecorder API

```javascript
// Inizializza camera
const stream = await navigator.mediaDevices.getUserMedia({ video: true })

// Registra
const mediaRecorder = new MediaRecorder(stream)
mediaRecorder.start()

// Stop
mediaRecorder.stop()

// Ottieni Blob
mediaRecorder.onstop = () => {
  const blob = new Blob(chunks, { type: 'video/webm' })
}
```

### Gestione Telecamere Multiple

```javascript
const devices = await navigator.mediaDevices.enumerateDevices()
const cameras = devices.filter(d => d.kind === 'videoinput')

// Seleziona camera specifica
const stream = await navigator.mediaDevices.getUserMedia({
  video: { deviceId: { exact: deviceId } }
})
```

## Styling

Mantiene il design system esistente:

**Colori:**
- Primary: `#2c3e50`
- Secondary: `#34495e`
- Accent: `#3498db`
- Success: `#2ecc71`
- Warning: `#f39c12`
- Error: `#e74c3c`

**Layout:**
- Grid 2:1 (video : step)
- Responsive: stacking verticale < 1200px
- Border radius: 12px
- Box shadow consistente

## Responsive Design

**Desktop (> 1200px):**
- Grid 2:1
- Video holder: fisso altezza
- Step holder: scroll verticale

**Tablet/Mobile (< 1200px):**
- Grid 1 colonna
- Video holder: 500px fisso
- Step holder: max-height 700px

## Testing

### Test Flusso Completo

1. **Baseline con Upload:**
   - Seleziona "Genera Baseline"
   - Seleziona "Carica Video"
   - Upload file
   - Inserisci parametri
   - Avvia analisi
   - Verifica risultati

2. **Baseline con Registrazione:**
   - Seleziona "Genera Baseline"
   - Seleziona "Registra Video"
   - Seleziona camera
   - Inserisci parametri
   - Registra video
   - Avvia analisi
   - Verifica risultati

3. **Analisi con Upload:**
   - Seleziona "Analizza Video"
   - Seleziona "Carica Video"
   - Upload file
   - Inserisci parametri
   - Avvia analisi
   - Verifica anomaly score

4. **Analisi con Registrazione:**
   - Seleziona "Analizza Video"
   - Seleziona "Registra Video"
   - Seleziona camera
   - Inserisci parametri
   - Registra video
   - Avvia analisi
   - Verifica anomaly score

## Troubleshooting

### Webcam non funziona
- Verifica permessi browser
- Controlla che nessun'altra app usi la webcam
- Prova browser diverso (Chrome/Edge consigliati)

### Eventi non funzionano
- Verifica che gli event listeners siano registrati in onMount
- Controlla console per errori JavaScript

### Step non avanza
- Verifica che lo store sia aggiornato correttamente
- Controlla validazione (es. video file presente)

## File Modificati/Creati

**Nuovi File:**
1. `frontend/src/lib/stores/analysisStore.js` - State management
2. `frontend/src/lib/components/VideoHolder.svelte` - Video container
3. `frontend/src/lib/components/StepHolder.svelte` - Step wizard
4. `frontend/src/lib/components/steps/Step1MainChoice.svelte`
5. `frontend/src/lib/components/steps/Step2VideoMethod.svelte`
6. `frontend/src/lib/components/steps/Step3CameraSetup.svelte`
7. `frontend/src/lib/components/steps/Step3Calibration.svelte`
8. `frontend/src/lib/components/steps/Step4Calibration.svelte`
9. `frontend/src/lib/components/steps/Step4Analysis.svelte`
10. `frontend/src/lib/components/steps/Step5Analysis.svelte`
11. `frontend/src/lib/components/steps/Step6Results.svelte`

**File Modificati:**
1. `frontend/src/routes/+page.svelte` - Nuovo layout grid

**File Obsoleti:**
1. `frontend/src/lib/components/BaselineUploader.svelte` - Sostituito da step wizard
2. `frontend/src/lib/components/AnalysisUploader.svelte` - Sostituito da step wizard

## Prossimi Passi

1. ✅ UI implementata con step wizard
2. ✅ Supporto webcam e registrazione
3. ✅ Parametri extra (fps, height, mass)
4. 🔄 Aggiornare backend per accettare nuovi parametri
5. 🔄 Testing completo flussi
6. 🔄 Documentazione utente aggiornata

---

**Versione UI**: 2.0.0  
**Data**: Novembre 2025

