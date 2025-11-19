# 🔧 Troubleshooting Guide - Jump Analyzer Pro

## Problemi Comuni e Soluzioni

### 🐍 Backend Issues

#### Problema: `ModuleNotFoundError: No module named 'flask'`
**Causa**: Dipendenze non installate o ambiente virtuale non attivato

**Soluzione**:
```bash
cd backend
# Attiva ambiente virtuale
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Reinstalla dipendenze
pip install -r requirements.txt
```

#### Problema: `ModuleNotFoundError: No module named 'tensorflow'`
**Causa**: TensorFlow non installato correttamente

**Soluzione**:
```bash
# Disinstalla e reinstalla TensorFlow
pip uninstall tensorflow
pip install tensorflow==2.15.0

# Se fallisce, prova la versione CPU
pip install tensorflow-cpu==2.15.0
```

#### Problema: MediaPipe non si avvia o crash
**Causa**: Missing Visual C++ Redistributable (Windows)

**Soluzione**:
1. Scarica Visual C++ Redistributable: https://aka.ms/vs/17/release/vc_redist.x64.exe
2. Installa e riavvia
3. Riprova `python app.py`

#### Problema: `OSError: [WinError 193] %1 is not a valid Win32 application`
**Causa**: Mismatch tra Python 32-bit e librerie 64-bit

**Soluzione**:
```bash
# Verifica architettura Python
python -c "import struct; print(struct.calcsize('P') * 8)"
# Output dovrebbe essere: 64

# Se è 32, disinstalla e installa Python 64-bit da python.org
```

#### Problema: `Address already in use` su porta 5000
**Causa**: Altra applicazione usa la porta o Flask già in esecuzione

**Soluzione**:
```bash
# Windows - trova e termina processo
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Oppure cambia porta in app.py:
app.run(port=5001)  # Usa porta diversa
```

#### Problema: Video non viene processato (restituisce keypoint None)
**Causa**: Video corrotto, codec non supportato, o nessuna persona visibile

**Soluzione**:
1. Converti video in MP4 H.264:
```bash
ffmpeg -i input.mov -c:v libx264 -c:a aac output.mp4
```
2. Verifica che il video mostri una persona intera, frontale
3. Controlla illuminazione (MediaPipe richiede buona visibilità)

#### Problema: Training molto lento
**Causa**: CPU training senza GPU

**Soluzione**:
- **Ridurre epochs**: In `config.py`, cambia `EPOCHS = 50` → `EPOCHS = 20`
- **Ridurre video resolution**: Preprocessa video a 720p invece di 1080p
- **GPU acceleration**: Installa tensorflow-gpu (richiede CUDA)

### 🎨 Frontend Issues

#### Problema: `command not found: npm`
**Causa**: Node.js non installato

**Soluzione**:
1. Scarica Node.js LTS da https://nodejs.org
2. Installa (include npm)
3. Verifica: `node --version && npm --version`

#### Problema: `Cannot find module '@sveltejs/kit'`
**Causa**: Dipendenze non installate

**Soluzione**:
```bash
cd frontend
rm -rf node_modules package-lock.json  # Pulisci cache
npm install
```

#### Problema: Vite non si avvia o crash
**Causa**: Conflitto versioni Node.js

**Soluzione**:
```bash
# Verifica versione Node.js
node --version
# Deve essere >= 16

# Se inferiore, aggiorna Node.js
# Se superiore e problemi, usa nvm per downgrade a LTS
```

#### Problema: `Error: ENOSPC: System limit for number of file watchers reached`
**Causa**: Linux file watcher limit (non su Windows)

**Soluzione** (Linux):
```bash
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

#### Problema: Pagina bianca dopo npm run dev
**Causa**: Errore JavaScript o rotte non configurate

**Soluzione**:
1. Apri console browser (F12)
2. Controlla errori
3. Verifica che `src/routes/+page.svelte` esista
4. Riavvia dev server

### 🌐 Comunicazione Backend-Frontend

#### Problema: `CORS policy: No 'Access-Control-Allow-Origin' header`
**Causa**: Backend non permette richieste dal frontend

**Soluzione**:
Verifica che in `backend/app.py` ci sia:
```python
from flask_cors import CORS
CORS(app)
```

Se già presente, prova:
```python
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
```

#### Problema: `Failed to fetch` o `Network Error`
**Causa**: Backend non in esecuzione o URL errato

**Soluzione**:
1. Verifica backend attivo: Apri http://localhost:5000/api/health
2. Controlla console backend per errori
3. Verifica URL nei componenti Svelte:
```javascript
const response = await fetch('http://localhost:5000/api/...', ...);
```

#### Problema: Upload file fallisce silenziosamente
**Causa**: File troppo grande o formato non supportato

**Soluzione**:
1. Verifica dimensione file < 500MB
2. Verifica estensione: .mp4, .avi, .mov, .mkv, .webm
3. Controlla console browser per errori
4. Aumenta limite in `config.py`:
```python
MAX_CONTENT_LENGTH = 1000 * 1024 * 1024  # 1GB
```

### 📹 Video Processing

#### Problema: Anomaly score sempre molto alto
**Causa**: Baseline non creata o modello non addestrato bene

**Soluzione**:
1. Verifica che `backend/models/baseline_model.h5` esista
2. Ricrea baseline con video di migliore qualità
3. Usa video simili (stessa camera, angolazione, illuminazione)

#### Problema: Anomaly score sempre ~0
**Causa**: Modello overfit o stesso video usato per baseline e test

**Soluzione**:
1. Non usare gli stessi video per baseline e test
2. Aumenta validation_split in `lstm_autoencoder.py`
3. Riduci epochs per evitare overfitting

#### Problema: MediaPipe non rileva pose
**Causa**: Angolazione camera, illuminazione, risoluzione

**Soluzione**:
1. **Camera**: Frontale o laterale (evita angoli strani)
2. **Distanza**: Persona intera visibile nel frame
3. **Illuminazione**: Buona luce, evita controluce
4. **Vestiti**: Evita vestiti molto larghi
5. **Risoluzione**: Minimo 480p, consigliato 720p+

#### Problema: Alcuni frame hanno keypoint a 0
**Causa**: MediaPipe perde tracking temporaneamente

**Soluzione**:
È normale. Il sistema lo gestisce. Se troppi frame:
1. Migliora qualità video
2. Abbassa velocità movimento
3. Aumenta FPS video (30+ fps)

### 💾 File System

#### Problema: `PermissionError: [Errno 13] Permission denied`
**Causa**: Mancano permessi scrittura in cartelle

**Soluzione**:
```bash
# Windows - esegui come amministratore
# O cambia permessi cartella:
icacls "backend\uploads" /grant Users:F
icacls "backend\models" /grant Users:F
```

#### Problema: Cartelle uploads/models non esistono
**Causa**: `Config.init_app()` non chiamato

**Soluzione**:
Verifica in `app.py`:
```python
Config.init_app()  # Deve essere chiamato all'avvio
```

O crea manualmente:
```bash
mkdir backend\uploads
mkdir backend\models
```

### 🚀 Performance

#### Problema: Processing troppo lento
**Ottimizzazioni**:

1. **Ridurre risoluzione video**:
```python
# In keypoint_extractor.py, prima di mp.process():
frame = cv2.resize(frame, (640, 480))
```

2. **Skip frames**:
```python
# Processa solo 1 frame ogni 2
if frame_count % 2 == 0:
    results = self.pose.process(frame_rgb)
```

3. **Ridurre LSTM size**:
```python
# In config.py
LSTM_UNITS = 32  # invece di 64
LATENT_DIM = 16  # invece di 32
```

### 🧪 Testing e Debug

#### Debug Backend
```python
# Aggiungi logging dettagliato in app.py
import logging
logging.basicConfig(level=logging.DEBUG)

# O print statements
print(f"Keypoints shape: {keypoints.shape}")
print(f"Angles shape: {angles.shape}")
```

#### Debug Frontend
```javascript
// In componenti Svelte
console.log('File selezionato:', file);
console.log('Response:', data);

// Usa browser DevTools (F12) → Console tab
```

#### Test Backend API isolato
```bash
# Test con curl
curl -X POST http://localhost:5000/api/health

# Test upload (PowerShell)
$file = Get-Item "test_video.mp4"
$form = @{ video = $file }
Invoke-WebRequest -Uri http://localhost:5000/api/detect_anomaly -Method POST -Form $form
```

### 📦 Dipendenze

#### Aggiornare tutte le dipendenze
```bash
# Backend
cd backend
pip install --upgrade -r requirements.txt

# Frontend
cd frontend
npm update
```

#### Versioni specifiche problematiche
```bash
# Se tensorflow 2.15 ha problemi, prova:
pip install tensorflow==2.14.0

# Se opencv ha problemi, prova:
pip install opencv-python-headless==4.8.1.78
```

## 🆘 Ulteriore Supporto

### Logs da Controllare
1. **Backend**: Output console dove hai eseguito `python app.py`
2. **Frontend**: Output console dove hai eseguito `npm run dev`
3. **Browser**: DevTools Console (F12)

### Informazioni da Fornire per Debug
- Sistema operativo e versione
- Python version: `python --version`
- Node version: `node --version`
- Output completo errore
- Steps per riprodurre il problema
- Screenshot (se UI issue)

### Checklist Debug Rapido
- [ ] Backend è in esecuzione? (http://localhost:5000)
- [ ] Frontend è in esecuzione? (http://localhost:3000)
- [ ] Console browser ha errori?
- [ ] Console backend ha errori?
- [ ] Video è formato valido e non corrotto?
- [ ] Baseline è stata creata? (models/baseline_model.h5 esiste?)

---

**Se il problema persiste dopo queste soluzioni, apri una issue con log completi!**

