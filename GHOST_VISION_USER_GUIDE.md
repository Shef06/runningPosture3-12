# Ghost Vision - User Guide

## Cos'è Ghost Vision?

**Ghost Vision** è una funzionalità innovativa che ti permette di vedere la "forma perfetta" della tua corsa sovrapposta al tuo video reale. Vedrai una silhouette semitrasparente (il "fantasma") che rappresenta la baseline biomeccanica ottimale, permettendoti di confrontare visivamente la tua postura con quella ideale in tempo reale.

## Come Funziona

### Passo 1: Crea la Baseline (Forma Perfetta)

1. **Seleziona "Crea Baseline"** dal menu principale
2. **Carica 5 video** della tua corsa in condizioni ottimali:
   - Video della stessa persona
   - Stessa velocità del tapis roulant
   - Stessa vista (posteriore o laterale)
   - Condizioni simili (riscaldamento, non affaticato)
3. **Inserisci parametri di calibrazione**:
   - Velocità tapis roulant (km/h)
   - FPS del video
   - Tipo di vista (posteriore/laterale)
4. **Avvia analisi** → L'app processa i 5 video e genera:
   - Statistiche baseline (media, deviazione standard)
   - **Ghost frames** (silhouette della forma migliore)

### Passo 2: Analizza il Tuo Video

1. **Seleziona "Analizza Video"** dal menu principale
2. **Carica il video** che vuoi confrontare con la baseline
3. **Usa stessi parametri** della baseline (velocità, FPS, vista)
4. **Avvia analisi** → L'app processa il video e mostra:
   - Video con scheletro (pose overlay)
   - Metriche biomeccaniche confrontate con baseline
   - Grafici temporali
   - **Toggle Ghost Vision** (se disponibile)

### Passo 3: Attiva Ghost Vision

Nella schermata **Risultati**:

1. **Trova la sezione "Ghost Vision"** (sotto le metriche principali)
2. **Attiva l'interruttore** "Ghost Vision"
   ```
   👻 Ghost Vision
   Sovrapponi la silhouette della baseline perfetta al tuo video
   [OFF] ← Clicca per attivare
   ```
3. **Guarda il video** con l'overlay attivo:
   - Silhouette ciano semitrasparente = Forma baseline ottimale
   - Video completo = Tua corsa reale
   - Confronta visivamente le differenze

## Cosa Puoi Vedere con Ghost Vision

### Vista Posteriore (Posterior)

**Confronta:**
- **Oscillazione laterale del tronco**
  - Ghost dritto → Tu oscillante = Problema di stabilità
- **Caduta pelvica**
  - Ghost livellato → Tuo bacino inclinato = Squilibrio muscolare
- **Valgismo delle ginocchia**
  - Ghost ginocchia dritte → Tue ginocchia verso interno = Rischio infortunio
- **Simmetria braccia**
  - Ghost simmetrico → Tue braccia asimmetriche = Spreco energia

### Vista Laterale (Lateral)

**Confronta:**
- **Inclinazione del tronco**
  - Ghost verticale → Tu troppo avanti = Rischio caduta, affaticamento
- **Overstriding** (piede troppo avanti)
  - Ghost piede sotto anca → Tuo piede davanti = Frenata, stress ginocchia
- **Flessione ginocchio al contatto**
  - Ghost ginocchio flesso → Tuo ginocchio rigido = Impatto elevato
- **Posizione braccia**
  - Ghost braccia a 90° → Tue braccia diverse = Inefficienza

## Interpretazione Visiva

### Overlay Perfettamente Allineato ✅
```
   USER VIDEO        GHOST OVERLAY
      │                   │
      ├───────────────────┤
      │   Allineamento    │
      │    perfetto!      │
      └───────────────────┘
```
**Significato**: La tua postura è ottimale, in linea con la baseline.

### Deviazioni Evidenti ⚠️
```
   USER VIDEO        GHOST OVERLAY
      │                   │
      ├──┐            ┌───┤
      │  └────────────┘   │ ← Deviazione visibile
      │   Tronco troppo   │
      │    inclinato      │
      └───────────────────┘
```
**Significato**: C'è una differenza significativa da correggere.

## Consigli per l'Uso

### Best Practices

1. **Video di Qualità**
   - Illuminazione buona
   - Camera stabile (treppiede)
   - Inquadratura completa del corpo
   - Sfondo contrastante

2. **Condizioni Simili**
   - Confronta video alla stessa velocità
   - Stesso livello di affaticamento
   - Stessa vista (posteriore/laterale)

3. **Interpretazione**
   - Usa Ghost Vision insieme alle metriche numeriche
   - Piccole differenze sono normali
   - Focus su pattern ricorrenti
   - Consulta un professionista per grandi deviazioni

### Limitazioni

- **Sincronizzazione Temporale**: Ghost si basa sul tempo del video, non sulla fase del ciclo del passo
- **FPS Costante**: Presume FPS costante (30 fps di default)
- **Segmentazione Richiesta**: Necessita che MediaPipe rilevi correttamente il corpo
- **Video Singola Baseline**: Mostra solo la baseline "migliore" dei 5 video

## Troubleshooting

### Ghost Vision Non Disponibile?

**Possibili cause:**
- Baseline non ancora creata
- Baseline creata con versione precedente (senza segmentazione)
- Errore durante generazione ghost frames
- Baseline corrotta o incompleta

**Soluzione:** Ricrea la baseline con i 5 video.

### Ghost Overlay Non Sincronizzato?

**Possibili cause:**
- FPS del video diverso dal dichiarato
- Video a velocità variabile
- Problemi di buffering rete

**Soluzione:** 
- Verifica FPS corretti nella calibrazione
- Ricarica la pagina
- Controlla connessione backend

### Ghost Non Visibile?

**Possibili cause:**
- Toggle disattivato
- Opacità troppo bassa
- Frame non disponibile per questo timestamp

**Soluzione:**
- Verifica che toggle sia ON
- Prova a riavviare il video
- Controlla console browser per errori

### Silhouette Sfocata o Distorta?

**Possibili cause:**
- Video baseline di bassa qualità
- Segmentazione MediaPipe imprecisa
- Problemi di scala/risoluzione

**Soluzione:**
- Usa video ad alta risoluzione per baseline
- Assicura buona illuminazione nei video baseline
- Ricrea baseline con video migliori

## Esempi di Utilizzo

### Caso 1: Correzione Trunk Lean

**Osservazione con Ghost Vision:**
- Ghost: tronco quasi verticale
- Tuo video: tronco inclinato ~20° in avanti

**Azione:**
- Consapevolezza della postura
- Esercizi di core stability
- Correzione graduale durante allenamenti
- Rianalizza dopo 2 settimane

### Caso 2: Riduzione Valgismo Ginocchia

**Osservazione con Ghost Vision:**
- Ghost: ginocchia allineate verticalmente
- Tuo video: ginocchia che convergono verso interno

**Azione:**
- Rinforzo muscoli abduttori (glutei)
- Esercizi propriocettivi
- Controllo durante corsa
- Monitoraggio progressi settimanale

### Caso 3: Simmetria Braccia

**Osservazione con Ghost Vision:**
- Ghost: braccia simmetriche, movimento uguale
- Tuo video: braccio destro più alto e oscillante

**Azione:**
- Focus su movimento braccia durante warm-up
- Esercizi di coordinazione bilaterale
- Video feedback regolare
- Correzione con Ghost Vision attivo

## FAQ

**Q: Posso usare Ghost Vision durante la corsa?**
A: No, Ghost Vision è uno strumento di analisi post-corsa. Analizza il video dopo l'allenamento.

**Q: Devo ricreare la baseline ogni volta?**
A: No, la baseline viene salvata. Ricreala solo se cambiano condizioni (velocità, forma fisica, ecc.).

**Q: Posso confrontare con baseline di altre persone?**
A: Attualmente no. Ghost Vision confronta con la TUA baseline personale ottimale.

**Q: Quanto è accurato Ghost Vision?**
A: Dipende dalla qualità dei video baseline e dalla precisione di MediaPipe. Usa come guida visiva, non diagnosi medica.

**Q: Posso modificare il colore del ghost?**
A: Attualmente fisso (ciano). Funzionalità futura permetterà personalizzazione.

**Q: Funziona con video dalla webcam?**
A: Sì, se la webcam registra video di qualità sufficiente per MediaPipe.

## Contatti e Supporto

Per problemi tecnici o suggerimenti:
- Controlla console del browser (F12) per errori
- Verifica log del backend per messaggi di debug
- Ricrea baseline se Ghost Vision non funziona
- Assicura che backend sia in esecuzione (porta 5000)

## Prossime Funzionalità

Previste per versioni future:
- [ ] Opacità regolabile (slider 30%-70%)
- [ ] Scelta colore ghost (cyan, verde, viola)
- [ ] Sincronizzazione per fase gait cycle
- [ ] Vista split-screen (ghost + video affiancati)
- [ ] Heatmap di deviazione
- [ ] Confronto multipli baselines
- [ ] Export overlay video con ghost

