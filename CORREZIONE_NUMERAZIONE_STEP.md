# Correzione Numerazione Step - Dopo Inserimento Step Vista

## 📊 Problema

Dopo l'inserimento del nuovo **Step 2: Selezione Vista**, tutti gli step successivi dovevano essere incrementati di 1, ma alcuni riferimenti erano rimasti con la vecchia numerazione.

## ✅ Correzioni Applicate

### 1. **StepHolder.svelte**

#### getStepComponent()
```javascript
// PRIMA (sbagliato)
if (currentStep === 6) return Step6Results; // Upload
if (currentStep === 7) return Step6Results; // Record

// DOPO (corretto)
if (currentStep === 7) return Step6Results; // Upload results
if (currentStep === 8) return Step6Results; // Record results
```

#### goBack()
```javascript
// PRIMA (sbagliato)
if (videoMethod === 'upload' && currentStep === 6) {
  analysisStore.goToStep(5);
}

// DOPO (corretto)
if (videoMethod === 'upload' && currentStep === 7) {
  analysisStore.goToStep(6);
}
if (videoMethod === 'record' && currentStep === 8) {
  analysisStore.goToStep(7);
}
```

#### calculateStepInfo()
```javascript
// PRIMA (sbagliato)
if (method === 'upload') {
  return { current: step, total: 6 };
}
if (method === 'record') {
  return { current: step, total: 7 };
}

// DOPO (corretto)
if (method === 'upload') {
  return { current: step, total: 7 }; // 7 step totali
}
if (method === 'record') {
  return { current: step, total: 8 }; // 8 step totali
}
```

### 2. **Step4Analysis.svelte**

```javascript
// PRIMA (sbagliato)
analysisStore.goToStep(6); // Risultati

// DOPO (corretto)
analysisStore.goToStep(7); // Risultati per upload method
```

**Aggiunto anche**:
- `setAnalyzing(true)` per attivare BaselineUploader (ingranaggio + progress bar)
- `setAnalyzing(false)` dopo success/error per disattivare BaselineUploader

### 3. **Step5Analysis.svelte**

```javascript
// PRIMA (mancava)
// setResults() andava automaticamente a step 6

// DOPO (corretto)
analysisStore.setResults(data);
analysisStore.goToStep(8); // Risultati per record method
```

### 4. **analysisStore.js**

```javascript
// PRIMA (sbagliato)
setResults: (results) => update(state => ({ ...state, results, currentStep: 6 })),

// DOPO (corretto)
setResults: (results) => update(state => ({ ...state, results, currentStep: 7 })),
```

## 📋 Nuova Numerazione Step

### Flusso Upload

| Step | Componente | Descrizione |
|------|------------|-------------|
| 1 | Step1MainChoice | Scelta Azione (Baseline/Analizza) |
| 2 | Step2ViewSelection | **NUOVO** - Selezione Vista (Posteriore/Laterale) |
| 3 | Step2VideoMethod | Metodo Video (Upload/Record) |
| 4 | Step3BaselineUpload / Step3Calibration | Upload Video / Calibrazione |
| 5 | Step4Analysis | Riepilogo + Avvio Analisi |
| 6 | *(skip)* | - |
| 7 | Step6Results | **Risultati** ✅ |

**Totale: 7 step**

### Flusso Record

| Step | Componente | Descrizione |
|------|------------|-------------|
| 1 | Step1MainChoice | Scelta Azione |
| 2 | Step2ViewSelection | **NUOVO** - Selezione Vista |
| 3 | Step2VideoMethod | Metodo Video |
| 4 | Step3CameraSetup | Setup Camera |
| 5 | Step4Calibration | Calibrazione |
| 6 | Step5Analysis | Registrazione + Analisi |
| 7 | *(skip)* | - |
| 8 | Step6Results | **Risultati** ✅ |

**Totale: 8 step**

## 🎯 Mappatura Step → Componente

```javascript
Step 1 → Step1MainChoice
Step 2 → Step2ViewSelection (NUOVO)
Step 3 → Step2VideoMethod
Step 4 → Step3CameraSetup (record) / Step3BaselineUpload (baseline upload) / Step3Calibration (analyze upload)
Step 5 → Step4Calibration (record) / Step4Analysis (upload)
Step 6 → Step5Analysis (record) / Step6Results (upload - skip)
Step 7 → Step6Results (upload results)
Step 8 → Step6Results (record results)
```

## ✅ Checklist Verifica

- [x] StepHolder.getStepComponent() - step 7 e 8 per risultati
- [x] StepHolder.goBack() - step 7 e 8 per back navigation
- [x] StepHolder.calculateStepInfo() - totali 7 e 8
- [x] Step4Analysis.goToStep() - va a step 7
- [x] Step5Analysis.goToStep() - va a step 8
- [x] analysisStore.setResults() - va a step 7
- [x] Step4Analysis.setAnalyzing() - attiva BaselineUploader

## 🐛 Bug Risolti

1. ✅ Step 6 mostrava registrazione invece di risultati (upload)
2. ✅ Step 7 non esisteva per upload (doveva essere step 7)
3. ✅ Step 8 non esisteva per record (doveva essere step 8)
4. ✅ BaselineUploader non si attivava (mancava setAnalyzing)
5. ✅ Numerazione step totali errata

## 🧪 Test

### Test Upload Baseline
1. Step 1: Scelta "Baseline" ✓
2. Step 2: Scelta Vista ✓
3. Step 3: Scelta "Upload" ✓
4. Step 4: Upload 5 video ✓
5. Step 5: Click "Crea Baseline" ✓
   - Vedi BaselineUploader (ingranaggio + progress) ✓
6. Step 7: Risultati ✓

### Test Upload Analizza
1. Step 1-4: Come sopra ✓
5. Step 5: Click "Avvia Analisi" ✓
6. Step 7: Risultati ✓

### Test Record
1. Step 1-2: Come sopra ✓
3. Step 3: Scelta "Record" ✓
4. Step 4: Camera Setup ✓
5. Step 5: Calibrazione ✓
6. Step 6: Record + Analisi ✓
7. Step 8: Risultati ✓

---

**Data**: 28 Novembre 2025
**Versione**: 3.12.2 (correzione numerazione step)

