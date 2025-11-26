# Running Analyzer - Guida Installazione

## ⚠️ Nota Importante: MediaPipe e TensorFlow

MediaPipe versione 0.10.8 ha **dipendenze interne a TensorFlow** anche se non viene usato direttamente nel nostro codice. Questo è un problema noto della libreria.

**Soluzione:** Mantenere TensorFlow nelle dipendenze ma **non usarlo** nel nostro codice.

## 📦 Installazione

### Opzione 1: Ambiente Esistente (Recommended)

Se hai già TensorFlow installato, aggiungi solo scipy:

```bash
cd backend
pip install scipy==1.11.4
```

### Opzione 2: Nuovo Ambiente Virtuale

```bash
# Crea ambiente virtuale
python -m venv venv

# Attiva (Windows)
venv\Scripts\activate

# Attiva (Linux/Mac)
source venv/bin/activate

# Installa dipendenze
cd backend
pip install -r requirements_full.txt
```

### requirements_full.txt

Crea questo file con tutte le dipendenze:

```
flask==3.0.0
flask-cors==4.0.0
scipy==1.11.4
opencv-python==4.8.1.78
mediapipe==0.10.8
numpy==1.24.3
werkzeug==3.0.1
tensorflow==2.15.0
```

**Nota:** TensorFlow è necessario solo come dipendenza di MediaPipe, non viene importato nel nostro codice.

## ✅ Verifica Installazione

```bash
cd backend
python -c "import scipy; print('✓ SciPy:', scipy.__version__)"
python -c "import mediapipe; print('✓ MediaPipe:', mediapipe.__version__)"
python -c "import cv2; print('✓ OpenCV:', cv2.__version__)"
```

## 🚀 Avvio Applicazione

```bash
cd backend
python app.py
```

**Output Atteso:**
```
============================================================
  🏃 RUNNING ANALYZER - Backend Server
  Approccio: Geometrico/Statistico (No Deep Learning)
============================================================
```

## 📊 Differenza Implementativa

### Vecchio Approccio (LSTM)
```python
from lstm_autoencoder import LSTMAutoencoder  # ❌ Usa TensorFlow
autoencoder = LSTMAutoencoder()
autoencoder.train(features)  # Training con rete neurale
score = autoencoder.calculate_reconstruction_error(test)
```

### Nuovo Approccio (Geometrico)
```python
from pose_engine import PoseEngine  # ✅ Solo numpy/scipy
engine = PoseEngine()
baseline = engine.create_baseline_stats(videos)  # Statistiche μ, σ
z_scores = engine.calculate_z_scores(video, baseline)  # Z-Score
```

**Vantaggi:**
- ✅ No training (5-10 sec vs 2-3 min)
- ✅ Deterministico e interpretabile
- ✅ Leggero (logica in ~500 righe vs modello 50MB)
- ⚠️ MediaPipe richiede ancora TensorFlow come dipendenza (non usata)

## 🔧 Troubleshooting

### Errore: ml_dtypes AttributeError

Questo è un problema di compatibilità tra versioni. Soluzioni:

**1. Aggiorna ml_dtypes:**
```bash
pip install --upgrade ml_dtypes
```

**2. Usa versioni specifiche:**
```bash
pip install ml_dtypes==0.2.0
```

**3. Reinstalla TensorFlow:**
```bash
pip uninstall tensorflow
pip install tensorflow==2.15.0
```

### Errore: CUDA/GPU

Se non hai GPU, TensorFlow usa CPU automaticamente (OK per MediaPipe).

### Lentezza Processing Video

MediaPipe usa CPU per inferenza Pose. Per velocizzare:
- Riduci `model_complexity` a 1 o 0 in `config.py`
- Usa video a risoluzione inferiore
- FPS più bassi (es. 24-30 invece di 60)

## 📁 Struttura Codice

```
backend/
├── pose_engine.py           # ✅ NUOVO: Logica geometrica (no TF)
├── app.py                   # ✅ NUOVO: Endpoint statistici (no TF)
├── app_old_lstm.py          # 📦 BACKUP: Vecchio codice LSTM
├── lstm_autoencoder.py      # ❌ DEPRECATO (usa TF)
├── keypoint_extractor.py    # ✅ OK: MediaPipe (dipende da TF)
├── config.py                # ✅ OK
└── requirements.txt         # ✅ AGGIORNATO: scipy invece di TF
```

## 🎯 File da NON Modificare

Questi moduli esistenti **rimangono invariati** e sono compatibili:
- `keypoint_extractor.py` (usa MediaPipe)
- `config.py`
- `gait_event_detection.py` (opzionale)
- `feature_engineering.py` (opzionale)

## 🚫 File Deprecati (Non Usati)

Questi moduli **non vengono più importati** nel nuovo app.py:
- `lstm_autoencoder.py`
- `statistics.py` (sostituito da logica in pose_engine)

## ✨ Test Rapido

```bash
# Terminal 1: Backend
cd backend
python app.py

# Terminal 2: Test
curl http://localhost:5000/api/health
```

**Risposta attesa:**
```json
{
  "status": "success",
  "message": "Running Analyzer Server attivo"
}
```

## 📚 Next Steps

Vedi `GEOMETRIC_APPROACH_README.md` per:
- Test creazione baseline
- Test analisi video
- Interpretazione Z-Scores
- Troubleshooting completo

