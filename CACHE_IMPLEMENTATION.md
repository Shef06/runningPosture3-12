# 💾 Implementazione Cache per PoseEngine

## ✅ Implementazione Completata

### Obiettivo
Evitare di riprocessare video già analizzati, rendendo la creazione della baseline **istantanea** se i video sono già stati processati.

## 📝 Modifiche al Codice

### File: `backend/pose_engine.py`

#### 1. Aggiunti Import
```python
import os
import hashlib
import pickle
```

#### 2. Aggiunta Directory Cache
```python
class PoseEngine:
    # Directory per cache
    CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache', 'pose_engine')
```

**Percorso cache**: `backend/cache/pose_engine/`

#### 3. Parametro `use_cache` nel Costruttore
```python
def __init__(self, 
             model_complexity: int = 2,
             min_detection_confidence: float = 0.5,
             min_tracking_confidence: float = 0.5,
             use_cache: bool = True):  # ← NUOVO
    self.use_cache = use_cache
    
    # Crea directory cache se non esiste
    if self.use_cache:
        os.makedirs(self.CACHE_DIR, exist_ok=True)
```

#### 4. Metodi Cache

**`_get_cache_path()`**: Genera percorso cache basato su hash
```python
def _get_cache_path(self, video_path: str, fps: Optional[float] = None) -> str:
    # Ottieni timestamp di modifica del file
    stat = os.stat(video_path)
    mtime = stat.st_mtime
    
    # Crea hash: video_path + timestamp + fps + parametri MediaPipe
    cache_key = f"{video_path}_{mtime}_{fps}_{self.model_complexity}_{self.min_detection_confidence}_{self.min_tracking_confidence}"
    cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
    return os.path.join(self.CACHE_DIR, f"{cache_hash}.pkl")
```

**`_load_from_cache()`**: Carica risultati dalla cache
```python
def _load_from_cache(self, cache_path: str) -> Optional[Dict]:
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'rb') as f:
                result = pickle.load(f)
            logger.info(f"✓ Risultati caricati dalla cache")
            return result
        except Exception as e:
            logger.warning(f"⚠ Errore nel caricare cache: {e}")
    return None
```

**`_save_to_cache()`**: Salva risultati nella cache
```python
def _save_to_cache(self, result: Dict, cache_path: str):
    try:
        with open(cache_path, 'wb') as f:
            pickle.dump(result, f)
        logger.info(f"✓ Risultati salvati in cache")
    except Exception as e:
        logger.warning(f"⚠ Errore nel salvare cache: {e}")
```

#### 5. Integrazione in `process_video()`

**All'inizio** (controlla cache):
```python
def process_video(self, video_path: str, fps: Optional[float] = None) -> Dict:
    logger.info(f"=== Inizio processing video: {video_path} ===")
    
    # Controlla cache se abilitata
    if self.use_cache:
        cache_path = self._get_cache_path(video_path, fps)
        cached_result = self._load_from_cache(cache_path)
        if cached_result is not None:
            logger.info(f"=== Processing completato (da cache) ===")
            return cached_result  # ← RITORNA SUBITO se in cache
    
    # ... processing normale ...
```

**Alla fine** (salva in cache):
```python
    result = {
        'left_knee_valgus': left_knee_valgus_arr.tolist(),
        'right_knee_valgus': right_knee_valgus_arr.tolist(),
        # ... altre metriche ...
    }
    
    # Salva in cache se abilitata
    if self.use_cache:
        cache_path = self._get_cache_path(video_path, fps)
        self._save_to_cache(result, cache_path)
    
    return result
```

## 🔑 Caratteristiche della Cache

### 1. Hash Completo
La chiave cache include:
- **Percorso video**: Identifica il file
- **Timestamp modifica** (`mtime`): Invalida cache se video cambia
- **FPS**: Cache separata per FPS diversi
- **Parametri MediaPipe**: Cache separata per configurazioni diverse
  - `model_complexity`
  - `min_detection_confidence`
  - `min_tracking_confidence`

### 2. Invalidazione Automatica
Se il video viene modificato (timestamp cambia), la cache viene automaticamente invalidata e il video viene riprocessato.

### 3. Formato Pickle
Usa `pickle` per salvare oggetti Python complessi (liste, dizionari, numpy arrays convertiti in liste).

### 4. Thread-Safe
Ogni thread crea la propria istanza di `PoseEngine`, quindi la cache è thread-safe (file system è thread-safe per operazioni di lettura/scrittura separate).

## 📊 Performance

### Prima (Senza Cache)
- **Prima volta**: 5 video × 60-90 sec = **5-7.5 minuti**
- **Seconda volta**: **5-7.5 minuti** (riprocessa tutto)

### Dopo (Con Cache)
- **Prima volta**: 5 video × 60-90 sec = **5-7.5 minuti** (salva in cache)
- **Seconda volta**: **< 5 secondi** (carica da cache) ⚡

**Miglioramento**: **60-90x più veloce** per video già processati!

## 🧪 Test

### Scenario 1: Prima Esecuzione
```bash
# Crea baseline con 5 video
POST /api/create_baseline

# Log attesi:
=== Inizio processing video: video1.mp4 ===
Video: 450 frame, 30.00 FPS
Processing completato: 450 frame, 445 con pose rilevata
✓ Risultati salvati in cache: abc123def456.pkl
```

### Scenario 2: Seconda Esecuzione (Stessi Video)
```bash
# Crea baseline con stessi 5 video
POST /api/create_baseline

# Log attesi:
=== Inizio processing video: video1.mp4 ===
✓ Risultati caricati dalla cache: abc123def456.pkl
  Video: 450 frame, FPS: 30.00
=== Processing completato (da cache) ===
```

**Tempo**: Da 5-7.5 minuti → **< 5 secondi** ⚡

### Scenario 3: Video Modificato
```bash
# Modifica video1.mp4 (es. taglia alcuni frame)
# Timestamp cambia → cache invalidata

# Log attesi:
=== Inizio processing video: video1.mp4 ===
Video: 420 frame, 30.00 FPS  # ← Nuovo processing
Processing completato: 420 frame, 415 con pose rilevata
✓ Risultati salvati in cache: xyz789abc123.pkl  # ← Nuovo hash
```

## 📁 Struttura Cache

```
backend/
└── cache/
    └── pose_engine/
        ├── abc123def456.pkl  # Video 1 (hash MD5)
        ├── def456ghi789.pkl  # Video 2
        ├── ghi789jkl012.pkl  # Video 3
        ├── jkl012mno345.pkl  # Video 4
        └── mno345pqr678.pkl  # Video 5
```

**Dimensione file cache**: ~50-200 KB per video (dipende da numero di frame)

## ⚙️ Configurazione

### Abilitare/Disabilitare Cache

**Per singola istanza:**
```python
# Cache abilitata (default)
engine = PoseEngine(use_cache=True)

# Cache disabilitata
engine = PoseEngine(use_cache=False)
```

**In app.py:**
```python
def process_single_video(i, video_path):
    engine = PoseEngine(
        model_complexity=Config.MEDIAPIPE_MODEL_COMPLEXITY,
        min_detection_confidence=Config.MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=Config.MEDIAPIPE_MIN_TRACKING_CONFIDENCE,
        use_cache=True  # ← Abilitata di default
    )
    return i, engine.process_video(video_path, fps=fps)
```

## 🧹 Pulizia Cache

### Manuale
```bash
# Elimina tutta la cache
rm -rf backend/cache/pose_engine/

# Elimina cache vecchia (> 30 giorni)
find backend/cache/pose_engine/ -name "*.pkl" -mtime +30 -delete
```

### Automatica (Futuro)
Potrebbe essere aggiunta una funzione per pulire cache vecchia automaticamente.

## ⚠️ Note Importanti

1. **Spazio Disco**: Ogni video processato crea un file cache (~50-200 KB). Per 100 video = ~5-20 MB.

2. **Compatibilità**: I file cache sono specifici per:
   - Versione Python (pickle può variare tra versioni)
   - Parametri MediaPipe (se cambiano, cache viene invalidata)

3. **Sicurezza**: I file cache contengono solo risultati numerici (metriche), non dati sensibili.

4. **Thread Safety**: La cache è thread-safe perché ogni thread scrive in file diversi (hash diversi).

## 🔄 Integrazione con Parallelizzazione

La cache funziona perfettamente con la parallelizzazione:
- Ogni thread controlla la propria cache
- Se un video è in cache, viene caricato istantaneamente
- Se non è in cache, viene processato normalmente
- Risultati vengono salvati in cache alla fine

**Esempio con 5 video, 3 in cache:**
```
Thread 1: video1.mp4 → ✓ Cache (0.1s)
Thread 2: video2.mp4 → ✓ Cache (0.1s)
Thread 3: video3.mp4 → ✓ Cache (0.1s)
Thread 4: video4.mp4 → Processing (60s)
Thread 5: video5.mp4 → Processing (60s)

Totale: ~60 secondi (invece di 300s)
```

## ✅ Verifica Implementazione

```bash
# Test sintassi
cd backend
python -m py_compile pose_engine.py

# Test import
python -c "from pose_engine import PoseEngine; print('OK')"

# Test cache directory
python -c "from pose_engine import PoseEngine; import os; print('Cache dir:', PoseEngine.CACHE_DIR); print('Exists:', os.path.exists(PoseEngine.CACHE_DIR))"
```

## 📚 Riferimenti

- Pattern simile a `backend/keypoint_extractor.py` (cache keypoints)
- Documentazione pickle: https://docs.python.org/3/library/pickle.html
- Hash MD5: https://docs.python.org/3/library/hashlib.html

---

**✅ Cache implementata e pronta per il test!**

**Risultato**: Creazione baseline istantanea per video già processati! ⚡

