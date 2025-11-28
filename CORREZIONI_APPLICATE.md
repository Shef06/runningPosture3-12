# Correzioni Applicate al Flusso Step

## 🐛 Problemi Risolti

### Problema 1: Step 6 mostrava la registrazione invece dei risultati
**Sintomo**: Dopo aver caricato i video e avviato l'analisi, veniva mostrato lo step per registrare invece dei risultati.

**Causa**: La logica in `getStepComponent()` non distingueva tra metodo upload e record per lo step 6.

**Soluzione**: 
```javascript
if (currentStep === 6) {
  if (videoMethod === 'record') return Step5Analysis;
  else return Step6Results; // Per upload, vai direttamente ai risultati
}
```

### Problema 2: BaselineUploader non veniva mostrato
**Sintomo**: L'ingranaggio rotante del BaselineUploader non appariva durante il caricamento.

**Causa**: BaselineUploader.svelte non era integrato nel nuovo flusso step-based. La logica API era stata spostata in Step4Analysis.

**Soluzione**: Step4Analysis ora fa direttamente la chiamata API e mostra il loading inline. BaselineUploader non serve più nel nuovo flusso.

### Problema 3: Numerazione step confusa
**Sintomo**: Conteggio step non corretto per metodo upload.

**Soluzione**: 
- **Upload**: 6 step totali (salta lo step di registrazione)
- **Record**: 7 step totali (include tutti gli step)

## ✅ Modifiche Applicate

### File: StepHolder.svelte

#### 1. Logica getStepComponent() corretta
```javascript
if (currentStep === 6) {
  if (videoMethod === 'record') return Step5Analysis;
  else return Step6Results; // Upload va direttamente ai risultati
}
```

#### 2. Calcolo step totali corretto
```javascript
if (method === 'upload') {
  return { current: step, total: 6 }; // 6 step per upload
}
if (method === 'record') {
  return { current: step, total: 7 }; // 7 step per record
}
```

#### 3. Navigazione "Indietro" corretta
```javascript
function goBack() {
  if (videoMethod === 'upload' && currentStep === 6) {
    analysisStore.goToStep(5); // Dai risultati torna al riepilogo
    return;
  }
  if (videoMethod === 'record' && currentStep === 7) {
    analysisStore.goToStep(6); // Dai risultati torna alla registrazione
    return;
  }
  analysisStore.prevStep();
}
```

### File: Step4Analysis.svelte

#### 1. Chiamata API inline
```javascript
async function startAnalysis() {
  // ... validazioni ...
  
  analysisStore.setLoading(true); // Mostra loading
  
  try {
    const formData = new FormData();
    // ... preparazione dati ...
    
    const response = await fetch('http://localhost:5000/api/...', {
      method: 'POST',
      body: formData
    });
    
    if (data.status === 'success') {
      analysisStore.setResults(data);
      analysisStore.goToStep(6); // ← Avanza ai risultati!
    }
  } catch (error) {
    analysisStore.setError(error.message);
  } finally {
    analysisStore.setLoading(false);
  }
}
```

## 🎯 Flusso Corretto per Upload

```
1️⃣ Scelta Azione
   [Baseline] o [Analizza]
       ↓
2️⃣ Selezione Vista
   [Posteriore] o [Laterale] ✨ NUOVO
       ↓
3️⃣ Metodo Video
   [Upload] ← selezioni questo
       ↓
4️⃣ Upload Video
   • Baseline: carica 5 video
   • Analizza: carica 1 video + params
       ↓
5️⃣ Riepilogo
   • Mostra dati caricati
   • Bottone "Crea Baseline" o "Avvia Analisi"
   • Click → Chiamata API + Loading
       ↓
6️⃣ Risultati ✅
   • Metriche calcolate
   • Grafici temporali
   • Z-Scores (per analisi)
```

## 🎬 Flusso Corretto per Record

```
1️⃣ Scelta Azione
2️⃣ Selezione Vista
3️⃣ Metodo Video
   [Record] ← selezioni questo
       ↓
4️⃣ Camera Setup
   • Selezione camera
       ↓
5️⃣ Calibrazione
   • FPS + Velocità
       ↓
6️⃣ Registrazione
   • Record video
   • Chiamata API + Loading
       ↓
7️⃣ Risultati ✅
```

## 🧪 Come Testare

### Test Upload Baseline
1. Apri l'app
2. Click "Genera Nuova Baseline"
3. Scegli "Vista Posteriore" o "Vista Laterale"
4. Scegli "Carica Video"
5. Carica 5 video
6. Inserisci FPS (es: 30) e Velocità (es: 10)
7. Click "🚀 Crea Baseline"
8. **Verifica**: 
   - Vedi loading (spinner overlay)
   - Dopo processing → Step 6 mostra risultati baseline
   - NON vedi lo step di registrazione

### Test Upload Analizza
1. Apri l'app (con baseline già creata)
2. Click "Analizza Video"
3. Scegli stessa vista della baseline
4. Scegli "Carica Video"
5. Carica 1 video + inserisci params
6. Click "🔍 Avvia Analisi"
7. **Verifica**:
   - Vedi loading
   - Dopo processing → Step 6 mostra risultati analisi
   - Metriche con Z-scores
   - Grafici temporali

## 💡 Note Tecniche

### Loading State
Durante la chiamata API:
- `analysisStore.setLoading(true)` attiva l'overlay in StepHolder
- Mostra spinner + messaggio "Elaborazione..."
- Blocca l'interfaccia durante processing

### BaselineUploader.svelte
- **Status**: Non più usato nel nuovo flusso
- **Motivo**: Funzionalità migrata in Step4Analysis
- **Azione**: Può essere rimosso o mantenuto come backup

### Componenti Step vs Nome File
Attenzione alla nomenclatura:
- `Step2VideoMethod.svelte` → Mostrato come Step 3
- `Step3BaselineUpload.svelte` → Mostrato come Step 4
- `Step4Analysis.svelte` → Mostrato come Step 5
- `Step5Analysis.svelte` → Mostrato come Step 6 (solo record)
- `Step6Results.svelte` → Mostrato come Step 6 (upload) o 7 (record)

## 🚨 Se Continui a Vedere Problemi

### Problema: Ancora vedo lo step di registrazione
**Soluzione**: 
1. Riavvia il dev server frontend
2. Fai hard refresh del browser (Ctrl+Shift+R)
3. Verifica che le modifiche a StepHolder.svelte siano applicate

### Problema: Loading non si vede
**Verifica**:
1. `analysisStore.setLoading(true)` è chiamato in Step4Analysis
2. StepHolder.svelte ha l'overlay loading configurato
3. Console del browser per eventuali errori

### Problema: API call fallisce
**Verifica**:
1. Backend è in esecuzione (`python backend/app.py`)
2. URL è corretto: `http://localhost:5000/api/...`
3. `view_type` è incluso nel FormData
4. Console backend per errori

## 📞 Debug

### Console Browser (F12)
Cerca questi log:
```javascript
console.log('Starting analysis...')
console.log('API response:', data)
console.log('Results set:', results)
```

### Console Backend
Cerca questi log:
```
=== Creazione Baseline ===
📊 Parametri baseline: Vista=posterior, Velocità=10 km/h, FPS=30
Processing video 1/5: video1.mp4
✅ Baseline creata con successo!
```

---

**Data**: 28 Novembre 2025
**Versione**: 3.12.1
**Status**: ✅ Flusso Corretto

