# Guida Risultati Analisi

## 📋 Panoramica

Alla fine dell'analisi video con MediaPipe, il sistema calcola automaticamente metriche biomeccaniche e mostra i risultati nello **Step 6 - Risultati**.

## 🎯 Flusso Completo

```
1. Utente carica video
2. Clicca "Avvia Analisi"
3. Video riprodotto con scheletro
4. MediaPipe raccoglie dati frame-by-frame
5. Al termine video → calcolo risultati
6. Transizione automatica a Step 6
7. Visualizzazione risultati dettagliati
```

## 📊 Dati Raccolti

### Durante l'Analisi

Per ogni frame del video, MediaPipe raccoglie:
- **33 Landmark 3D** del corpo
- **Timestamp** del frame
- **Numero frame** progressivo

### Angoli Biomeccanici Calcolati

#### 1. **Angolo Ginocchio Sinistro/Destro**
```javascript
calculateAngle(hip, knee, ankle)
```
- **Unità**: gradi (°)
- **Valore ideale**: ~160° (estensione durante corsa)
- **Landmark usati**: Anca (23/24), Ginocchio (25/26), Caviglia (27/28)

#### 2. **Caduta Pelvica (Pelvic Drop)**
```javascript
Math.abs(leftHip.y - rightHip.y)
```
- **Unità**: percentuale (%)
- **Valore ideale**: <2% (minimo sbilanciamento)
- **Landmark usati**: Anca sinistra (23), Anca destra (24)

#### 3. **Inclinazione Tronco (Trunk Inclination)**
```javascript
Math.atan2(shoulderMidpoint - hipMidpoint)
```
- **Unità**: gradi (°)
- **Valore ideale**: ~85° (quasi verticale)
- **Landmark usati**: Spalle (11/12), Anche (23/24)

## 📈 Statistiche Calcolate

Per ogni metrica biomeccanica:
- **Media (mean)**: Valore medio su tutti i frame
- **Minimo (min)**: Valore minimo osservato
- **Massimo (max)**: Valore massimo osservato
- **Dev.Std (std)**: Deviazione standard (variabilità)

### Esempio Output

```json
{
  "status": "success",
  "framesAnalyzed": 120,
  "duration": 4.0,
  "fps": 30,
  "anomaly_score": 0.0234,
  "biomechanics": {
    "leftKneeAngle": {
      "mean": "158.45°",
      "min": "142.30°",
      "max": "172.15°",
      "std": "8.23°"
    },
    "rightKneeAngle": {
      "mean": "159.12°",
      "min": "143.20°",
      "max": "171.80°",
      "std": "7.89°"
    },
    "pelvicDrop": {
      "mean": "1.85%",
      "min": "0.45%",
      "max": "3.20%",
      "std": "0.67%"
    },
    "trunkInclination": {
      "mean": "84.23°",
      "min": "81.50°",
      "max": "87.10°",
      "std": "1.45°"
    }
  }
}
```

## 🎨 Visualizzazione Step 6

### 1. **Anomaly Score**
```
┌─────────────────────────┐
│  Anomaly Score: 0.0234  │
│  ✓ Buono!               │
└─────────────────────────┘
```

**Scala Interpretazione:**
- `< 0.01`: ✓ Eccellente
- `< 0.05`: ✓ Buono
- `< 0.10`: ⚠ Moderato
- `< 0.20`: ⚠ Attenzione
- `≥ 0.20`: 🚨 Critico

### 2. **Dati Biomeccanici**

Layout a griglia 2x2 per ogni metrica:

```
📊 Dati Biomeccanici
├─ 🦵 Angolo Ginocchio Sinistro
│  ├─ Media: 158.45°    Min: 142.30°
│  └─ Max: 172.15°      Dev.Std: 8.23°
│
├─ 🦵 Angolo Ginocchio Destro
│  ├─ Media: 159.12°    Min: 143.20°
│  └─ Max: 171.80°      Dev.Std: 7.89°
│
├─ ⚖️ Caduta Pelvica
│  ├─ Media: 1.85%      Min: 0.45%
│  └─ Max: 3.20%        Dev.Std: 0.67%
│
└─ 📐 Inclinazione Tronco
   ├─ Media: 84.23°     Min: 81.50°
   └─ Max: 87.10°       Dev.Std: 1.45°
```

### 3. **Dettagli Tecnici**

```
Dettagli Tecnici:
- Frame Analizzati: 120
- Durata Video: 4.00s
- FPS Analisi: 30.0 fps
```

## 🔬 Calcolo Anomaly Score

Formula utilizzata:

```javascript
const kneeDeviation = |leftKnee.mean - 160| + |rightKnee.mean - 160|
const pelvicDeviation = pelvicDrop.mean / 0.02
const trunkDeviation = |trunkInclination.mean - 85|

anomalyScore = (kneeDeviation * 0.4 + 
                pelvicDeviation * 0.3 + 
                trunkDeviation * 0.3) / 100
```

**Pesi:**
- Ginocchia: 40% (critiche per infortuni)
- Bacino: 30% (stabilità)
- Tronco: 30% (postura)

## 💻 Implementazione Tecnica

### VideoAnalyzer.svelte

```javascript
// Durante processamento
function onPoseResults(results) {
  const angles = calculateBiomechanicalAngles(results.poseLandmarks);
  
  collectedFrames.push({
    frameNumber: frameCount++,
    timestamp: videoElement.currentTime,
    landmarks: results.poseLandmarks,
    angles: angles
  });
}

// Al termine video
function handleVideoEnded() {
  const results = calculateFinalResults();
  analysisStore.setResults(results); // → Step 6
}
```

### Step6Results.svelte

```svelte
{#if results.biomechanics}
  <div class="biomechanics-section">
    <h4>📊 Dati Biomeccanici</h4>
    
    {#each Object.entries(results.biomechanics) as [key, metric]}
      <div class="bio-metric">
        <h5>{metric.name}</h5>
        <div class="metric-stats">
          <div>Media: {metric.mean}{metric.unit}</div>
          <div>Min: {metric.min}{metric.unit}</div>
          <div>Max: {metric.max}{metric.unit}</div>
          <div>Dev.Std: {metric.std}{metric.unit}</div>
        </div>
      </div>
    {/each}
  </div>
{/if}
```

## 🎨 Stili CSS

### Sezione Biomeccanica

```css
.biomechanics-section {
  background: rgba(52, 152, 219, 0.05);
  border: 1px solid rgba(52, 152, 219, 0.2);
  border-radius: 8px;
  padding: 1rem;
}

.bio-metric {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  padding: 0.75rem;
}

.metric-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}
```

## 🔄 Transizione Automatica

### Store Action

```javascript
// analysisStore.js
setResults: (results) => update(state => ({ 
  ...state, 
  results, 
  currentStep: 6  // ← Passa automaticamente a Step 6
}))
```

Quando `setResults()` viene chiamato, lo step cambia automaticamente da 4 → 6.

## 🧪 Test Esempio

```javascript
// Console log atteso:
✅ Video terminato
📊 Risultati analisi: {
  status: "success",
  framesAnalyzed: 120,
  anomaly_score: 0.0234,
  biomechanics: { ... }
}
```

## 📝 Note Importanti

### Valori Ideali

I valori ideali sono approssimativi e possono variare:
- **Ginocchio**: 160° (può variare 140-175°)
- **Pelvic Drop**: <2% (dipende dall'atleta)
- **Tronco**: 85° (leggermente inclinato avanti è normale)

### Limitazioni

- **Vista Camera**: I risultati sono ottimali con vista laterale
- **Qualità Video**: Meglio con buona illuminazione e HD
- **Complessità Movimento**: Corsa è più complessa di camminata

### Prossimi Sviluppi

- [ ] Confronto con baseline storica
- [ ] Grafici temporali degli angoli
- [ ] Export dati CSV/JSON
- [ ] Report PDF generato
- [ ] Confronto sinistra vs destra

---

**Data implementazione**: 12 Novembre 2025  
**Version**: 1.0











