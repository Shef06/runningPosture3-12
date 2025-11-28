# Guida Rapida: Vista Laterale - Running Analyzer

## 🎯 Cosa è Cambiato

L'applicazione ora supporta **due prospettive** di analisi:

### Vista Posteriore (Esistente)
- Video da **dietro** il corridore
- Analizza: Valgismo ginocchia, Caduta pelvica, Cadenza

### Vista Laterale (Nuova) ✨
- Video di **profilo** del corridore  
- Analizza: Overstriding, Flessione ginocchio, Inclinazione tronco, Tempo di contatto

## 📹 Come Usare

### 1. Creare una Baseline

1. Seleziona "Genera Nuova Baseline"
2. **NUOVO**: Scegli "Vista Laterale" o "Vista Posteriore"
3. Scegli metodo (Upload o Registra)
4. Fornisci 5 video della stessa prospettiva
5. Inserisci FPS e velocità tapis roulant
6. Avvia creazione baseline

### 2. Analizzare un Video

1. Seleziona "Analizza Video"
2. **NUOVO**: Scegli la stessa vista della baseline
3. Carica il video da analizzare
4. Inserisci parametri
5. Avvia analisi

### ⚠️ Importante
- La vista del video da analizzare **deve corrispondere** alla vista della baseline
- Non puoi analizzare video laterale con baseline posteriore (e viceversa)

## 📊 Metriche Analizzate

### Vista Posteriore
| Metrica | Descrizione | Unità |
|---------|-------------|-------|
| Valgismo Ginocchio SX/DX | Deviazione mediale del ginocchio | ° (gradi) |
| Caduta Pelvica | Inclinazione del bacino | ° (gradi) |
| Cadenza | Passi al minuto | spm |

### Vista Laterale
| Metrica | Descrizione | Unità |
|---------|-------------|-------|
| Overstriding | Distanza caviglia-anca al contatto | m (metri) |
| Flessione Ginocchio @ IC | Angolo ginocchio al contatto iniziale | ° (gradi) |
| Trunk Lean | Inclinazione tronco vs verticale | ° (gradi) |
| Ground Contact Time (GCT) | Tempo piede a terra | s (secondi) |

## 🎬 Consigli per Video Ottimali

### Vista Posteriore
- Posiziona la camera **dietro** il corridore
- Inquadratura: dalla testa ai piedi
- Mantieni distanza costante dal tapis roulant
- Evita angolazioni oblique

### Vista Laterale
- Posiziona la camera di **profilo** al corridore
- Inquadratura: tutto il corpo visibile
- Perpendicolare al tapis roulant (90°)
- Mantieni altezza camera a metà del corpo

## 🔍 Interpretazione Risultati

### Z-Score
- **|Z| < 1.0** → 🟢 Ottimale (nella norma)
- **1.0 ≤ |Z| < 2.0** → 🟡 Attenzione (lieve deviazione)
- **|Z| ≥ 2.0** → 🔴 Critico (deviazione significativa)

### Valori Tipici Vista Laterale

**Overstriding**
- Ottimale: < 0.05m
- Attenzione: 0.05-0.10m
- Critico: > 0.10m

**Flessione Ginocchio @ IC**
- Ottimale: 15-20°
- Attenzione: 10-15° o 20-25°
- Critico: < 10° o > 25°

**Trunk Lean**
- Ottimale: 5-10° (avanti)
- Attenzione: 0-5° o 10-15°
- Critico: < 0° (indietro) o > 15°

**Ground Contact Time**
- Ottimale: 0.20-0.25s
- Attenzione: 0.25-0.30s o 0.15-0.20s
- Critico: > 0.30s o < 0.15s

## 🛠️ Troubleshooting

### Problema: "Il tipo di vista non corrisponde alla baseline"
**Soluzione**: Crea una nuova baseline con la vista corretta, oppure usa un video con la vista della baseline esistente.

### Problema: Metriche laterali mostrano valori strani
**Verifica**:
- Video di profilo perfetto (90° dal tapis roulant)
- Corridore completamente visibile
- Buona illuminazione
- Video stabile (no movimenti camera)

### Problema: Ground Contact Time non rilevato
**Cause**:
- Video troppo corto (serve almeno 2-3 secondi di corsa)
- Scarsa visibilità caviglie/piedi
- FPS troppo bassi (minimo 24fps raccomandato)

## 📈 Best Practices

1. **Consistenza**: Usa sempre la stessa prospettiva per baseline e analisi
2. **Qualità Video**: Risoluzione minima 720p, 30fps ideale
3. **Lighting**: Illuminazione uniforme, evita controluce
4. **Setup**: Posizione camera fissa durante registrazione
5. **Durata**: 10-15 secondi per video (più lungo = statistiche migliori)

## 🔄 Workflow Completo

```
┌─────────────────┐
│ Scelta Azione   │ → Baseline o Analizza
└────────┬────────┘
         ↓
┌─────────────────┐
│ Selezione Vista │ → Posteriore o Laterale ⭐ NUOVO
└────────┬────────┘
         ↓
┌─────────────────┐
│ Metodo Video    │ → Upload o Registra
└────────┬────────┘
         ↓
┌─────────────────┐
│ Acquisizione    │ → 5 video (baseline) o 1 video (analisi)
└────────┬────────┘
         ↓
┌─────────────────┐
│ Calibrazione    │ → FPS e velocità
└────────┬────────┘
         ↓
┌─────────────────┐
│ Processing      │ → MediaPipe + Calcoli geometrici
└────────┬────────┘
         ↓
┌─────────────────┐
│ Risultati       │ → Metriche + Grafici + Z-Scores
└─────────────────┘
```

## 💡 Esempi d'Uso

### Scenario 1: Atleta con Overstriding
1. Crea baseline vista laterale
2. Analizza video tecnica attuale
3. Overstriding alto? → Lavora su contatto sotto centro massa
4. Ri-analizza dopo correzioni

### Scenario 2: Runner con Valgismo
1. Crea baseline vista posteriore
2. Analizza video tecnica attuale
3. Valgismo eccessivo? → Rinforzo glutei/core
4. Monitora progressi con analisi periodiche

### Scenario 3: Analisi Completa
1. Crea baseline posteriore (5 video)
2. Crea baseline laterale (5 video)
3. Analizza con entrambe le prospettive
4. Ottieni quadro biomeccanico completo

## 📞 Supporto

Per problemi o domande:
1. Controlla questa guida
2. Verifica LATERAL_VIEW_IMPLEMENTATION.md per dettagli tecnici
3. Controlla i log del backend per errori specifici

---

**Versione**: 3.12 con Vista Laterale
**Data**: 28 Novembre 2025

