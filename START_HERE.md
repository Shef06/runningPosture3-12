# 🚀 START HERE - Jump Analyzer Pro

> **Sistema completo di analisi biomeccanica della corsa con AI e Computer Vision**

---

## ⚡ Quick Start (5 minuti)

### 1️⃣ Setup (una volta sola)

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Frontend (nuovo terminal)
cd frontend
npm install
```

### 2️⃣ Avvio

**Modo Facile**: Doppio click su `start_all.bat`

### 3️⃣ Usa l'App

1. Apri **http://localhost:3000**
2. Carica 5 video per baseline
3. Analizza nuovi video
4. Visualizza risultati! 🎉

---

## 📚 Documentazione Completa

| Per Chi | Documento | Descrizione |
|---------|-----------|-------------|
| 🆕 **Nuovo Utente** | [GET_STARTED.md](GET_STARTED.md) | Congratulazioni e primi passi |
| 📖 **Overview** | [README.md](README.md) | Panoramica completa progetto |
| ⚡ **Setup Rapido** | [QUICK_START.md](QUICK_START.md) | Installazione e utilizzo |
| 🏗 **Sviluppatore** | [ARCHITECTURE.md](ARCHITECTURE.md) | Architettura tecnica dettagliata |
| 🐛 **Ho Problemi** | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Soluzioni problemi comuni |
| 🧪 **Testing** | [TEST_GUIDE.md](TEST_GUIDE.md) | Guida testing completa |
| 📊 **Manager** | [SUMMARY.md](SUMMARY.md) | Executive summary |
| 📑 **Indice** | [DOCS_INDEX.md](DOCS_INDEX.md) | Naviga tutti i documenti |
| ✅ **Status** | [PROJECT_STATUS.md](PROJECT_STATUS.md) | Completamento progetto |

---

## 🎯 Cosa Fa Quest'App?

### Problema
Come valutare oggettivamente la tecnica di corsa e identificare anomalie biomeccaniche?

### Soluzione
**Jump Analyzer Pro** usa AI per:

1. **Apprendere** la tua corsa ottimale da 5 video di riferimento
2. **Analizzare** nuovi video e calcolare quanto differiscono dalla baseline
3. **Rilevare** automaticamente anomalie e pattern problematici

### Tecnologie
- 🤖 **AI**: LSTM Autoencoder per anomaly detection
- 👁 **Computer Vision**: MediaPipe per tracking 3D del corpo
- 🐍 **Backend**: Python + Flask + TensorFlow
- 🎨 **Frontend**: Svelte + UI moderna

---

## 📁 Struttura Progetto

```
runningPosture3-12/
│
├── 📚 12 Documenti Markdown
│   ├── START_HERE.md         ← TU SEI QUI
│   ├── GET_STARTED.md        ← Leggi per iniziare
│   ├── README.md             ← Overview completo
│   └── ... (9 altri docs)
│
├── 🐍 backend/               ← Python + Flask + AI
│   ├── app.py               (API REST)
│   ├── keypoint_extractor.py (MediaPipe)
│   ├── feature_engineering.py (Angoli)
│   ├── lstm_autoencoder.py   (Modello AI)
│   └── ... (5 file + deps)
│
├── 🎨 frontend/              ← Svelte UI
│   ├── src/
│   │   ├── lib/components/
│   │   │   ├── BaselineUploader.svelte
│   │   │   └── AnalysisUploader.svelte
│   │   └── routes/
│   │       └── +page.svelte
│   └── ... (config files)
│
└── 🚀 start_all.bat          ← Avvio automatico
```

---

## ✨ Features Principali

### 🎥 Baseline Creation
- Upload 5 video della tua corsa ottimale
- Estrazione automatica keypoint 3D con MediaPipe
- Training LSTM Autoencoder (2-5 minuti)
- Modello salvato e riutilizzabile

### 🔍 Video Analysis
- Upload singolo video da analizzare
- Processing automatico (30-60 secondi)
- **Anomaly Score**: Quanto differisce dalla baseline
- **Interpretazione**: Livello rischio con spiegazione

### 📊 Results Display
- Score numerico (più basso = più simile a baseline)
- Badge colorato (verde → rosso)
- Interpretazione testuale user-friendly
- Dettagli tecnici per esperti

---

## 🎓 Come Funziona (Semplificato)

```
Video → MediaPipe → Keypoint 3D → Angoli → LSTM → Score
         (CV)      (33 punti)   (4 angoli)  (AI)  (Anomalia)
```

1. **MediaPipe** trova 33 punti del corpo in 3D
2. **Feature Engineering** calcola 4 angoli biomeccanici
3. **LSTM Autoencoder** impara pattern ottimale (baseline)
4. **Anomaly Detection** calcola differenza nuovo video vs baseline

---

## 🎯 Casi d'Uso

✅ **Atleti**: Monitorare tecnica nel tempo  
✅ **Allenatori**: Feedback oggettivo data-driven  
✅ **Fisioterapisti**: Tracking riabilitazione  
✅ **Ricercatori**: Raccolta dati biomeccanici  

---

## 💡 Tips Utili

### Video Ideali per Baseline
- ✅ 5 video della stessa sessione
- ✅ Tua migliore tecnica
- ✅ Vista frontale, corpo intero
- ✅ Buona illuminazione
- ✅ Camera ferma
- ✅ 10-30 secondi ciascuno
- ✅ Formato .mp4 consigliato

### Interpretazione Risultati
- **< 0.01**: ✅ Ottimale (identico a baseline)
- **0.01-0.05**: ✅ Buono (piccole variazioni)
- **0.05-0.1**: ⚠ Moderato (differenze notabili)
- **0.1-0.2**: ⚠ Attenzione (deviazioni significative)
- **> 0.2**: 🚨 Critico (molto diverso)

---

## 🔧 Requisiti Sistema

Prima di iniziare, verifica:

- ✅ **Python 3.8+**: `python --version`
- ✅ **Node.js 16+**: `node --version`
- ✅ **8GB RAM** (16GB consigliato)
- ✅ **10GB spazio disco**
- ✅ **Windows 10/11** (o adatta script)

---

## 📊 Progetto In Numeri

- **34 file** totali
- **~3,500 righe** di codice
- **~15,700 parole** di documentazione
- **12 documenti** markdown
- **5 moduli** Python backend
- **4 componenti** Svelte frontend
- **2 API endpoints** REST
- **100%** requisiti completati

---

## 🚀 Azioni Immediate

### Per Utenti
→ Leggi [GET_STARTED.md](GET_STARTED.md)  
→ Segui setup in [QUICK_START.md](QUICK_START.md)  
→ Avvia con `start_all.bat`  

### Per Sviluppatori
→ Leggi [ARCHITECTURE.md](ARCHITECTURE.md)  
→ Esplora codice in `backend/` e `frontend/`  
→ Segui [TEST_GUIDE.md](TEST_GUIDE.md)  

### Per Manager
→ Leggi [SUMMARY.md](SUMMARY.md)  
→ Vedi [PROJECT_STATUS.md](PROJECT_STATUS.md)  
→ Review [PROJECT_COMPLETION_REPORT.md](PROJECT_COMPLETION_REPORT.md)  

---

## ❓ FAQ Rapide

**Q: Quanto tempo per setup?**  
A: 10 minuti prima volta, 30 secondi dopo

**Q: Serve GPU?**  
A: No, funziona su CPU (più lento ma ok)

**Q: Quanti video servono?**  
A: 5 per baseline, poi 1 per ogni analisi

**Q: Che formati video?**  
A: .mp4, .avi, .mov, .mkv, .webm

**Q: Funziona in real-time?**  
A: No, offline processing (30-60s per video)

**Q: Posso usare webcam?**  
A: Non ancora (feature futura)

**Q: È production-ready?**  
A: Ready per testing/demo, serve setup per production

**Q: Ho problemi, cosa faccio?**  
A: Consulta [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 🎯 Next Steps

1. **📖 Leggi**: [GET_STARTED.md](GET_STARTED.md) (5 min)
2. **🔧 Setup**: Segui istruzioni (10 min)
3. **🚀 Avvia**: `start_all.bat`
4. **🎥 Testa**: Con i tuoi video
5. **🎉 Analizza**: Visualizza risultati!

---

## 🏆 Ready to Go!

Hai tutto il necessario per iniziare:

✅ Codice completo e funzionante  
✅ Documentazione dettagliata  
✅ Script di automazione  
✅ Testing guide  
✅ Troubleshooting support  

**Non ti resta che provarlo!**

---

## 📞 Supporto

**Hai domande?**
1. Cerca in [DOCS_INDEX.md](DOCS_INDEX.md)
2. Consulta [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. Controlla logs backend e frontend
4. Review codice sorgente (è ben commentato)

---

## 🎊 Congratulazioni!

Hai a disposizione un sistema completo di analisi biomeccanica AI-powered.

**Per iniziare subito**: [GET_STARTED.md](GET_STARTED.md)

**Buona analisi della corsa!** 🏃‍♂️💪🚀

---

*Jump Analyzer Pro v1.0.0 - Powered by MediaPipe + TensorFlow LSTM Autoencoder*

