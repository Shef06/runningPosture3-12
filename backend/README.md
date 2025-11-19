# Backend - Analisi Biomeccanica della Corsa

Backend Flask per l'applicazione di analisi della corsa e rilevamento anomalie.

## Installazione

1. Crea un ambiente virtuale:
```bash
python -m venv venv
```

2. Attiva l'ambiente virtuale:
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

3. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

## Avvio del Server

```bash
python app.py
```

Il server sarà disponibile su `http://localhost:5000`

## API Endpoints

### POST /api/create_baseline
Crea la baseline biomeccanica da 5 video di riferimento.

**Body:** FormData con 5 file video (chiave: `videos`)

**Response:**
```json
{
  "status": "success",
  "message": "Baseline creata e modello addestrato con successo",
  "details": {
    "n_frames_total": 1500,
    "n_features": 4,
    "final_loss": 0.0023,
    "final_val_loss": 0.0025
  }
}
```

### POST /api/detect_anomaly
Rileva anomalie in un nuovo video rispetto alla baseline.

**Body:** FormData con 1 file video (chiave: `video`)

**Response:**
```json
{
  "status": "success",
  "anomaly_score": 0.0123,
  "anomaly_level": "Buono",
  "anomaly_color": "lightgreen",
  "details": {
    "n_frames": 300,
    "n_features": 4
  }
}
```

## Struttura

- `app.py` - Server Flask principale
- `config.py` - Configurazione dell'applicazione
- `keypoint_extractor.py` - Estrazione keypoint 3D con MediaPipe
- `feature_engineering.py` - Calcolo angoli biomeccanici
- `lstm_autoencoder.py` - Modello LSTM Autoencoder per anomalie

