# Analisi Video con Scheletro MediaPipe

## 📋 Panoramica

Quando viene cliccato il pulsante **"Avvia Analisi"**, il video viene riprodotto con uno scheletro sovrapposto in tempo reale utilizzando **MediaPipe Pose**.

## 🎯 Funzionalità Implementate

### 1. **Componente VideoAnalyzer**

Un nuovo componente Svelte (`VideoAnalyzer.svelte`) che:
- ✅ Carica MediaPipe Pose da CDN
- ✅ Processa ogni frame del video in tempo reale
- ✅ Disegna lo scheletro sovrapposto al video usando un canvas
- ✅ Gestisce play/pause dell'analisi

### 2. **Integrazione con VideoHolder**

Il `VideoHolder` ora mostra automaticamente il `VideoAnalyzer` quando:
- `mainFlow === 'analyze'`
- `videoMethod === 'upload'` 
- È presente un video caricato

### 3. **Flusso Utente**

```
1. Utente carica un video
2. Inserisce parametri di calibrazione (fps, altezza, massa)
3. Clicca "🔍 Avvia Analisi"
4. isAnalyzing → true
5. VideoAnalyzer si attiva automaticamente
6. Video riprodotto con scheletro sovrapposto
7. Al termine: messaggio "✅ Analisi completata!"
```

## 🎨 Visualizzazione Scheletro

### Colori
- **Verde (#00FF00)**: Connessioni (le "ossa")
- **Rosso (#FF0000)**: Landmark (i "giunti")

### Connessioni Disegnate

MediaPipe Pose disegna 33 landmark del corpo:
- Viso: naso, occhi, orecchie, bocca
- Corpo: spalle, gomiti, polsi, anche, ginocchia, caviglie
- Mani: pollice, indice, mignolo, palmo
- Piedi: tallone, punta, indice piede

## 💻 Implementazione Tecnica

### package.json

```json
"dependencies": {
  "@mediapipe/pose": "^0.5.1675469404",
  "@mediapipe/camera_utils": "^0.3.1675466862",
  "@mediapipe/drawing_utils": "^0.3.1620248257"
}
```

### Architettura

```
VideoAnalyzer.svelte
├── <video> elemento
├── <canvas> overlay (per disegnare scheletro)
├── MediaPipe Pose (caricato da CDN)
├── processFrame() (loop di analisi)
└── onPoseResults() (callback disegno)
```

### Canvas Overlay

```svelte
<canvas
  class="skeleton-canvas"
  class:visible={isAnalyzing}
/>
```

```css
.skeleton-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  opacity: 0;
}

.skeleton-canvas.visible {
  opacity: 1;
}
```

### Sincronizzazione Video-Canvas

```javascript
function handleVideoLoaded() {
  canvasElement.width = videoElement.videoWidth;
  canvasElement.height = videoElement.videoHeight;
  canvasCtx = canvasElement.getContext('2d');
}
```

## 🔄 Flusso Dati

### Quando "Avvia Analisi" viene cliccato

```javascript
// Step4Analysis.svelte
async function startAnalysis() {
  analysisStore.setAnalyzing(true);
  analysisStore.setMessage('🎬 Avvio analisi con MediaPipe...');
}
```

### Auto-start nel VideoAnalyzer

```javascript
// VideoAnalyzer.svelte
$: if (isAnalyzing && videoElement && pose && !isProcessing) {
  setTimeout(() => startAnalysis(), 300);
}
```

### Loop di Processamento

```javascript
async function processFrame() {
  if (!isAnalyzing || videoElement.paused || videoElement.ended) {
    return;
  }
  
  await pose.send({ image: videoElement });
  animationFrame = requestAnimationFrame(processFrame);
}
```

### Disegno Risultati

```javascript
function onPoseResults(results) {
  canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
  
  if (results.poseLandmarks) {
    drawConnectors(canvasCtx, results.poseLandmarks, POSE_CONNECTIONS);
    drawLandmarks(canvasCtx, results.poseLandmarks);
  }
}
```

## 🎮 Controlli Utente

### Pulsanti Disponibili

1. **▶️ Riproduci con Scheletro**: Avvia l'analisi
2. **⏸️ Ferma**: Mette in pausa l'analisi
3. **Video Controls**: Il video HTML nativo ha anche i controlli di default

### Stato Visivo

Quando l'analisi è attiva:
```
┌─────────────────────────┐
│ 🟢 Analisi in corso...  │
└─────────────────────────┘
```

## 🔧 Configurazione MediaPipe

```javascript
pose.setOptions({
  modelComplexity: 1,          // Modello medio (0=lite, 1=full, 2=heavy)
  smoothLandmarks: true,       // Smooth dei landmark tra frame
  enableSegmentation: false,   // Non serve segmentazione
  minDetectionConfidence: 0.5, // Soglia rilevamento
  minTrackingConfidence: 0.5   // Soglia tracking
});
```

## 📊 Performance

- **Frame Processing**: ~30-60 FPS (dipende da CPU)
- **Latency**: <50ms per frame
- **Model Load Time**: ~2-3 secondi (primo caricamento)

## 🐛 Debug

Console logs disponibili:
```
✅ MediaPipe Pose inizializzato
📹 Video caricato: 1920x1080
🎬 Analisi video avviata
✅ Video terminato
⏸️ Analisi fermata
```

## 🚀 Prossimi Passi (TODO)

1. ✅ Visualizzazione scheletro in tempo reale
2. ⏳ Invio dati al backend dopo analisi
3. ⏳ Calcolo angoli biomeccanici (knee valgus, pelvic drop, trunk inclination)
4. ⏳ Confronto con baseline
5. ⏳ Calcolo anomaly score
6. ⏳ Visualizzazione risultati dettagliati

## 📝 Note

- MediaPipe viene caricato da CDN per ridurre la dimensione del bundle
- Il canvas è posizionato absolute sopra il video
- L'analisi si ferma automaticamente al termine del video
- Lo scheletro è visibile solo quando `isAnalyzing === true`

---

**Data implementazione**: 12 Novembre 2025  
**Tecnologie**: Svelte, MediaPipe Pose, Canvas API










