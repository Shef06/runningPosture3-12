# 🚀 Guida Rapida - Jump Analyzer Pro

## Setup Iniziale (Prima Volta)

### 1. Setup Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 2. Setup Frontend

```bash
cd frontend
npm install
```

## Avvio Applicazione

### Metodo 1: Script Automatico (Windows)

Doppio click su `start_all.bat` nella cartella root del progetto.

Questo avvierà automaticamente sia backend che frontend in due finestre separate.

### Metodo 2: Manuale

#### Terminal 1 - Backend
```bash
cd backend
venv\Scripts\activate
python app.py
```

Backend disponibile su: http://localhost:5000

#### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```

Frontend disponibile su: http://localhost:3000

## Utilizzo

### 1. Creare la Baseline
1. Apri http://localhost:3000
2. Nella sezione "Crea Baseline Biomeccanica":
   - Clicca su "Clicca per selezionare 5 video"
   - Seleziona 5 video della tua corsa ottimale
   - Clicca su "🚀 Crea Baseline"
3. Attendi che il modello venga addestrato (può richiedere alcuni minuti)

### 2. Analizzare un Video
1. Nella sezione "Analizza Corsa":
   - Clicca su "📹 Seleziona Video"
   - Seleziona un video da analizzare
   - Clicca su "🔍 Analizza Corsa"
2. I risultati appariranno nella sezione "Risultati Analisi" con:
   - Anomaly Score numerico
   - Livello di anomalia (Ottimale, Buono, Moderato, Attenzione, Critico)
   - Interpretazione testuale
   - Dettagli tecnici

## Troubleshooting

### Backend non si avvia
- Verifica che Python 3.8+ sia installato: `python --version`
- Verifica che l'ambiente virtuale sia attivato
- Reinstalla le dipendenze: `pip install -r requirements.txt --upgrade`

### Frontend non si avvia
- Verifica che Node.js 16+ sia installato: `node --version`
- Reinstalla le dipendenze: `npm install`
- Pulisci la cache: `rm -rf node_modules package-lock.json && npm install`

### Errore CORS
- Assicurati che il backend sia avviato su http://localhost:5000
- Controlla che flask-cors sia installato

### Errore MediaPipe
- Su Windows, potrebbe essere necessario installare Visual C++ Redistributable
- Scarica da: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Video non viene processato
- Verifica che il formato video sia supportato (mp4, avi, mov, mkv, webm)
- Assicurati che il video contenga una persona in posizione frontale visibile
- Riduci la risoluzione del video se è molto grande

## Formati Video Supportati
- MP4 (consigliato)
- AVI
- MOV
- MKV
- WEBM

## Note Importanti

1. **Qualità Video**: Usa video con buona illuminazione e una visione frontale chiara del corpo
2. **Baseline**: Usa 5 video della tua migliore tecnica di corsa, non video con errori
3. **Analisi**: Dopo aver creato la baseline, puoi analizzare tutti i video che vuoi
4. **Modello**: Il modello baseline viene salvato e può essere riutilizzato

## Performance

- Estrazione keypoint: ~30 FPS su CPU moderna
- Addestramento baseline (5 video): 2-5 minuti
- Analisi singolo video: 30-60 secondi

## Prossimi Passi

1. Crea la tua baseline personale
2. Analizza video di sessioni di allenamento diverse
3. Monitora i miglioramenti nel tempo
4. Confronta l'anomaly score prima e dopo correzioni tecniche

Buon allenamento! 🏃‍♂️💪

