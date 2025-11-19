# 📹 Guida Upload 5 Video Baseline - Jump Analyzer Pro

## 🎯 Obiettivo
Implementare un sistema robusto per selezionare, gestire e visualizzare 5 video separati per la creazione della baseline biomeccanica.

## ✅ Features Implementate

### 1. Upload Multiplo con Drag & Drop

**Componente:** `Step3BaselineUpload.svelte`

**Funzionalità:**
- ✅ Upload multiplo (seleziona più file contemporaneamente)
- ✅ Drag & Drop area reattiva
- ✅ Validazione automatica (max 5 video)
- ✅ Filtro file video only
- ✅ Progress indicator (X/5 video)

**UI:**
```
┌─────────────────────────────────┐
│ Progress: ████░░  3/5 video     │
├─────────────────────────────────┤
│   📹                            │
│   Clicca o trascina i video    │
│   Ancora 2 video richiesti      │
└─────────────────────────────────┘
```

### 2. Gestione Lista Video

**Features:**
- ✅ Lista scrollabile con tutti i video caricati
- ✅ Card per ogni video con:
  - Numero progressivo (1-5)
  - Thumbnail preview
  - Nome file
  - Dimensione (MB)
  - Pulsante rimozione (×)
- ✅ Animazioni slideIn
- ✅ Hover effects

**UI:**
```
┌─────────────────────────────────┐
│ [1] [thumb] video1.mp4   45MB ×│
│ [2] [thumb] video2.mp4   52MB ×│
│ [3] [thumb] video3.mp4   48MB ×│
└─────────────────────────────────┘
```

### 3. Form Calibrazione Condizionale

**Logica:**
- Form appare SOLO quando tutti e 5 i video sono caricati
- Background verde success per indicare completamento
- Parametri: FPS, Altezza (cm), Massa (kg)

**Validazione:**
- Pulsante "Continua" disabilitato finché non ci sono 5 video
- Testo dinamico: "Carica X video rimanenti" vs "Continua →"

### 4. Video Gallery nel VideoHolder

**Componente:** `VideoHolder.svelte`

**Features:**
- ✅ Player principale con video corrente
- ✅ Navigazione prev/next con pulsanti
- ✅ Counter "X / 5"
- ✅ Griglia 5 thumbnail sotto il player
- ✅ Click su thumbnail per cambiare video
- ✅ Highlight video attivo (bordo verde)
- ✅ Numeri progressivi sui thumbnail

**UI:**
```
┌─────────────────────────────────┐
│                                 │
│      [Video Player]             │
│                                 │
│      ‹  2 / 5  ›               │
├─────────────────────────────────┤
│ [1] [2] [3] [4] [5]             │
│  ↑ active (green border)        │
└─────────────────────────────────┘
```

### 5. State Management Migliorato

**Store:** `analysisStore.js`

**Nuovi Stati:**
```javascript
baselineVideos: []        // Array di File objects
baselineVideoUrls: []     // Array di Blob URLs per preview
```

**Nuove Azioni:**
- `setBaselineVideos(files)` - Imposta array completo
- `addBaselineVideo(file)` - Aggiungi un video (max 5)
- `removeBaselineVideo(index)` - Rimuovi video specifico

**Memory Management:**
- Auto cleanup vecchi Blob URLs quando cambiati
- Revoca URLs su rimozione

### 6. API Integration

**Step4Analysis.svelte** aggiornato per:

```javascript
// Carica TUTTI e 5 i video separati
baselineVideos.forEach(video => {
  formData.append('videos', video);
});

// Aggiungi parametri
formData.append('fps', fps);
formData.append('height', height);
formData.append('mass', mass);
```

**Riepilogo Parametri:**
- Lista tutti e 5 i video con nomi
- Sub-items indentati per migliore leggibilità
- Overflow ellipsis per nomi lunghi

## 🎨 UX Miglioramenti

### Progress Indicator
- Barra di progresso visuale
- Colore: azzurro → verde quando completato
- Testo: "X / 5 video caricati"

### Drag & Drop Feedback
- Area cambia colore quando file dragged over
- Border diventa verde
- Leggero scale effect (1.02)

### Video Cards
- Animazione slideIn quando aggiunti
- Hover effect (bordo azzurro)
- Remove button con rotate animation

### Gallery Navigation
- Overlay navigation su video
- Backdrop blur effect
- Pulsanti circular con hover scale
- Disabled state per first/last video

### Thumbnails
- Grid responsive 5 colonne
- Active state con glow effect (box-shadow)
- Hover lift effect (translateY)
- Numeri con background dinamico (nero/verde)

## 📊 Flusso Utente Completo

### Baseline con Upload - Step by Step

1. **Step 1:** Seleziona "Genera Nuova Baseline"
2. **Step 2:** Seleziona "Carica Video"
3. **Step 3:** Upload 5 video
   - Clicca o drag & drop
   - Vedi progress: 0/5 → 5/5
   - Rimuovi/sostituisci se necessario
   - Inserisci FPS, altezza, massa (quando 5/5)
   - Clicca "Continua"
4. **Step 4:** Verifica riepilogo
   - Vedi lista 5 video
   - Vedi parametri calibrazione
   - Clicca "🚀 Crea Baseline"
5. **VideoHolder:** Naviga tra i 5 video
   - Player principale
   - Thumbnail grid sotto
   - Click per cambiare
   - Prev/Next buttons

## 🔧 Validazioni Implementate

### Step3BaselineUpload
- ✅ Max 5 video
- ✅ Solo file video (`video/*`)
- ✅ Duplicati prevenuti dall'array
- ✅ Button disabled se < 5 video

### Step4Analysis
- ✅ Verifica `baselineVideos.length === 5`
- ✅ Errore se non esattamente 5
- ✅ FormData con tutti i 5 file

### analysisStore
- ✅ `addBaselineVideo` ritorna early se già 5
- ✅ Blob URL cleanup automatico
- ✅ Reset completo su `reset()`

## 🎯 Differenze Upload Baseline vs Analisi

| Feature | Baseline (5 video) | Analisi (1 video) |
|---------|-------------------|-------------------|
| Componente Step3 | Step3BaselineUpload | Step3Calibration |
| Upload multiplo | ✅ Sì | ❌ No |
| Drag & Drop | ✅ Sì | ❌ No |
| Progress bar | ✅ Sì | ❌ No |
| Lista video | ✅ Sì (5) | ❌ No |
| Rimozione video | ✅ Sì | ❌ No |
| Gallery VideoHolder | ✅ Sì | ❌ No (solo player) |
| Form calibrazione | ✅ Quando 5/5 | ✅ Sempre visibile |

## 📦 File Modificati/Creati

### Nuovi File (1)
1. `frontend/src/lib/components/steps/Step3BaselineUpload.svelte` ⭐

### File Modificati (4)
1. `frontend/src/lib/stores/analysisStore.js`
   - Aggiunti `baselineVideos`, `baselineVideoUrls`
   - Aggiunte azioni: `setBaselineVideos`, `addBaselineVideo`, `removeBaselineVideo`

2. `frontend/src/lib/components/StepHolder.svelte`
   - Logica condizionale per Step3: baseline usa Step3BaselineUpload

3. `frontend/src/lib/components/VideoHolder.svelte`
   - Gallery mode per baseline con 5 video
   - Navigation prev/next
   - Thumbnail grid

4. `frontend/src/lib/components/steps/Step4Analysis.svelte`
   - Loop tutti i 5 video in FormData
   - Riepilogo con lista 5 video
   - Validazione 5 video richiesti

## 🚀 Testing

### Test Scenari

#### Scenario 1: Upload Normale
1. Seleziona 5 video ✅
2. Vedi tutti in lista ✅
3. Completa calibrazione ✅
4. Vai a Step 4 ✅
5. Vedi riepilogo 5 video ✅
6. Crea baseline ✅

#### Scenario 2: Rimozione Video
1. Carica 3 video
2. Rimuovi il secondo (click ×)
3. Verifica: ora 2 video
4. Progress: 2/5
5. Aggiungi altri 3
6. Progress: 5/5 ✅

#### Scenario 3: Drag & Drop
1. Drag 5 file sulla area
2. Vedi feedback drag-over (verde)
3. Drop
4. Tutti e 5 caricati ✅

#### Scenario 4: Gallery Navigation
1. Completa upload 5 video
2. Vai a Step 4
3. VideoHolder mostra gallery
4. Click prev/next
5. Click thumbnails
6. Video cambiano correttamente ✅

#### Scenario 5: Validazione
1. Carica solo 3 video
2. Button "Continua" disabilitato ✅
3. Form calibrazione nascosto ✅
4. Aggiungi 2 video
5. Form appare ✅
6. Button enabled ✅

## 💡 Best Practices Implementate

### Performance
- ✅ Blob URLs per preview (no re-upload)
- ✅ Cleanup automatico URLs
- ✅ Lazy rendering thumbnails
- ✅ CSS transitions hardware-accelerated

### Accessibilità
- ✅ Button con title attributes
- ✅ Keyboard navigation support
- ✅ Disabled states chiari
- ✅ Counter visuale progress

### UX
- ✅ Feedback immediato (animazioni)
- ✅ Progress chiaro
- ✅ Errori preventivi (validazione)
- ✅ Undo friendly (rimozione)

### Code Quality
- ✅ Reactive statements ($:)
- ✅ Single source of truth (store)
- ✅ Componentizzazione
- ✅ Styles scoped

## 🔮 Future Enhancements

### Possibili Migliorie
- [ ] Reorder video (drag & drop nella lista)
- [ ] Replace video (click per sostituire specifico)
- [ ] Bulk upload (cartella)
- [ ] Video trimming (seleziona porzione)
- [ ] Auto-detect FPS da metadata video
- [ ] Preview simultanea 2x2 grid
- [ ] Export/Import configurazione
- [ ] Salva draft (localStorage)

## 📝 Note Backend

Il backend riceverà ora:

```javascript
FormData {
  videos: File,  // 5 volte
  videos: File,
  videos: File,
  videos: File,
  videos: File,
  fps: "30",
  height: "180",
  mass: "70"
}
```

**Backend deve:**
- ✅ Accettare esattamente 5 file nella chiave `videos`
- ✅ Validare che siano tutti video
- ✅ Processarli separatamente
- ✅ Concatenare features da tutti e 5
- ✅ Usare parametri fps, height, mass

## 🎉 Risultato Finale

Sistema completo e robusto per:
- ✅ Upload intuitivo di 5 video separati
- ✅ Gestione individuale di ogni video
- ✅ Visualizzazione gallery professionale
- ✅ Validazione completa
- ✅ UX moderna e fluida

**Ready for testing!** 🚀

---

**Versione**: 2.2.0 - Baseline 5 Videos  
**Data**: Novembre 2025

