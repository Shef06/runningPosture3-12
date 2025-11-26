# Running Analyzer - Esempi Test API

## 🚀 Test Endpoint

### 1. Health Check

```bash
curl http://localhost:5000/api/health
```

**Risposta Attesa:**
```json
{
  "status": "success",
  "message": "Running Analyzer Server attivo"
}
```

---

### 2. Creazione Baseline

**Request (cURL):**
```bash
curl -X POST http://localhost:5000/api/create_baseline \
  -F "videos=@video1.mp4" \
  -F "videos=@video2.mp4" \
  -F "videos=@video3.mp4" \
  -F "videos=@video4.mp4" \
  -F "videos=@video5.mp4" \
  -F "speed=10.0" \
  -F "fps=30"
```

**Request (Python):**
```python
import requests

files = [
    ('videos', open('video1.mp4', 'rb')),
    ('videos', open('video2.mp4', 'rb')),
    ('videos', open('video3.mp4', 'rb')),
    ('videos', open('video4.mp4', 'rb')),
    ('videos', open('video5.mp4', 'rb')),
]

data = {
    'speed': '10.0',  # km/h
    'fps': '30'
}

response = requests.post(
    'http://localhost:5000/api/create_baseline',
    files=files,
    data=data
)

print(response.json())
```

**Risposta Attesa:**
```json
{
  "status": "success",
  "message": "Baseline creata con successo",
  "baselineCreated": true,
  "baselineRanges": {
    "leftKneeValgus": {
      "min": 2.34,
      "max": 15.67,
      "mean": 8.45,
      "std": 3.21,
      "unit": "°"
    },
    "rightKneeValgus": {
      "min": 2.11,
      "max": 14.89,
      "mean": 7.89,
      "std": 2.98,
      "unit": "°"
    },
    "pelvicDrop": {
      "min": 0.12,
      "max": 5.67,
      "mean": 2.34,
      "std": 1.12,
      "unit": "°"
    },
    "cadence": {
      "min": 168,
      "max": 186,
      "mean": 178.2,
      "std": 4.5,
      "unit": "spm"
    }
  }
}
```

**File Creato:**
`backend/models/baseline.json`:
```json
{
  "left_knee_valgus": {
    "mean": 8.45,
    "std": 3.21,
    "min": 2.34,
    "max": 15.67
  },
  "right_knee_valgus": {
    "mean": 7.89,
    "std": 2.98,
    "min": 2.11,
    "max": 14.89
  },
  "pelvic_drop": {
    "mean": 2.34,
    "std": 1.12,
    "min": 0.12,
    "max": 5.67
  },
  "cadence": {
    "mean": 178.2,
    "std": 4.5,
    "min": 168.0,
    "max": 186.0
  },
  "speed_kmh": 10.0,
  "fps": 30.0,
  "n_videos": 5,
  "total_frames": 2250,
  "created_at": "2025-11-24T15:30:45.123456"
}
```

---

### 3. Analisi Video

**Request (cURL):**
```bash
curl -X POST http://localhost:5000/api/detect_anomaly \
  -F "video=@test_run.mp4" \
  -F "speed=10.0" \
  -F "fps=30"
```

**Request (Python):**
```python
import requests

files = {
    'video': open('test_run.mp4', 'rb')
}

data = {
    'speed': '10.0',
    'fps': '30'
}

response = requests.post(
    'http://localhost:5000/api/detect_anomaly',
    files=files,
    data=data
)

result = response.json()
print(f"Stato: {result['anomaly_level']}")
print(f"Z-Score Max: {result['anomaly_score']}")

for metric, values in result['metrics'].items():
    print(f"\n{metric}:")
    print(f"  Valore: {values['value']}")
    print(f"  Z-Score: {values['z_score']:.2f}")
    print(f"  Livello: {values['level']}")
```

**Risposta Esempio (Ottimale):**
```json
{
  "status": "success",
  "anomaly_level": "Ottimale",
  "anomaly_color": "#10b981",
  "anomaly_score": 0.85,
  "metrics": {
    "left_knee_valgus": {
      "value": 11.18,
      "z_score": 0.85,
      "level": "Ottimale",
      "color": "#10b981",
      "baseline_mean": 8.45,
      "baseline_std": 3.21,
      "unit": "°"
    },
    "right_knee_valgus": {
      "value": 8.23,
      "z_score": 0.11,
      "level": "Ottimale",
      "color": "#10b981",
      "baseline_mean": 7.89,
      "baseline_std": 2.98,
      "unit": "°"
    },
    "pelvic_drop": {
      "value": 2.72,
      "z_score": 0.34,
      "level": "Ottimale",
      "color": "#10b981",
      "baseline_mean": 2.34,
      "baseline_std": 1.12,
      "unit": "°"
    },
    "cadence": {
      "value": 177.8,
      "z_score": -0.09,
      "level": "Ottimale",
      "color": "#10b981",
      "baseline_mean": 178.2,
      "baseline_std": 4.5,
      "unit": "spm"
    }
  },
  "charts": {
    "timeline": [0, 1, 2, 3, ..., 299],
    "left_knee_valgus": [8.2, 8.5, 9.1, 10.3, ..., 9.7],
    "right_knee_valgus": [7.1, 7.4, 8.2, 8.8, ..., 7.9],
    "pelvic_drop": [2.1, 2.3, 2.5, 2.8, ..., 2.4]
  },
  "video_info": {
    "n_frames": 300,
    "frames_with_pose": 297,
    "fps": 30.0,
    "duration": 10.0
  }
}
```

**Risposta Esempio (Attenzione):**
```json
{
  "status": "success",
  "anomaly_level": "Attenzione",
  "anomaly_color": "#f59e0b",
  "anomaly_score": 1.42,
  "metrics": {
    "left_knee_valgus": {
      "value": 11.18,
      "z_score": 0.85,
      "level": "Ottimale",
      "color": "#10b981"
    },
    "right_knee_valgus": {
      "value": 12.12,
      "z_score": 1.42,
      "level": "Attenzione",
      "color": "#f59e0b"
    },
    "pelvic_drop": {
      "value": 2.72,
      "z_score": 0.34,
      "level": "Ottimale",
      "color": "#10b981"
    },
    "cadence": {
      "value": 177.8,
      "z_score": -0.09,
      "level": "Ottimale",
      "color": "#10b981"
    }
  },
  ...
}
```

**Risposta Esempio (Critico):**
```json
{
  "status": "success",
  "anomaly_level": "Critico",
  "anomaly_color": "#ef4444",
  "anomaly_score": 2.34,
  "metrics": {
    "left_knee_valgus": {
      "value": 15.96,
      "z_score": 2.34,
      "level": "Critico",
      "color": "#ef4444"
    },
    ...
  }
}
```

---

## 🔴 Errori Comuni

### Errore: Baseline non trovata

**Request:**
```bash
curl -X POST http://localhost:5000/api/detect_anomaly \
  -F "video=@test.mp4" \
  -F "speed=10.0" \
  -F "fps=30"
```

**Risposta:**
```json
{
  "status": "error",
  "message": "Baseline non trovata. Crea prima una baseline con 5 video."
}
```

**Soluzione:** Creare prima la baseline con 5 video.

---

### Errore: Velocità non corrisponde

**Request:**
```bash
# Baseline creata a 10.0 km/h
curl -X POST http://localhost:5000/api/detect_anomaly \
  -F "video=@test.mp4" \
  -F "speed=12.0" \
  -F "fps=30"
```

**Risposta:**
```json
{
  "status": "error",
  "message": "Velocità non corrisponde alla baseline. Baseline: 10.0 km/h, Fornito: 12.0 km/h."
}
```

**Soluzione:** Usare la stessa velocità della baseline (±0.5 km/h).

---

### Errore: Numero video sbagliato

**Request:**
```bash
curl -X POST http://localhost:5000/api/create_baseline \
  -F "videos=@video1.mp4" \
  -F "videos=@video2.mp4" \
  -F "speed=10.0" \
  -F "fps=30"
```

**Risposta:**
```json
{
  "status": "error",
  "message": "Sono richiesti esattamente 5 video, ricevuti 2"
}
```

**Soluzione:** Fornire esattamente 5 video per la baseline.

---

## 🧪 Script Python Completo

```python
#!/usr/bin/env python3
"""
Test completo API Running Analyzer
"""
import requests
import json
from pathlib import Path

BASE_URL = 'http://localhost:5000'

def test_health():
    """Test endpoint health"""
    print("🏥 Test Health Check...")
    response = requests.get(f'{BASE_URL}/api/health')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def create_baseline(video_dir, speed=10.0, fps=30):
    """Crea baseline da 5 video"""
    print("📊 Creazione Baseline...")
    
    video_files = list(Path(video_dir).glob('*.mp4'))[:5]
    
    if len(video_files) < 5:
        print(f"❌ Trovati solo {len(video_files)} video, ne servono 5")
        return None
    
    files = [
        ('videos', (f.name, open(f, 'rb'), 'video/mp4'))
        for f in video_files
    ]
    
    data = {
        'speed': str(speed),
        'fps': str(fps)
    }
    
    print(f"  Video: {[f.name for f in video_files]}")
    print(f"  Velocità: {speed} km/h")
    print(f"  FPS: {fps}")
    
    response = requests.post(
        f'{BASE_URL}/api/create_baseline',
        files=files,
        data=data
    )
    
    # Chiudi file
    for _, (_, file, _) in files:
        file.close()
    
    result = response.json()
    
    if response.status_code == 200:
        print("✅ Baseline creata!")
        print(f"  Range:")
        for metric, values in result.get('baselineRanges', {}).items():
            print(f"    {metric}: {values['mean']:.2f} ± {values['std']:.2f}")
    else:
        print(f"❌ Errore: {result.get('message')}")
    
    print()
    return result

def analyze_video(video_path, speed=10.0, fps=30):
    """Analizza un singolo video"""
    print("🔍 Analisi Video...")
    
    files = {
        'video': (Path(video_path).name, open(video_path, 'rb'), 'video/mp4')
    }
    
    data = {
        'speed': str(speed),
        'fps': str(fps)
    }
    
    print(f"  Video: {Path(video_path).name}")
    print(f"  Velocità: {speed} km/h")
    print(f"  FPS: {fps}")
    
    response = requests.post(
        f'{BASE_URL}/api/detect_anomaly',
        files=files,
        data=data
    )
    
    files['video'][1].close()
    
    result = response.json()
    
    if response.status_code == 200:
        print(f"✅ Analisi completata!")
        print(f"  Stato: {result['anomaly_level']}")
        print(f"  Z-Score Max: {result['anomaly_score']:.2f}")
        print(f"  Metriche:")
        for metric, values in result['metrics'].items():
            emoji = '✅' if values['level'] == 'Ottimale' else '⚠️' if values['level'] == 'Attenzione' else '🚨'
            print(f"    {emoji} {metric}: {values['value']:.2f} (Z={values['z_score']:.2f}, {values['level']})")
    else:
        print(f"❌ Errore: {result.get('message')}")
    
    print()
    return result

if __name__ == '__main__':
    # Test health
    test_health()
    
    # Crea baseline
    baseline_dir = './baseline_videos'  # Cartella con 5 video
    create_baseline(baseline_dir, speed=10.0, fps=30)
    
    # Analizza video test
    test_video = './test_video.mp4'
    analyze_video(test_video, speed=10.0, fps=30)
```

**Esecuzione:**
```bash
python test_api.py
```

---

## 📊 Interpretazione Z-Score

| Z-Score | Significato | Probabilità | Livello |
|---------|-------------|-------------|---------|
| 0.00 | Perfettamente sulla media | - | Ottimale ✅ |
| ±0.50 | Vicino alla media | ~69% popolazione | Ottimale ✅ |
| ±1.00 | 1 deviazione standard | ~68% popolazione | Ottimale ✅ |
| ±1.50 | Tra 1 e 2 deviazioni | ~86-95% | Attenzione ⚠️ |
| ±2.00 | 2 deviazioni standard | ~95% popolazione | Attenzione ⚠️ |
| ±2.50 | Oltre 2 deviazioni | ~99% popolazione | Critico 🚨 |
| ±3.00 | 3 deviazioni standard | ~99.7% popolazione | Critico 🚨 |

**Esempio:**
- Baseline: Valgismo = 8.45° ± 3.21°
- Tuo valore: 11.18°
- Z-Score: (11.18 - 8.45) / 3.21 = **0.85**
- Interpretazione: ✅ **Ottimale** (entro 1σ)

---

## 🎯 Best Practices

1. **Video Baseline:**
   - Stessa velocità tapis roulant
   - Stessi FPS
   - Stessa vista (posteriore)
   - Durata minima 10 secondi ciascuno

2. **Video Analisi:**
   - Stessa velocità della baseline (±0.5 km/h)
   - Stessi FPS
   - Minimo 5 secondi

3. **Qualità Video:**
   - Soggetto centrato
   - Buona illuminazione
   - Nessuna occlusione
   - Camera stabile

---

**Pronto per il test! 🚀**

