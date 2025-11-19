"""
Modulo per l'estrazione dei keypoint 3D dal video usando MediaPipe
Ottimizzato con parallelizzazione e caching
"""
import cv2
import mediapipe as mp
import numpy as np
from typing import List, Optional, Tuple
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
import logging
import time

# Logger per questo modulo
logger = logging.getLogger('KEYPOINT_EXTRACTOR')


class KeypointExtractor:
    """Classe per estrarre i keypoint 3D del mondo da video usando MediaPipe"""
    
    # Directory per cache
    CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache', 'keypoints')
    
    def __init__(self, model_complexity=1, min_detection_confidence=0.5, min_tracking_confidence=0.5, 
                 use_cache=True, max_workers=None):
        """
        Inizializza l'estrattore di keypoint
        
        Args:
            model_complexity: Complessità del modello (0, 1, o 2)
            min_detection_confidence: Confidenza minima per la detection
            min_tracking_confidence: Confidenza minima per il tracking
            use_cache: Se True, usa cache per evitare rielaborazioni
            max_workers: Numero massimo di worker per parallelizzazione (None = auto)
        """
        self.model_complexity = model_complexity
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.use_cache = use_cache
        self.max_workers = max_workers or min(5, multiprocessing.cpu_count())
        
        # Crea directory cache se non esiste
        if self.use_cache:
            os.makedirs(self.CACHE_DIR, exist_ok=True)
        
        # MediaPipe pose verrà creato per ogni thread (non thread-safe)
        self.mp_pose = mp.solutions.pose
    
    def _get_cache_path(self, video_path: str, target_fps: Optional[float] = None) -> str:
        """Genera il percorso del file cache per un video"""
        # Crea hash del percorso video e parametri
        cache_key = f"{video_path}_{target_fps}_{self.model_complexity}"
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
        return os.path.join(self.CACHE_DIR, f"{cache_hash}.npy")
    
    def _load_from_cache(self, cache_path: str) -> Optional[np.ndarray]:
        """Carica keypoints dalla cache se disponibile"""
        if os.path.exists(cache_path):
            try:
                keypoints = np.load(cache_path)
                logger.info(f"✓ Keypoints caricati dalla cache: {os.path.basename(cache_path)}")
                logger.info(f"  Shape keypoints: {keypoints.shape}")
                return keypoints
            except Exception as e:
                logger.warning(f"⚠ Errore nel caricare cache: {e}")
        return None
    
    def _save_to_cache(self, keypoints: np.ndarray, cache_path: str):
        """Salva keypoints nella cache"""
        try:
            np.save(cache_path, keypoints)
            logger.info(f"✓ Keypoints salvati in cache: {os.path.basename(cache_path)}")
        except Exception as e:
            logger.warning(f"⚠ Errore nel salvare cache: {e}")
        
    def extract_from_video(self, video_path: str, target_fps: Optional[float] = None) -> Optional[np.ndarray]:
        """
        Estrae i keypoint 3D del mondo da un video
        
        Args:
            video_path: Percorso del video da processare
            target_fps: FPS target per il resampling (opzionale). Se None, usa gli FPS originali.
            
        Returns:
            Array numpy di forma (n_frames, 33, 4) contenente i keypoint 3D + visibilità
            o None se l'estrazione fallisce
        """
        start_time = time.time()
        video_name = os.path.basename(video_path)
        logger.info(f"=== Inizio estrazione keypoint da: {video_name} ===")
        
        # Controlla cache
        if self.use_cache:
            cache_path = self._get_cache_path(video_path, target_fps)
            cached = self._load_from_cache(cache_path)
            if cached is not None:
                elapsed = time.time() - start_time
                logger.info(f"=== Estrazione completata (da cache) in {elapsed:.2f}s ===")
                return cached
        
        # Crea MediaPipe pose per questo thread
        pose = self.mp_pose.Pose(
            model_complexity=self.model_complexity,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
            enable_segmentation=False,
            smooth_landmarks=True
        )
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            logger.error(f"Errore nell'aprire il video: {video_path}")
            return None
        
        # Ottieni gli FPS originali del video
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        logger.info(f"FPS originali: {original_fps:.2f}, Frame totali: {total_frames}")
        
        # Determina se serve resampling
        if target_fps is not None and abs(original_fps - target_fps) > 0.5:
            logger.warning(f"⚠️ FPS mismatch: video={original_fps:.2f}, target={target_fps:.2f}")
            logger.info(f"   Applicando resampling a {target_fps} FPS...")
            # Calcola quanti frame saltare (per downsampling) o duplicare (per upsampling)
            if original_fps > target_fps:
                # Downsampling: salta frame
                skip_frames = int(original_fps / target_fps)
                use_resampling = True
                logger.info(f"   Downsampling: salto 1 frame ogni {skip_frames}")
            else:
                # Upsampling: duplica frame (implementazione semplificata)
                logger.warning(f"   ⚠️ Upsampling non completamente supportato. Usando tutti i frame disponibili.")
                skip_frames = 1
                use_resampling = False
        else:
            skip_frames = 1
            use_resampling = False
            if target_fps is not None:
                logger.info(f"✓ FPS corrispondono: {original_fps:.2f} ≈ {target_fps:.2f}")
        
        keypoints_sequence = []
        frame_count = 0
        frames_skipped = 0
        frames_with_keypoints = 0
        frames_without_keypoints = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Resampling: salta frame se necessario
            if use_resampling and skip_frames > 1:
                if frames_skipped < skip_frames - 1:
                    frames_skipped += 1
                    continue
                frames_skipped = 0
            
            # Converti BGR a RGB (MediaPipe richiede RGB)
            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            except Exception as e:
                logger.warning(f"⚠️ Errore conversione colore frame {frame_count}: {e}")
                keypoints_sequence.append(np.zeros((33, 4)))
                frame_count += 1
                frames_without_keypoints += 1
                continue
            
            # Processa il frame con gestione errori robusta
            try:
                results = pose.process(frame_rgb)
                
                if results and results.pose_world_landmarks:
                    # Estrai i landmark 3D del mondo (coordinate in metri)
                    landmarks = results.pose_world_landmarks.landmark
                    
                    # Converti in array numpy: [x, y, z, visibility]
                    frame_keypoints = np.array([
                        [lm.x, lm.y, lm.z, lm.visibility]
                        for lm in landmarks
                    ])
                    
                    keypoints_sequence.append(frame_keypoints)
                    frame_count += 1
                    frames_with_keypoints += 1
                else:
                    # Se non vengono rilevati landmark, riempi con zeri
                    keypoints_sequence.append(np.zeros((33, 4)))
                    frame_count += 1
                    frames_without_keypoints += 1
            except Exception as e:
                logger.warning(f"⚠️ Errore MediaPipe frame {frame_count}: {e}")
                # In caso di errore, usa frame con zeri (fallback)
                keypoints_sequence.append(np.zeros((33, 4)))
                frame_count += 1
                frames_without_keypoints += 1
        
        cap.release()
        pose.close()
        
        if len(keypoints_sequence) == 0:
            logger.error(f"Nessun keypoint estratto dal video: {video_path}")
            return None
        
        keypoints_array = np.array(keypoints_sequence)
        elapsed_time = time.time() - start_time
        
        # Log statistiche estrazione
        logger.info(f"=== Statistiche estrazione keypoint ===")
        logger.info(f"  Frame totali processati: {frame_count}")
        logger.info(f"  Frame con keypoint rilevati: {frames_with_keypoints}")
        logger.info(f"  Frame senza keypoint (scartati): {frames_without_keypoints}")
        logger.info(f"  Percentuale successo: {(frames_with_keypoints/frame_count*100):.1f}%")
        logger.info(f"  Shape output: {keypoints_array.shape}")
        if use_resampling:
            logger.info(f"  Resampling applicato: {original_fps:.2f} FPS → {target_fps:.2f} FPS")
        logger.info(f"  Tempo totale elaborazione: {elapsed_time:.2f}s")
        logger.info(f"  Velocità: {frame_count/elapsed_time:.1f} frame/s")
        
        # Salva in cache
        if self.use_cache:
            cache_path = self._get_cache_path(video_path, target_fps)
            self._save_to_cache(keypoints_array, cache_path)
        
        logger.info(f"=== Estrazione keypoint completata ===")
        
        return keypoints_array
    
    def extract_from_multiple_videos(self, video_paths: List[str], target_fps: Optional[float] = None, 
                                     parallel: bool = True) -> Optional[np.ndarray]:
        """
        Estrae i keypoint da multipli video e li concatena (ottimizzato con parallelizzazione)
        
        Args:
            video_paths: Lista dei percorsi dei video
            target_fps: FPS target per il resampling (opzionale)
            parallel: Se True, processa i video in parallelo
            
        Returns:
            Array numpy concatenato di tutti i keypoint
        """
        if not parallel or len(video_paths) == 1:
            # Processamento sequenziale (fallback o singolo video)
            all_keypoints = []
            for video_path in video_paths:
                keypoints = self.extract_from_video(video_path, target_fps=target_fps)
                if keypoints is not None:
                    all_keypoints.append(keypoints)
        else:
            # Processamento parallelo
            logger.info(f"🚀 Estrazione parallela di {len(video_paths)} video con {self.max_workers} worker...")
            all_keypoints = []
            
            def extract_single(video_path):
                """Funzione helper per estrazione singola (crea nuovo extractor per thread safety)"""
                extractor = KeypointExtractor(
                    model_complexity=self.model_complexity,
                    min_detection_confidence=self.min_detection_confidence,
                    min_tracking_confidence=self.min_tracking_confidence,
                    use_cache=self.use_cache,
                    max_workers=1
                )
                return extractor.extract_from_video(video_path, target_fps=target_fps)
            
            # Usa ThreadPoolExecutor per parallelizzare
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_video = {executor.submit(extract_single, vp): vp for vp in video_paths}
                video_to_keypoints = {}
                
                for future in as_completed(future_to_video):
                    video_path = future_to_video[future]
                    try:
                        keypoints = future.result()
                        if keypoints is not None:
                            video_to_keypoints[video_path] = keypoints
                            logger.info(f"✓ Completato: {os.path.basename(video_path)} ({keypoints.shape[0]} frame)")
                    except Exception as e:
                        logger.error(f"⚠ Errore nell'elaborazione di {video_path}: {e}")
            
            # Ordina per mantenere l'ordine originale dei video
            sorted_keypoints = [video_to_keypoints[vp] for vp in video_paths if vp in video_to_keypoints]
            all_keypoints = sorted_keypoints
        
        if len(all_keypoints) == 0:
            logger.error("Nessun keypoint estratto da nessun video")
            return None
        
        # Concatena tutti i keypoint lungo l'asse temporale
        concatenated = np.concatenate(all_keypoints, axis=0)
        total_frames = sum(kp.shape[0] for kp in all_keypoints)
        logger.info(f"=== Estrazione multipla completata ===")
        logger.info(f"  Video processati: {len(all_keypoints)}/{len(video_paths)}")
        logger.info(f"  Frame totali concatenati: {total_frames}")
        logger.info(f"  Shape finale: {concatenated.shape}")
        
        return concatenated
    
    def __del__(self):
        """Chiude le risorse MediaPipe"""
        # Non chiudiamo qui perché pose viene creato per thread
        pass

