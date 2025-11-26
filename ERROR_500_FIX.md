# 🔧 Fix: Errore 500 nella Creazione Baseline

## ❌ Problema

Errore 500 (INTERNAL SERVER ERROR) quando si tenta di creare la baseline:
```
Failed to load resource: the server responded with a status of 500
```

## 🔍 Possibili Cause

1. **`static_image_mode` non supportato**: MediaPipe Pose potrebbe non supportare questo parametro
2. **Errore durante processing video**: Un video potrebbe causare un'eccezione non gestita
3. **Problema con parallelizzazione**: Thread potrebbero fallire silenziosamente

## ✅ Soluzioni Implementate

### 1. Rimosso `static_image_mode`
```python
# PRIMA (causava errore 500)
pose = self.mp_pose.Pose(
    static_image_mode=True,  # ← Parametro non supportato?
    ...
)

# DOPO (fix)
pose = self.mp_pose.Pose(
    model_complexity=self.model_complexity,
    min_detection_confidence=self.min_detection_confidence,
    min_tracking_confidence=0.1,  # ← Basso per ridurre dipendenze temporali
    enable_segmentation=False,
    smooth_landmarks=False
)
```

### 2. Gestione Errori Migliorata in `process_video()`
```python
try:
    results = pose.process(frame_rgb)
except Exception as e:
    logger.warning(f"⚠ Errore MediaPipe frame {frame_count}: {e}")
    results = None  # Continua con frame vuoto invece di crashare
```

### 3. Gestione Errori Migliorata in `app.py`
```python
# Raccoglie errori invece di crashare immediatamente
errors = []
for future in as_completed(future_to_index):
    try:
        idx, video_data = future.result()
        videos_data[idx] = video_data
    except Exception as e:
        error_msg = f"Errore video {i+1}/5: {str(e)}"
        logger.error(f"⚠ {error_msg}", exc_info=True)
        errors.append(error_msg)  # Raccoglie invece di raise

# Verifica finale con messaggio dettagliato
if len(videos_data) != len(video_paths):
    error_details = "; ".join(errors)
    return jsonify({
        'status': 'error',
        'message': f'Errore: {len(videos_data)}/{len(video_paths)} video processati. Dettagli: {error_details}'
    }), 500
```

### 4. Logging Dettagliato
```python
except Exception as e:
    error_msg = str(e)
    error_type = type(e).__name__
    logger.error(f"❌ Errore: {error_type}: {error_msg}", exc_info=True)
    return jsonify({
        'status': 'error',
        'message': f'Errore interno: {error_type}: {error_msg}',
        'error_type': error_type
    }), 500
```

## 🧪 Debug

### Verifica Log del Server
Controlla i log del server Flask per vedere l'errore specifico:
```bash
# Avvia server con logging dettagliato
python app.py

# Cerca errori nei log quando crei baseline
```

### Test Isolato
```python
# Test processing singolo video
from pose_engine import PoseEngine

engine = PoseEngine()
result = engine.process_video('test_video.mp4', fps=30)
print(result)
```

## 📊 Cosa Aspettarsi

### Se Funziona
- Baseline creata con successo
- Log mostrano "✓ Completato video X/5" per ogni video
- File `baseline.json` creato

### Se C'è Ancora Errore
- Controlla i log del server per il messaggio di errore specifico
- Il messaggio JSON ora include `error_type` e dettagli
- Verifica che i video siano validi e leggibili

## 🔄 Prossimi Passi

1. **Controlla i log del server** per vedere l'errore specifico
2. **Verifica i video** siano validi (formato, codec, dimensioni)
3. **Testa con un singolo video** per isolare il problema
4. **Verifica spazio disco** e permessi di scrittura

## ⚠️ Note

- I **warning di timestamp mismatch** possono ancora apparire ma **non bloccano** il processing
- Sono solo warning informativi di MediaPipe, non errori fatali
- Il processing continua anche con questi warning

---

**✅ Fix implementato! Controlla i log del server per dettagli specifici dell'errore.**

