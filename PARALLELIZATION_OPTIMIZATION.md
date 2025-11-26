# 🚀 Ottimizzazione: Parallelizzazione Processing Video

## ✅ Implementazione Completata

### Problema Identificato
La creazione della baseline processava i 5 video **sequenzialmente**, causando tempi di attesa molto lunghi:
- **Prima**: 5 video × ~60-90 secondi = **5-7.5 minuti totali**

### Soluzione Implementata
**Parallelizzazione con ThreadPoolExecutor** per processare i 5 video contemporaneamente.

## 📝 Modifiche al Codice

### File: `backend/app.py`

**Prima (Sequenziale):**
```python
# Processa tutti i 5 video
logger.info("Fase 1: Processing video con PoseEngine...")
videos_data = []
for i, video_path in enumerate(video_paths):
    logger.info(f"Processing video {i+1}/5: {os.path.basename(video_path)}")
    video_data = engine.process_video(video_path, fps=fps)
    videos_data.append(video_data)
```

**Dopo (Parallelo):**
```python
# Funzione helper per processare un singolo video (thread-safe)
def process_single_video(i, video_path):
    """Processa un singolo video creando una nuova istanza di PoseEngine (thread-safe)"""
    logger.info(f"Processing video {i+1}/5: {os.path.basename(video_path)}")
    # Crea nuova istanza per ogni thread (MediaPipe non è thread-safe)
    engine = PoseEngine(
        model_complexity=Config.MEDIAPIPE_MODEL_COMPLEXITY,
        min_detection_confidence=Config.MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=Config.MEDIAPIPE_MIN_TRACKING_CONFIDENCE
    )
    return i, engine.process_video(video_path, fps=fps)

# Processa tutti i 5 video in parallelo
logger.info("Fase 1: Processing video con PoseEngine (parallelo)...")
videos_data = [None] * len(video_paths)

with ThreadPoolExecutor(max_workers=5) as executor:
    # Sottometti tutti i task
    future_to_index = {
        executor.submit(process_single_video, i, vp): i 
        for i, vp in enumerate(video_paths)
    }
    
    # Raccogli risultati man mano che completano
    for future in as_completed(future_to_index):
        i = future_to_index[future]
        try:
            idx, video_data = future.result()
            videos_data[idx] = video_data
            logger.info(f"✓ Completato video {idx+1}/5: {os.path.basename(video_paths[idx])}")
        except Exception as e:
            logger.error(f"⚠ Errore nell'elaborazione video {i+1}/5: {e}", exc_info=True)
            raise
```

## 🔑 Punti Chiave

### 1. Thread-Safety di MediaPipe
**Problema**: MediaPipe Pose **NON è thread-safe**. Non si può condividere un'istanza tra thread.

**Soluzione**: Creare una **nuova istanza di PoseEngine** per ogni thread:
```python
def process_single_video(i, video_path):
    # Nuova istanza per ogni thread
    engine = PoseEngine(...)
    return engine.process_video(video_path, fps=fps)
```

### 2. ThreadPoolExecutor
- **max_workers=5**: Processa fino a 5 video contemporaneamente
- **as_completed()**: Raccoglie risultati man mano che completano (non in ordine)
- **future_to_index**: Mantiene traccia dell'ordine originale dei video

### 3. Gestione Errori
- Try/except per ogni video
- Verifica finale che tutti i video siano stati processati
- Log dettagliati per debugging

## 📊 Performance Attese

| Scenario | Prima (Sequenziale) | Dopo (Parallelo) | Miglioramento |
|----------|---------------------|------------------|---------------|
| **5 video × 30 sec** | ~5-7.5 minuti | ~1-1.5 minuti | **~5x più veloce** |
| **5 video × 60 sec** | ~10-15 minuti | ~2-3 minuti | **~5x più veloce** |

**Nota**: Il miglioramento dipende da:
- Numero di core CPU disponibili
- Velocità I/O disco (lettura video)
- Complessità MediaPipe (model_complexity)

## 🧪 Test

### Log Attesi
```
📊 Parametri baseline: Velocità=10.0 km/h, FPS=30.0
Fase 1: Processing video con PoseEngine (parallelo)...
Processing video 1/5: video1.mp4
Processing video 2/5: video2.mp4
Processing video 3/5: video3.mp4
Processing video 4/5: video4.mp4
Processing video 5/5: video5.mp4
✓ Completato video 2/5: video2.mp4
✓ Completato video 1/5: video1.mp4
✓ Completato video 4/5: video4.mp4
✓ Completato video 3/5: video3.mp4
✓ Completato video 5/5: video5.mp4
Fase 2: Creazione statistiche baseline...
```

**Nota**: I video completano in ordine diverso (quello che finisce prima viene loggato prima).

## ⚠️ Limitazioni

1. **CPU-bound**: Se la CPU ha meno di 5 core, il miglioramento sarà minore
2. **I/O-bound**: Se i video sono su disco lento, il miglioramento sarà limitato
3. **Memoria**: Ogni thread usa memoria per MediaPipe (~100-200MB per thread)

## 🔄 Prossime Ottimizzazioni Possibili

1. **Ridurre model_complexity a 0** (2-3x più veloce per video)
2. **Downsampling frame** (processare 1 frame ogni 2)
3. **Cache dei risultati** (evitare riprocessare stessi video)

## ✅ Verifica Implementazione

```bash
# Test sintassi
cd backend
python -m py_compile app.py

# Test import
python -c "from app import app; print('OK')"
```

## 📚 Riferimenti

- Pattern simile a `backend/keypoint_extractor.py::extract_from_multiple_videos()`
- Documentazione ThreadPoolExecutor: https://docs.python.org/3/library/concurrent.futures.html
- MediaPipe Thread Safety: https://google.github.io/mediapipe/solutions/pose.html

---

**✅ Parallelizzazione implementata e pronta per il test!**

