# Flusso Step Corretto - Running Analyzer

## 📊 Flusso Upload Method

```
Step 1: Scelta Azione (Baseline/Analizza)
         ↓
Step 2: Selezione Vista (Posteriore/Laterale)
         ↓
Step 3: Metodo Video (Upload/Record)
         ↓
Step 4: Upload Video
         - Baseline: Step3BaselineUpload (5 video)
         - Analizza: Step3Calibration (1 video + params)
         ↓
Step 5: Riepilogo e Avvio
         - Step4Analysis (mostra riepilogo + bottone)
         - Click bottone → Chiamata API
         - API success → goToStep(6)
         ↓
Step 6: Risultati
         - Step6Results (metriche + grafici)
```

**Totale: 6 step per Upload**

## 📊 Flusso Record Method

```
Step 1: Scelta Azione (Baseline/Analizza)
         ↓
Step 2: Selezione Vista (Posteriore/Laterale)
         ↓
Step 3: Metodo Video (Upload/Record)
         ↓
Step 4: Camera Setup
         - Step3CameraSetup (selezione camera)
         ↓
Step 5: Calibrazione
         - Step4Calibration (FPS + velocità)
         ↓
Step 6: Registrazione e Analisi
         - Step5Analysis (record + API call)
         - API success → goToStep(7)
         ↓
Step 7: Risultati
         - Step6Results (metriche + grafici)
```

**Totale: 7 step per Record**

## 🔧 Logica StepHolder

### getStepComponent()

```javascript
Step 1 → Step1MainChoice
Step 2 → Step2ViewSelection
Step 3 → Step2VideoMethod

Step 4 → 
  if (record) → Step3CameraSetup
  else if (baseline) → Step3BaselineUpload
  else → Step3Calibration

Step 5 → 
  if (record) → Step4Calibration
  else → Step4Analysis (fa API call + goToStep(6))

Step 6 → 
  if (record) → Step5Analysis (record + API + goToStep(7))
  else → Step6Results

Step 7 → Step6Results
```

### Componenti Usati

| Step | Upload Baseline | Upload Analizza | Record Baseline/Analizza |
|------|----------------|-----------------|-------------------------|
| 1 | Step1MainChoice | Step1MainChoice | Step1MainChoice |
| 2 | Step2ViewSelection | Step2ViewSelection | Step2ViewSelection |
| 3 | Step2VideoMethod | Step2VideoMethod | Step2VideoMethod |
| 4 | Step3BaselineUpload | Step3Calibration | Step3CameraSetup |
| 5 | Step4Analysis | Step4Analysis | Step4Calibration |
| 6 | Step6Results | Step6Results | Step5Analysis |
| 7 | - | - | Step6Results |

## 🎯 Note Importanti

### Step4Analysis
- **NON usa più** `setAnalyzing(true)`
- **FA direttamente** la chiamata API quando si clicca il bottone
- **Avanza** a Step 6 (risultati) con `goToStep(6)` dopo success

### BaselineUploader.svelte
- **NON viene più usato** nel nuovo flusso
- Era stato sostituito da Step4Analysis che fa la stessa cosa inline
- Può essere rimosso o tenuto come backup

### Step5Analysis
- Usato **SOLO per Recording**
- Gestisce sia recording che chiamata API
- Avanza a Step 7 con `goToStep(7)` (se implementato)

### Loading States
- `analysisStore.setLoading(true)` durante API call
- Loading overlay mostrato in StepHolder
- `analysisStore.setLoading(false)` in finally

## 🐛 Bug Corretti

### Problema 1: Step 6 mostrava recording invece di risultati
**Causa**: `getStepComponent()` mostrava sempre Step5Analysis per step 6
**Fix**: Condizione `if (record) → Step5Analysis else → Step6Results`

### Problema 2: BaselineUploader non mostrato
**Causa**: Non era integrato nel flusso upload
**Fix**: Step4Analysis fa la chiamata API inline, non serve più BaselineUploader

### Problema 3: Step count errato
**Causa**: Conteggio includeva step non usati per upload
**Fix**: Upload = 6 step, Record = 7 step

## ✅ Testing Checklist

### Upload Baseline
- [ ] Step 1: Scelta "Baseline" ✓
- [ ] Step 2: Scelta vista (Posteriore/Laterale) ✓
- [ ] Step 3: Scelta "Upload" ✓
- [ ] Step 4: Upload 5 video ✓
- [ ] Step 5: Riepilogo + Click "Crea Baseline" ✓
- [ ] Loading durante API call ✓
- [ ] Step 6: Mostra risultati baseline ✓

### Upload Analizza
- [ ] Step 1: Scelta "Analizza" ✓
- [ ] Step 2: Scelta vista ✓
- [ ] Step 3: Scelta "Upload" ✓
- [ ] Step 4: Upload 1 video + params ✓
- [ ] Step 5: Riepilogo + Click "Avvia Analisi" ✓
- [ ] Loading durante API call ✓
- [ ] Step 6: Mostra risultati analisi ✓

### Record
- [ ] Step 1-3: Come upload ✓
- [ ] Step 4: Camera setup ✓
- [ ] Step 5: Calibrazione ✓
- [ ] Step 6: Record + analisi ✓
- [ ] Step 7: Risultati ✓

## 📝 Riepilogo Modifiche

### File Modificati

1. **StepHolder.svelte**
   - `getStepComponent()`: Logica condizionale per step 5 e 6
   - `calculateStepInfo()`: 6 step per upload, 7 per record
   - `goBack()`: Gestione corretta back navigation

2. **Step4Analysis.svelte**
   - Chiamata API inline invece di `setAnalyzing(true)`
   - `goToStep(6)` dopo success API
   - Gestione loading con `setLoading()`

3. **BaselineUploader.svelte**
   - Non più usato (può essere rimosso)
   - Funzionalità migrata in Step4Analysis

---

**Data Fix**: 28 Novembre 2025
**Versione**: 3.12.1 (correzione flusso)

