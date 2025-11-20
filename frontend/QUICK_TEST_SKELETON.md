# 🧪 Test Rapido Analisi Scheletro

## 📋 Come Testare la Funzionalità

### 1. Avvia il Frontend

```bash
cd frontend
npm run dev
```

Il server dovrebbe avviarsi su `http://localhost:5173`

### 2. Percorso di Test

1. **Step 1**: Clicca su **"Analizza Video"**
2. **Step 2**: Clicca su **"Carica Video"**  
3. **Step 3**: 
   - Carica un video di corsa (.mp4, .webm, etc.)
   - Inserisci parametri:
     - FPS: 30 (default)
     - Altezza: 180 cm
     - Massa: 70 kg
   - Clicca **"Avvia Analisi →"**
4. **Step 4**: 
   - Verifica i parametri nel riepilogo
   - Clicca **"🔍 Avvia Analisi"**
5. **Risultato**: 
   - Il video appare nel VideoHolder (sinistra)
   - MediaPipe si carica (vedi console)
   - Il video parte automaticamente con lo scheletro sovrapposto

### 3. Cosa Dovresti Vedere

#### Nel VideoHolder (sinistra):

```
┌──────────────────────────────┐
│                              │
│   🎬 Video con scheletro     │
│   ┌─────────────────────┐   │
│   │                     │   │
│   │  👤 (scheletro      │   │
│   │      verde/rosso)   │   │
│   │                     │   │
│   └─────────────────────┘   │
│                              │
│   ▶️ Riproduci / ⏸️ Ferma   │
│                              │
│   🟢 Analisi in corso...     │
└──────────────────────────────┘
```

#### Console del Browser (F12):

```
✅ MediaPipe Pose inizializzato
📹 Video caricato: 1920x1080
🎬 Analisi video avviata
```

### 4. Controlli Disponibili

- **▶️ Riproduci con Scheletro**: Avvia l'analisi
- **⏸️ Ferma**: Mette in pausa
- **Video controls**: Barra di avanzamento HTML nativa

### 5. Indicatori Visivi

#### Durante l'analisi:
- ✅ Scheletro verde (connessioni)
- ✅ Punti rossi (landmark/giunti)
- ✅ Indicatore "Analisi in corso..." con pallino pulsante
- ✅ Canvas overlay visibile

#### Quando fermo:
- ❌ Canvas overlay nascosto (opacity: 0)
- ❌ Video in pausa
- ❌ Nessun indicatore di analisi

## 🎯 Video di Test Consigliati

### Caratteristiche Ideali:
- **Risoluzione**: 720p o superiore
- **FPS**: 30 o 60
- **Vista**: Laterale o frontale della persona
- **Illuminazione**: Buona (per miglior rilevamento)
- **Soggetto**: Persona che corre/cammina
- **Durata**: 10-30 secondi

### Dove Trovare Video di Test:
1. Registra con webcam (Step "Registra Video")
2. Usa video di esempio online
3. Video personali di corsa

## 🐛 Troubleshooting

### MediaPipe non si carica

**Sintomo**: Console mostra "❌ Errore inizializzazione MediaPipe"

**Soluzioni**:
1. Controlla connessione internet (MediaPipe viene da CDN)
2. Verifica console per errori CORS
3. Ricarica la pagina

### Scheletro non appare

**Sintomo**: Video riprodotto ma nessun scheletro

**Controlla**:
1. Console: cerca "✅ MediaPipe Pose inizializzato"
2. Verifica che `isAnalyzing === true` (dev tools)
3. Controlla che il canvas abbia `opacity: 1`

**Debug**:
```javascript
// Nel browser console:
$analysisStore.isAnalyzing  // dovrebbe essere true
```

### Video non si carica

**Sintomo**: Placeholder invece del video

**Soluzioni**:
1. Verifica formato video supportato (.mp4, .webm, .ogv)
2. Controlla dimensione file (<100MB consigliato)
3. Prova con un altro video

### Performance Lenta

**Sintomo**: Frame rate basso, video laggy

**Soluzioni**:
1. Usa video a risoluzione inferiore (720p invece di 4K)
2. Chiudi altre tab del browser
3. Modifica `modelComplexity` in VideoAnalyzer.svelte:
   ```javascript
   pose.setOptions({
     modelComplexity: 0,  // 0=lite, 1=full, 2=heavy
   });
   ```

## 📊 Verifica Funzionamento

### Checklist:
- [ ] Frontend avviato senza errori
- [ ] Navigazione attraverso gli step funzionante
- [ ] Video caricato correttamente
- [ ] Console mostra "✅ MediaPipe Pose inizializzato"
- [ ] Video riprodotto quando si clicca "Avvia Analisi"
- [ ] Scheletro visibile sovrapposto al video
- [ ] Punti rossi sui giunti del corpo
- [ ] Linee verdi tra i giunti
- [ ] Indicatore "Analisi in corso..." visibile
- [ ] Pulsante "Ferma" funzionante
- [ ] Video si ferma al termine
- [ ] Messaggio "✅ Analisi completata!" appare

## 📝 Test Edge Cases

### Test 1: Video senza persona
- ✅ Non dovrebbero apparire landmark
- ✅ Canvas dovrebbe rimanere trasparente

### Test 2: Persona parzialmente visibile
- ✅ Solo i landmark visibili dovrebbero essere disegnati
- ✅ Nessun errore in console

### Test 3: Video molto lungo
- ✅ L'analisi dovrebbe continuare fino alla fine
- ✅ Nessun memory leak

### Test 4: Mettere in pausa e riprendere
- ✅ Ferma → riavvia dovrebbe funzionare correttamente
- ✅ Lo scheletro dovrebbe riattivarsi

## 🎉 Successo!

Se vedi:
```
✅ Video riprodotto
✅ Scheletro sovrapposto
✅ Movimenti fluidi
✅ Nessun errore in console
```

**La funzionalità è implementata correttamente!** 🎊

## 🚀 Next Steps

Dopo aver verificato che funziona:
1. Testare con più video diversi
2. Provare diverse risoluzioni
3. Testare su diversi browser (Chrome, Firefox, Edge)
4. Ottimizzare performance se necessario

---

**Tempo test stimato**: 5-10 minuti  
**Browser consigliato**: Chrome (migliore supporto MediaPipe)











