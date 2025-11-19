# Guida alla Navigazione Step

## 📋 Panoramica

La navigazione dell'applicazione è stata ridisegnata per centralizzare il pulsante "Indietro" nello **StepHolder** invece che nei singoli componenti step.

## 🎯 Modifiche Principali

### 1. **Header dello StepHolder**

**Prima:**
```
Analisi Biomeccanica          [Step 1 / 6]
```

**Dopo:**
```
Step                          [← Indietro]
Step 1 di 6
```

### 2. **Struttura Header**

- **Sinistra**: 
  - Titolo principale: "Step"
  - Sottotitolo: "Step x di y"

- **Destra**: 
  - Pulsante "← Indietro" (visibile solo da step 2 in poi)

### 3. **Footer dello StepHolder**

- Mantiene il pulsante "🔄 Ricomincia" (visibile solo da step 2 in poi)
- Questo permette di resettare completamente il flusso

## 🔢 Calcolo Step Totali

Il numero totale di step viene calcolato dinamicamente in base al flusso selezionato:

| Flusso | Metodo | Step Totali | Percorso |
|--------|--------|-------------|----------|
| Baseline | Upload | 4 | 1 → 2 → 3 (upload 5 video) → 4 (analisi) → 6 (risultati) |
| Baseline | Record | 6 | 1 → 2 → 3 (camera) → 4 (calibrazione) → 5 (analisi) → 6 (risultati) |
| Analyze | Upload | 4 | 1 → 2 → 3 (calibrazione) → 4 (analisi) → 6 (risultati) |
| Analyze | Record | 6 | 1 → 2 → 3 (camera) → 4 (calibrazione) → 5 (analisi) → 6 (risultati) |

**Nota**: Lo step 5 viene saltato quando si usa il metodo "Upload" perché la registrazione non è necessaria.

## 🎨 Stile del Pulsante "Indietro"

```css
.btn-back {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
}

/* Effetto hover: traslazione a sinistra */
.btn-back:hover {
  transform: translateX(-2px);
}
```

## 🧹 Pulizia Componenti Step

I pulsanti "Indietro" sono stati **rimossi** dai seguenti componenti:
- ✅ Step2VideoMethod.svelte
- ✅ Step3CameraSetup.svelte
- ✅ Step3Calibration.svelte
- ✅ Step3BaselineUpload.svelte
- ✅ Step4Calibration.svelte
- ✅ Step4Analysis.svelte
- ✅ Step5Analysis.svelte
- ✅ Step6Results.svelte

Ora ogni step ha solo il pulsante principale (Continua/Avvia/etc.).

## 📝 Implementazione

### StepHolder.svelte

```svelte
<div class="step-header">
  <div class="header-left">
    <h2>Step</h2>
    <p class="step-subtitle">Step {currentStep} di {totalSteps}</p>
  </div>
  <div class="header-right">
    {#if currentStep > 1}
      <button class="btn-back" on:click={goBack}>
        ← Indietro
      </button>
    {/if}
  </div>
</div>
```

### Funzione di Navigazione

```javascript
function goBack() {
  analysisStore.prevStep();
}

function calculateTotalSteps(flow, method) {
  if (!flow) return 6;
  
  if (method === 'record') {
    return 6;
  } else if (method === 'upload') {
    return 4; // Skip step 5
  }
  
  return 6;
}
```

## ✨ Vantaggi

1. **Consistenza**: Il pulsante "Indietro" è sempre nella stessa posizione
2. **Chiarezza**: "Step x di y" è più chiaro di "Step x / y"
3. **Pulizia**: I componenti step sono più semplici e focalizzati
4. **UX**: Navigazione più intuitiva e prevedibile

## 🎯 Comportamento

- **Step 1**: Nessun pulsante "Indietro" (primo step)
- **Step 2-6**: Pulsante "Indietro" visibile in alto a destra
- **Tutti gli step > 1**: Pulsante "🔄 Ricomincia" nel footer
- **Click "Indietro"**: Torna allo step precedente
- **Click "Ricomincia"**: Reset completo, torna allo Step 1

---

**Data aggiornamento**: 12 Novembre 2025

