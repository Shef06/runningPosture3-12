# 🔧 Fix: MediaPipe Timestamp Mismatch Error

## ❌ Problema

Errore MediaPipe quando si processano video in parallelo:
```
Packet timestamp mismatch on a calculator receiving from stream "image". 
Current minimum expected timestamp is 166398337 but received 166365003.
```

## 🔍 Causa

L'errore si verifica quando `smooth_landmarks=True` perché:
1. **MediaPipe usa tracking temporale** per smooth dei landmark
2. **Richiede timestamp monotonicamente crescenti** per ogni frame
3. **Con parallelizzazione**, ogni thread processa un video diverso ma MediaPipe può confondere i timestamp
4. **OpenCV legge frame** con timestamp che possono non essere perfettamente sequenziali

## ✅ Soluzione Implementata (Aggiornata)

**Usato `static_image_mode=True`** per disabilitare completamente il tracking temporale:

```python
# PRIMA (causava errore)
pose = self.mp_pose.Pose(
    model_complexity=self.model_complexity,
    min_detection_confidence=self.min_detection_confidence,
    min_tracking_confidence=self.min_tracking_confidence,
    enable_segmentation=False,
    smooth_landmarks=True  # ← Causava timestamp mismatch
)

# DOPO (fix robusto)
pose = self.mp_pose.Pose(
    static_image_mode=True,  # ← Disabilita tracking temporale completamente
    model_complexity=self.model_complexity,
    min_detection_confidence=self.min_detection_confidence,
    min_tracking_confidence=self.min_tracking_confidence,
    enable_segmentation=False,
    smooth_landmarks=False
)
```

**Perché `static_image_mode=True`?**
- Ogni frame viene processato **indipendentemente** senza dipendenze temporali
- **Nessun tracking** tra frame → nessun problema di timestamp
- **Perfetto per analisi geometrica** dove non serve il tracking temporale
- **Completamente thread-safe** per parallelizzazione

## 📊 Impatto

### Vantaggi
- ✅ **Risolve errore timestamp mismatch**
- ✅ **Funziona correttamente con parallelizzazione**
- ✅ **Nessun problema con video multipli**

### Svantaggi Minori
- ⚠️ **Nessun tracking temporale** tra frame (ogni frame è indipendente)
- ⚠️ **Landmark non smooth** tra frame (ma non necessario per analisi geometrica)

**Nota**: Per l'analisi biomeccanica geometrica (angoli, distanze), il tracking temporale **NON è necessario**. I calcoli geometrici sono deterministici e calcolati frame-by-frame. Ogni frame viene analizzato indipendentemente, il che è perfetto per la nostra analisi.

## 🔄 Alternative (Non Implementate)

Se in futuro servisse il smoothing, si potrebbero usare:

1. **Smoothing manuale post-processing**:
   ```python
   from scipy.signal import savgol_filter
   smoothed = savgol_filter(series, window_length=5, polyorder=2)
   ```

2. **`static_image_mode=True`** (✅ IMPLEMENTATO):
   ```python
   pose = self.mp_pose.Pose(static_image_mode=True, ...)
   ```
   Ogni frame viene processato indipendentemente, eliminando completamente i problemi di timestamp.

3. **Processamento sequenziale** invece di parallelo (più lento)

## ✅ Verifica

Dopo questa modifica, l'errore timestamp mismatch non dovrebbe più apparire nei log.

**Test**:
```bash
# Crea baseline con 5 video
POST /api/create_baseline

# Verifica log: non dovrebbero esserci errori timestamp
```

## 📚 Riferimenti

- MediaPipe Smooth Landmarks: https://google.github.io/mediapipe/solutions/pose.html
- Timestamp Synchronization: https://ai.google.dev/edge/mediapipe/framework/framework_concepts/synchronization

---

**✅ Fix implementato! L'errore timestamp mismatch dovrebbe essere risolto.**

