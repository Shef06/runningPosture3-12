# Guida Gestione Baseline

## 📋 Panoramica

Il sistema ora gestisce correttamente la creazione della baseline biomeccanica da 5 video ottimali. I video vengono processati sequenzialmente con MediaPipe per creare un modello di riferimento.

## 🎯 Flusso Baseline Completo

```
1. Utente seleziona "Genera Nuova Baseline"
2. Sceglie "Carica Video"
3. Carica 5 video della corsa ottimale
4. Inserisce parametri di calibrazione (fps, altezza, massa)
5. Clicca "🚀 Crea Baseline"
   ↓
6. BaselineAnalyzer si attiva
   ↓
7. Processa video 1/5 con scheletro
8. Processa video 2/5 con scheletro
9. Processa video 3/5 con scheletro
10. Processa video 4/5 con scheletro
11. Processa video 5/5 con scheletro
    ↓
12. Calcola statistiche aggregate
13. Salva baseline nello store
14. Transizione automatica a Step 6
    ↓
15. Visualizza valori baseline biomeccanici ✅
```

## 🆕 Componente: BaselineAnalyzer

### Caratteristiche

- ✅ **Processamento Sequenziale**: Analizza i 5 video uno alla volta
- ✅ **Progress Bar**: Mostra avanzamento (0% → 20% → 40% → 60% → 80% → 100%)
- ✅ **Scheletro Sovrapposto**: MediaPipe disegna lo scheletro su ogni video
- ✅ **Raccolta Dati**: Estrae landmark e calcola angoli per ogni frame
- ✅ **Statistiche Aggregate**: Combina dati di tutti e 5 i video

### Implementazione

```svelte
<BaselineAnalyzer 
  videoUrls={baselineVideoUrls}
  onAnalysisComplete={(results) => {
    console.log('Baseline creata', results);
  }}
/>
```

### Dati Raccolti

```javascript
allVideosData = [
  {
    videoIndex: 0,
    frames: [
      { frameNumber, timestamp, landmarks, angles },
      { frameNumber, timestamp, landmarks, angles },
      ...
    ],
    frameCount: 120
  },
  { videoIndex: 1, frames: [...], frameCount: 115 },
  { videoIndex: 2, frames: [...], frameCount: 118 },
  { videoIndex: 3, frames: [...], frameCount: 122 },
  { videoIndex: 4, frames: [...], frameCount: 117 }
]
```

## 📊 Calcolo Baseline

### Aggregazione Dati

```javascript
// Concatena tutti i frame di tutti i video
const allFrames = allVideosData.flatMap(video => video.frames);

// Estrai angoli da tutti i frame
const leftKneeAngles = allFrames.map(f => f.angles.leftKneeAngle);
const rightKneeAngles = allFrames.map(f => f.angles.rightKneeAngle);
const pelvicDrops = allFrames.map(f => f.angles.pelvicDrop);
const trunkAngles = allFrames.map(f => f.angles.trunkAngle);

// Calcola statistiche per ogni metrica
const baselineStats = {
  leftKnee: calculateStats(leftKneeAngles),
  rightKnee: calculateStats(rightKneeAngles),
  pelvicDrop: calculateStats(pelvicDrops),
  trunkInclination: calculateStats(trunkAngles)
};
```

### Output Baseline

```json
{
  "status": "success",
  "baselineCreated": true,
  "videosProcessed": 5,
  "totalFrames": 592,
  "averageFramesPerVideo": 118,
  "biomechanics": {
    "leftKneeAngle": {
      "mean": "159.23°",
      "min": "140.15°",
      "max": "173.45°",
      "std": "7.82°"
    },
    "rightKneeAngle": {
      "mean": "158.67°",
      "min": "141.20°",
      "max": "172.90°",
      "std": "7.95°"
    },
    "pelvicDrop": {
      "mean": "1.65%",
      "min": "0.32%",
      "max": "3.45%",
      "std": "0.58%"
    },
    "trunkInclination": {
      "mean": "84.78°",
      "min": "80.12°",
      "max": "88.34°",
      "std": "1.67°"
    }
  },
  "timestamp": "2025-11-12T15:30:45.123Z"
}
```

## 🎨 UI Durante Analisi

### Progress Bar Visivo

```
┌──────────────────────────────────┐
│  Video con scheletro             │
│  ┌────────────────────────────┐  │
│  │                            │  │
│  │   👤 (scheletro animato)   │  │
│  │                            │  │
│  └────────────────────────────┘  │
│                                  │
│  🟢 Analisi Baseline:            │
│     Video 3 di 5                 │
│                                  │
│  ▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░            │
│  60% completato                  │
└──────────────────────────────────┘
```

### Step 6 - Risultati Baseline

```
┌──────────────────────────────────────────┐
│  ✅ Baseline Creata con Successo!        │
│                                          │
│  Il modello di riferimento biomeccanico  │
│  è stato creato dai 5 video ottimali.    │
├──────────────────────────────────────────┤
│  📊 Valori Baseline Biomeccanici         │
│                                          │
│  Questi sono i valori di riferimento     │
│  della corsa ottimale, calcolati         │
│  dall'analisi dei 5 video.               │
│                                          │
│  🦵 Angolo Ginocchio Sinistro            │
│  ┌──────────┬──────────┐                │
│  │ Media    │ Min      │                │
│  │ 159.23°  │ 140.15°  │                │
│  │ Max      │ Dev.Std  │                │
│  │ 173.45°  │ 7.82°    │                │
│  └──────────┴──────────┘                │
│                                          │
│  [stesse card per altre metriche]        │
├──────────────────────────────────────────┤
│  Dettagli Tecnici:                       │
│  - Video Processati: 5/5                 │
│  - Frame Totali: 592                     │
│  - Media Frame/Video: 118                │
└──────────────────────────────────────────┘
```

## 🔄 Differenze Baseline vs Analisi

| Aspetto | Baseline | Analisi |
|---------|----------|---------|
| **Video** | 5 video | 1 video |
| **Componente** | BaselineAnalyzer | VideoAnalyzer |
| **Processamento** | Sequenziale | Diretto |
| **Progress** | Mostra video X/5 | Nessun progress |
| **Output** | Valori di riferimento | Anomaly score + deviazioni |
| **Colore UI** | Verde (success) | Blu (info) |

## 💻 Codice Chiave

### VideoHolder.svelte

```svelte
{#if mainFlow === 'baseline' && videoMethod === 'upload' && baselineVideos.length === 5 && isAnalyzing}
  <!-- Analisi baseline con 5 video -->
  <BaselineAnalyzer 
    videoUrls={baselineVideoUrls}
    onAnalysisComplete={(results) => {
      console.log('Analisi baseline completata', results);
      analysisStore.setMessage('✅ Baseline creata con successo!');
    }}
  />

{:else if mainFlow === 'baseline' && videoMethod === 'upload' && baselineVideos.length > 0}
  <!-- Gallery 5 video baseline (preview) -->
  <div class="baseline-gallery">
    <!-- Thumbnail grid per vedere i 5 video -->
  </div>
{/if}
```

### BaselineAnalyzer.svelte

```javascript
async function processNextVideo() {
  if (currentVideoIndex >= videoUrls.length) {
    await finishBaselineAnalysis();
    return;
  }
  
  currentVideoFrames = [];
  frameCount = 0;
  
  videoElement.src = videoUrls[currentVideoIndex];
  videoElement.load();
}

function handleVideoEnded() {
  allVideosData.push({
    videoIndex: currentVideoIndex,
    frames: currentVideoFrames,
    frameCount: currentVideoFrames.length
  });
  
  currentVideoIndex++;
  
  if (currentVideoIndex < videoUrls.length) {
    processNextVideo();
  } else {
    finishBaselineAnalysis();
  }
}
```

## 🧪 Test Baseline

### Checklist Test

- [ ] Carica esattamente 5 video
- [ ] Clicca "Crea Baseline"
- [ ] Verifica che ogni video venga riprodotto con scheletro
- [ ] Verifica progress bar: 0% → 20% → 40% → 60% → 80% → 100%
- [ ] Console mostra "📹 Processamento video X/5..."
- [ ] Console mostra "✅ Video X/5 completato" per ognuno
- [ ] Console mostra "✅ Tutti i 5 video processati"
- [ ] Transizione automatica a Step 6
- [ ] Step 6 mostra "✅ Baseline Creata con Successo!"
- [ ] Visualizza 4 metriche biomeccaniche con statistiche
- [ ] Dettagli tecnici mostrano "Video Processati: 5/5"

### Console Output Atteso

```
🎬 Avvio analisi baseline con 5 video
📹 Processamento video 1/5...
📹 Video 1/5 caricato: 1920x1080
✅ Video 1/5 completato
📹 Processamento video 2/5...
📹 Video 2/5 caricato: 1920x1080
✅ Video 2/5 completato
📹 Processamento video 3/5...
📹 Video 3/5 caricato: 1920x1080
✅ Video 3/5 completato
📹 Processamento video 4/5...
📹 Video 4/5 caricato: 1920x1080
✅ Video 4/5 completato
📹 Processamento video 5/5...
📹 Video 5/5 caricato: 1920x1080
✅ Video 5/5 completato
✅ Tutti i 5 video processati
📊 Risultati baseline: { status: "success", ... }
```

## 🎯 Vantaggi Implementazione

1. **Robustezza**: Analisi di 5 video fornisce valori baseline più affidabili
2. **Feedback Visivo**: Progress bar mostra avanzamento chiaro
3. **Validazione**: Ogni video viene analizzato con MediaPipe
4. **Statistiche**: Media/Min/Max/Std da dataset ampio
5. **Scalabilità**: Facile estendere a più/meno video

## 📝 Note Importanti

### Requisiti

- ✅ Esattamente **5 video** richiesti
- ✅ Formato supportato: `.mp4`, `.webm`, `.ogv`
- ✅ Risoluzione consigliata: 720p o superiore
- ✅ Vista: Laterale o frontale
- ✅ Illuminazione: Buona per rilevamento ottimale

### Limitazioni

- **Processamento Sequenziale**: I video sono processati uno alla volta (non parallelo)
- **Memoria**: 5 video + tutti i frame possono occupare molta RAM
- **Tempo**: ~5-10 minuti totali per 5 video (dipende dalla durata)

### Ottimizzazioni Future

- [ ] Processamento parallelo dei video
- [ ] Salvataggio baseline su file/database
- [ ] Caricamento baseline salvate
- [ ] Confronto tra multiple baseline
- [ ] Export baseline come JSON

---

**Data implementazione**: 12 Novembre 2025  
**Componenti**: BaselineAnalyzer.svelte, VideoHolder.svelte, Step6Results.svelte











