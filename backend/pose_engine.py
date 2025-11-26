"""
Modulo PoseEngine per analisi biomeccanica basata su geometria
Sostituisce l'approccio Deep Learning con calcoli geometrici/statistici deterministici
"""
import numpy as np
import cv2
import mediapipe as mp
from scipy.signal import find_peaks
import logging
import os
import hashlib
import pickle
import warnings
import sys
from contextlib import contextmanager
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger('POSE_ENGINE')

# Sopprimi warning di MediaPipe timestamp mismatch (sono solo warning, non errori fatali)
# Questi warning appaiono con parallelizzazione ma non bloccano il processing
warnings.filterwarnings('ignore', category=UserWarning, module='mediapipe')

@contextmanager
def suppress_stderr():
    """Context manager per sopprimere stderr temporaneamente"""
    with open(os.devnull, 'w') as devnull:
        old_stderr = sys.stderr
        try:
            sys.stderr = devnull
            yield
        finally:
            sys.stderr = old_stderr


class PoseEngine:
    """
    Engine per l'analisi biomeccanica della corsa basato su calcoli geometrici
    Vista: Frontal Plane, Posterior View (vista posteriore)
    """
    
    # Directory per cache
    CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache', 'pose_engine')
    
    # Indici dei landmark MediaPipe
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_HEEL = 29
    RIGHT_HEEL = 30
    LEFT_FOOT_INDEX = 31
    RIGHT_FOOT_INDEX = 32
    
    def __init__(self, 
                 model_complexity: int = 2,
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5,
                 use_cache: bool = True):
        """
        Inizializza il PoseEngine
        
        Args:
            model_complexity: 0, 1, o 2 (più alto = più accurato ma più lento)
            min_detection_confidence: Soglia di confidenza per rilevamento
            min_tracking_confidence: Soglia di confidenza per tracking
            use_cache: Se True, usa cache per evitare rielaborazioni
        """
        self.mp_pose = mp.solutions.pose
        self.model_complexity = model_complexity
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.use_cache = use_cache
        
        # Crea directory cache se non esiste
        if self.use_cache:
            os.makedirs(self.CACHE_DIR, exist_ok=True)
        
    def _get_angle_2d(self, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
        """
        Calcola l'angolo tra tre punti in 2D (vista frontale)
        
        Args:
            a: Punto 1 (es. anca)
            b: Punto 2 (es. ginocchio) - vertice dell'angolo
            c: Punto 3 (es. caviglia)
            
        Returns:
            Angolo in gradi
        """
        # Usa solo coordinate X e Y (vista frontale)
        ba = a[:2] - b[:2]
        bc = c[:2] - b[:2]
        
        # Calcola l'angolo usando il prodotto scalare
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
        angle = np.arccos(cosine_angle)
        
        return np.degrees(angle)
    
    def _get_pelvic_drop(self, l_hip: np.ndarray, r_hip: np.ndarray) -> float:
        """
        Calcola la caduta pelvica (pelvic drop) in gradi
        Misura l'inclinazione del bacino nel piano frontale
        
        Args:
            l_hip: Posizione 3D dell'anca sinistra
            r_hip: Posizione 3D dell'anca destra
            
        Returns:
            Angolo di inclinazione in gradi (positivo = caduta a sinistra)
        """
        # Usa coordinate Y (verticale) e X (orizzontale) per vista frontale
        delta_y = l_hip[1] - r_hip[1]  # Differenza verticale
        delta_x = abs(l_hip[0] - r_hip[0])  # Distanza orizzontale
        
        # Calcola l'angolo di inclinazione
        angle = np.arctan2(delta_y, delta_x + 1e-6)
        return np.degrees(angle)
    
    def _get_knee_valgus(self, hip: np.ndarray, knee: np.ndarray, ankle: np.ndarray) -> float:
        """
        Calcola il valgismo del ginocchio (knee valgus)
        Misura la deviazione mediale del ginocchio rispetto all'asse anca-caviglia
        
        Args:
            hip: Posizione 3D dell'anca
            knee: Posizione 3D del ginocchio
            ankle: Posizione 3D della caviglia
            
        Returns:
            Angolo di valgismo in gradi (positivo = valgismo, negativo = varismo)
        """
        # Calcola l'angolo nel piano frontale (X-Y)
        angle = self._get_angle_2d(hip, knee, ankle)
        
        # Converti in valgus: 180° = perfettamente dritto
        # Angolo < 180 indica valgismo, > 180 varismo
        valgus = 180.0 - angle
        
        return valgus
    
    def _detect_cadence(self, ankle_y: np.ndarray, fps: float) -> Tuple[float, List[int]]:
        """
        Calcola la cadenza (passi al minuto) usando rilevamento picchi
        
        Args:
            ankle_y: Array con coordinate Y della caviglia nel tempo
            fps: Frame per secondo del video
            
        Returns:
            Tupla (cadenza in passi/min, lista di indici dei picchi)
        """
        # Inverti l'array perché Y cresce verso il basso in MediaPipe
        ankle_y_inverted = -ankle_y
        
        # Trova i picchi (quando il piede è più alto, durante la fase di swing)
        # distance: minimo di frame tra picchi (es. 0.3s a 30fps = 9 frame)
        min_distance = int(0.3 * fps)
        
        # prominence: quanto deve essere prominente il picco
        peaks, properties = find_peaks(
            ankle_y_inverted,
            distance=min_distance,
            prominence=0.02  # Valore empirico
        )
        
        if len(peaks) < 2:
            logger.warning("Pochi picchi rilevati per calcolo cadenza")
            return 0.0, []
        
        # Calcola la cadenza media
        # Ogni picco rappresenta un passo
        n_steps = len(peaks)
        duration_seconds = len(ankle_y) / fps
        cadence = (n_steps / duration_seconds) * 60.0  # passi/minuto
        
        return cadence, list(peaks)
    
    def _calculate_cadence_series(self, left_peaks: List[int], right_peaks: List[int], 
                                   n_frames: int, fps: float, window_frames: int) -> np.ndarray:
        """
        Calcola una serie temporale della cadenza usando finestre temporali
        
        Args:
            left_peaks: Lista di indici dei picchi per la caviglia sinistra
            right_peaks: Lista di indici dei picchi per la caviglia destra
            n_frames: Numero totale di frame
            fps: Frame per secondo
            window_frames: Dimensione della finestra in frame
            
        Returns:
            Array con la cadenza per ogni frame (calcolata su finestre temporali)
        """
        cadence_series = np.zeros(n_frames)
        
        # Combina tutti i picchi (sinistra e destra) e ordina
        all_peaks = sorted(list(set(left_peaks + right_peaks)))
        
        if len(all_peaks) < 2:
            # Se non ci sono abbastanza picchi, usa la cadenza media per tutto il video
            if len(all_peaks) > 0:
                duration_seconds = n_frames / fps
                avg_cadence = (len(all_peaks) / duration_seconds) * 60.0
                cadence_series.fill(avg_cadence)
            return cadence_series
        
        # Per ogni frame, calcola la cadenza nella finestra temporale
        for i in range(n_frames):
            # Finestra temporale: [i - window_frames/2, i + window_frames/2]
            window_start = max(0, i - window_frames // 2)
            window_end = min(n_frames, i + window_frames // 2)
            
            # Conta i picchi nella finestra
            peaks_in_window = [p for p in all_peaks if window_start <= p < window_end]
            n_steps = len(peaks_in_window)
            
            # Calcola cadenza per questa finestra
            window_duration_seconds = (window_end - window_start) / fps
            if window_duration_seconds > 0:
                cadence_series[i] = (n_steps / window_duration_seconds) * 60.0
            else:
                # Se la finestra è vuota, usa la cadenza media globale
                duration_seconds = n_frames / fps
                cadence_series[i] = (len(all_peaks) / duration_seconds) * 60.0
        
        return cadence_series
    
    def _get_cache_path(self, video_path: str, fps: Optional[float] = None) -> str:
        """
        Genera il percorso del file cache per un video
        
        Args:
            video_path: Percorso del video
            fps: FPS del video
            
        Returns:
            Percorso completo del file cache
        """
        # Ottieni timestamp di modifica del file per invalidare cache se video cambia
        try:
            stat = os.stat(video_path)
            mtime = stat.st_mtime
        except OSError:
            mtime = 0
        
        # Crea hash del percorso video, timestamp, fps e parametri MediaPipe
        cache_key = f"{video_path}_{mtime}_{fps}_{self.model_complexity}_{self.min_detection_confidence}_{self.min_tracking_confidence}"
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
        return os.path.join(self.CACHE_DIR, f"{cache_hash}.pkl")
    
    def _load_from_cache(self, cache_path: str) -> Optional[Dict]:
        """
        Carica risultati dalla cache se disponibile
        
        Args:
            cache_path: Percorso del file cache
            
        Returns:
            Dizionario con risultati o None se cache non disponibile
        """
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    result = pickle.load(f)
                logger.info(f"✓ Risultati caricati dalla cache: {os.path.basename(cache_path)}")
                logger.info(f"  Video: {result.get('n_frames', 0)} frame, FPS: {result.get('fps', 0):.2f}")
                return result
            except Exception as e:
                logger.warning(f"⚠ Errore nel caricare cache: {e}")
        return None
    
    def _save_to_cache(self, result: Dict, cache_path: str):
        """
        Salva risultati nella cache
        
        Args:
            result: Dizionario con risultati del processing
            cache_path: Percorso del file cache
        """
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(result, f)
            logger.info(f"✓ Risultati salvati in cache: {os.path.basename(cache_path)}")
        except Exception as e:
            logger.warning(f"⚠ Errore nel salvare cache: {e}")
    
    def process_video(self, video_path: str, fps: Optional[float] = None) -> Dict:
        """
        Processa un video e estrae metriche biomeccaniche
        
        Args:
            video_path: Percorso del video da analizzare
            fps: FPS del video (opzionale, altrimenti usa quelli del video)
            
        Returns:
            Dizionario con metriche e serie temporali:
            {
                'left_knee_valgus': [frame1, frame2, ...],
                'right_knee_valgus': [...],
                'pelvic_drop': [...],
                'left_cadence': float,
                'right_cadence': float,
                'fps': float,
                'n_frames': int
            }
        """
        logger.info(f"=== Inizio processing video: {video_path} ===")
        
        # Controlla cache se abilitata
        if self.use_cache:
            cache_path = self._get_cache_path(video_path, fps)
            cached_result = self._load_from_cache(cache_path)
            if cached_result is not None:
                logger.info(f"=== Processing completato (da cache) ===")
                return cached_result
        
        # Apri il video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Impossibile aprire il video: {video_path}")
            raise ValueError(f"Impossibile aprire il video: {video_path}")
        
        # Ottieni FPS del video se non forniti
        if fps is None:
            fps = cap.get(cv2.CAP_PROP_FPS)
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        logger.info(f"Video: {total_frames} frame, {fps:.2f} FPS")
        
        # Inizializza MediaPipe Pose
        # NOTA: I warning di timestamp mismatch possono apparire con parallelizzazione
        # ma sono solo warning informativi, non errori fatali. Il processing continua normalmente.
        # Sopprimiamo questi warning perché non influenzano i risultati.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pose = self.mp_pose.Pose(
                model_complexity=self.model_complexity,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=0.1,  # Basso per ridurre dipendenze temporali
                enable_segmentation=False,
                smooth_landmarks=False  # Disabilitato per evitare tracking temporale
            )
        
        # Array per raccogliere dati
        left_knee_valgus_series = []
        right_knee_valgus_series = []
        pelvic_drop_series = []
        left_ankle_y_series = []
        right_ankle_y_series = []
        
        frame_count = 0
        frames_with_pose = 0
        
        # Processa frame per frame
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Converti BGR a RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Processa con MediaPipe
            # NOTA: I warning di timestamp mismatch vengono soppressi perché sono solo
            # warning informativi che non bloccano il processing. MediaPipe continua
            # a funzionare correttamente anche con questi warning.
            # MediaPipe stampa questi warning su stderr, quindi li sopprimiamo temporaneamente
            try:
                with suppress_stderr():
                    results = pose.process(frame_rgb)
            except Exception as e:
                # Se c'è un errore fatale (raro), logga e continua con frame vuoto
                logger.warning(f"⚠ Errore MediaPipe frame {frame_count}: {e}")
                results = None
            
            if results and results.pose_world_landmarks:
                landmarks = results.pose_world_landmarks.landmark
                
                # Estrai posizioni 3D
                l_hip = np.array([landmarks[self.LEFT_HIP].x, 
                                 landmarks[self.LEFT_HIP].y,
                                 landmarks[self.LEFT_HIP].z])
                r_hip = np.array([landmarks[self.RIGHT_HIP].x,
                                 landmarks[self.RIGHT_HIP].y,
                                 landmarks[self.RIGHT_HIP].z])
                l_knee = np.array([landmarks[self.LEFT_KNEE].x,
                                  landmarks[self.LEFT_KNEE].y,
                                  landmarks[self.LEFT_KNEE].z])
                r_knee = np.array([landmarks[self.RIGHT_KNEE].x,
                                  landmarks[self.RIGHT_KNEE].y,
                                  landmarks[self.RIGHT_KNEE].z])
                l_ankle = np.array([landmarks[self.LEFT_ANKLE].x,
                                   landmarks[self.LEFT_ANKLE].y,
                                   landmarks[self.LEFT_ANKLE].z])
                r_ankle = np.array([landmarks[self.RIGHT_ANKLE].x,
                                   landmarks[self.RIGHT_ANKLE].y,
                                   landmarks[self.RIGHT_ANKLE].z])
                
                # Calcola metriche
                left_valgus = self._get_knee_valgus(l_hip, l_knee, l_ankle)
                right_valgus = self._get_knee_valgus(r_hip, r_knee, r_ankle)
                pelvic_drop = self._get_pelvic_drop(l_hip, r_hip)
                
                # Salva dati
                left_knee_valgus_series.append(left_valgus)
                right_knee_valgus_series.append(right_valgus)
                pelvic_drop_series.append(pelvic_drop)
                left_ankle_y_series.append(l_ankle[1])
                right_ankle_y_series.append(r_ankle[1])
                
                frames_with_pose += 1
            else:
                # Frame senza pose: usa valori precedenti o zero
                left_knee_valgus_series.append(
                    left_knee_valgus_series[-1] if left_knee_valgus_series else 0.0
                )
                right_knee_valgus_series.append(
                    right_knee_valgus_series[-1] if right_knee_valgus_series else 0.0
                )
                pelvic_drop_series.append(
                    pelvic_drop_series[-1] if pelvic_drop_series else 0.0
                )
                left_ankle_y_series.append(
                    left_ankle_y_series[-1] if left_ankle_y_series else 0.0
                )
                right_ankle_y_series.append(
                    right_ankle_y_series[-1] if right_ankle_y_series else 0.0
                )
            
            frame_count += 1
        
        cap.release()
        pose.close()
        
        logger.info(f"Processing completato: {frame_count} frame, {frames_with_pose} con pose rilevata")
        logger.info(f"Percentuale successo: {(frames_with_pose/frame_count*100):.1f}%")
        
        # Converti in numpy array
        left_knee_valgus_arr = np.array(left_knee_valgus_series)
        right_knee_valgus_arr = np.array(right_knee_valgus_series)
        pelvic_drop_arr = np.array(pelvic_drop_series)
        left_ankle_y_arr = np.array(left_ankle_y_series)
        right_ankle_y_arr = np.array(right_ankle_y_series)
        
        # Calcola cadenza
        left_cadence, left_peaks = self._detect_cadence(left_ankle_y_arr, fps)
        right_cadence, right_peaks = self._detect_cadence(right_ankle_y_arr, fps)
        avg_cadence = (left_cadence + right_cadence) / 2.0
        
        # Calcola serie temporale della cadenza (rolling window)
        # Usa una finestra di 2 secondi per calcolare la cadenza locale
        window_seconds = 2.0
        window_frames = int(window_seconds * fps)
        cadence_series = self._calculate_cadence_series(left_peaks, right_peaks, frame_count, fps, window_frames)
        
        logger.info(f"Cadenza rilevata: SX={left_cadence:.1f} spm, DX={right_cadence:.1f} spm, Media={avg_cadence:.1f} spm")
        
        # Statistiche rapide
        logger.info(f"Valgismo Ginocchio SX: μ={np.mean(left_knee_valgus_arr):.2f}°, σ={np.std(left_knee_valgus_arr):.2f}°")
        logger.info(f"Valgismo Ginocchio DX: μ={np.mean(right_knee_valgus_arr):.2f}°, σ={np.std(right_knee_valgus_arr):.2f}°")
        logger.info(f"Caduta Pelvica: μ={np.mean(pelvic_drop_arr):.2f}°, σ={np.std(pelvic_drop_arr):.2f}°")
        
        result = {
            'left_knee_valgus': left_knee_valgus_arr.tolist(),
            'right_knee_valgus': right_knee_valgus_arr.tolist(),
            'pelvic_drop': pelvic_drop_arr.tolist(),
            'cadence': cadence_series.tolist(),  # Serie temporale della cadenza
            'left_cadence': float(left_cadence),
            'right_cadence': float(right_cadence),
            'avg_cadence': float(avg_cadence),
            'fps': float(fps),
            'n_frames': frame_count,
            'frames_with_pose': frames_with_pose
        }
        
        # Salva in cache se abilitata
        if self.use_cache:
            cache_path = self._get_cache_path(video_path, fps)
            self._save_to_cache(result, cache_path)
        
        return result
    
    def create_baseline_stats(self, videos_data: List[Dict]) -> Dict:
        """
        Crea statistiche baseline da multipli video processati
        Calcola Media, Deviazione Standard, Min e Max per ogni metrica
        
        Args:
            videos_data: Lista di dizionari restituiti da process_video()
            
        Returns:
            Dizionario con statistiche aggregate:
            {
                'left_knee_valgus': {'mean': float, 'std': float, 'min': float, 'max': float},
                'right_knee_valgus': {...},
                'pelvic_drop': {...},
                'cadence': {...},
                'n_videos': int,
                'total_frames': int
            }
        """
        logger.info(f"=== Creazione baseline da {len(videos_data)} video ===")
        
        # Aggrega tutti i dati
        all_left_valgus = []
        all_right_valgus = []
        all_pelvic_drop = []
        all_cadence = []  # Per la cadenza, usiamo la media della serie temporale per coerenza
        total_frames = 0
        
        for video_data in videos_data:
            all_left_valgus.extend(video_data['left_knee_valgus'])
            all_right_valgus.extend(video_data['right_knee_valgus'])
            all_pelvic_drop.extend(video_data['pelvic_drop'])
            
            # Per la cadenza, usa la media della serie temporale invece di avg_cadence
            # Questo è coerente con il calcolo dello Z-Score
            cadence_series = video_data.get('cadence', [])
            if cadence_series and len(cadence_series) > 0:
                # Filtra valori zero (potrebbero essere frame senza dati validi)
                cadence_series_filtered = [c for c in cadence_series if c > 0]
                if len(cadence_series_filtered) > 0:
                    cadence_mean = np.mean(cadence_series_filtered)
                    all_cadence.append(cadence_mean)
                else:
                    # Fallback a avg_cadence se la serie è tutta zero
                    all_cadence.append(video_data.get('avg_cadence', 0.0))
            else:
                # Fallback a avg_cadence se la serie non esiste
                all_cadence.append(video_data.get('avg_cadence', 0.0))
            
            total_frames += video_data['n_frames']
        
        # Converti in numpy array
        all_left_valgus = np.array(all_left_valgus)
        all_right_valgus = np.array(all_right_valgus)
        all_pelvic_drop = np.array(all_pelvic_drop)
        all_cadence = np.array(all_cadence)
        
        # Calcola statistiche
        baseline_stats = {
            'left_knee_valgus': {
                'mean': float(np.mean(all_left_valgus)),
                'std': float(np.std(all_left_valgus)),
                'min': float(np.min(all_left_valgus)),
                'max': float(np.max(all_left_valgus))
            },
            'right_knee_valgus': {
                'mean': float(np.mean(all_right_valgus)),
                'std': float(np.std(all_right_valgus)),
                'min': float(np.min(all_right_valgus)),
                'max': float(np.max(all_right_valgus))
            },
            'pelvic_drop': {
                'mean': float(np.mean(all_pelvic_drop)),
                'std': float(np.std(all_pelvic_drop)),
                'min': float(np.min(all_pelvic_drop)),
                'max': float(np.max(all_pelvic_drop))
            },
            'cadence': {
                'mean': float(np.mean(all_cadence)),
                'std': float(np.std(all_cadence)),
                'min': float(np.min(all_cadence)),
                'max': float(np.max(all_cadence))
            },
            'n_videos': len(videos_data),
            'total_frames': total_frames
        }
        
        logger.info("=== Statistiche Baseline ===")
        logger.info(f"Valgismo Ginocchio SX: μ={baseline_stats['left_knee_valgus']['mean']:.2f}° ± {baseline_stats['left_knee_valgus']['std']:.2f}°")
        logger.info(f"Valgismo Ginocchio DX: μ={baseline_stats['right_knee_valgus']['mean']:.2f}° ± {baseline_stats['right_knee_valgus']['std']:.2f}°")
        logger.info(f"Caduta Pelvica: μ={baseline_stats['pelvic_drop']['mean']:.2f}° ± {baseline_stats['pelvic_drop']['std']:.2f}°")
        logger.info(f"Cadenza: μ={baseline_stats['cadence']['mean']:.1f} ± {baseline_stats['cadence']['std']:.1f} spm (calcolata dalla media delle serie temporali)")
        
        return baseline_stats
    
    def calculate_z_scores(self, video_data: Dict, baseline_stats: Dict) -> Dict:
        """
        Calcola Z-Score per ogni metrica confrontando con baseline
        Z-Score = (Valore - MediaBaseline) / StdDevBaseline
        
        Args:
            video_data: Dati del video da analizzare (da process_video)
            baseline_stats: Statistiche baseline (da create_baseline_stats)
            
        Returns:
            Dizionario con Z-scores e livelli di anomalia:
            {
                'left_knee_valgus': {'value': float, 'z_score': float, 'level': str},
                'right_knee_valgus': {...},
                'pelvic_drop': {...},
                'cadence': {...},
                'overall_status': 'Ottimale' | 'Attenzione' | 'Critico'
            }
        """
        logger.info("=== Calcolo Z-Scores ===")
        
        # Calcola valori medi dal video
        left_valgus_mean = np.mean(video_data['left_knee_valgus'])
        right_valgus_mean = np.mean(video_data['right_knee_valgus'])
        pelvic_drop_mean = np.mean(video_data['pelvic_drop'])
        
        # Per la cadenza, usa la media della serie temporale invece di avg_cadence
        # Questo è più coerente con il grafico che mostra la serie temporale
        cadence_series = video_data.get('cadence', [])
        if cadence_series and len(cadence_series) > 0:
            # Filtra valori zero (potrebbero essere frame senza dati validi)
            cadence_series_filtered = [c for c in cadence_series if c > 0]
            if len(cadence_series_filtered) > 0:
                cadence_value = np.mean(cadence_series_filtered)
                logger.info(f"  Cadenza: usando media serie temporale = {cadence_value:.1f} spm (da {len(cadence_series_filtered)} frame validi)")
            else:
                # Fallback a avg_cadence se la serie è tutta zero
                cadence_value = video_data.get('avg_cadence', 0.0)
                logger.warning(f"  Cadenza: serie temporale vuota, usando avg_cadence = {cadence_value:.1f} spm")
        else:
            # Fallback a avg_cadence se la serie non esiste
            cadence_value = video_data.get('avg_cadence', 0.0)
            logger.warning(f"  Cadenza: serie temporale non disponibile, usando avg_cadence = {cadence_value:.1f} spm")
        
        # Calcola Z-scores
        z_left_valgus = (left_valgus_mean - baseline_stats['left_knee_valgus']['mean']) / \
                        (baseline_stats['left_knee_valgus']['std'] + 1e-6)
        z_right_valgus = (right_valgus_mean - baseline_stats['right_knee_valgus']['mean']) / \
                         (baseline_stats['right_knee_valgus']['std'] + 1e-6)
        z_pelvic_drop = (pelvic_drop_mean - baseline_stats['pelvic_drop']['mean']) / \
                        (baseline_stats['pelvic_drop']['std'] + 1e-6)
        z_cadence = (cadence_value - baseline_stats['cadence']['mean']) / \
                    (baseline_stats['cadence']['std'] + 1e-6)
        
        # Determina livelli per ogni metrica
        # |Z| < 1.0: Ottimale
        # 1.0 <= |Z| < 2.0: Attenzione
        # |Z| >= 2.0: Critico
        def get_level(z_score):
            abs_z = abs(z_score)
            if abs_z < 1.0:
                return 'Ottimale', '#10b981'  # Verde
            elif abs_z < 2.0:
                return 'Attenzione', '#f59e0b'  # Arancione
            else:
                return 'Critico', '#ef4444'  # Rosso
        
        level_left, color_left = get_level(z_left_valgus)
        level_right, color_right = get_level(z_right_valgus)
        level_pelvic, color_pelvic = get_level(z_pelvic_drop)
        level_cadence, color_cadence = get_level(z_cadence)
        
        # Determina stato generale (peggiore tra tutte le metriche)
        all_z_scores = [abs(z_left_valgus), abs(z_right_valgus), 
                       abs(z_pelvic_drop), abs(z_cadence)]
        max_z = max(all_z_scores)
        
        if max_z < 1.0:
            overall_status = 'Ottimale'
            overall_color = '#10b981'
        elif max_z < 2.0:
            overall_status = 'Attenzione'
            overall_color = '#f59e0b'
        else:
            overall_status = 'Critico'
            overall_color = '#ef4444'
        
        logger.info(f"Z-Score Valgismo SX: {z_left_valgus:.2f} -> {level_left}")
        logger.info(f"Z-Score Valgismo DX: {z_right_valgus:.2f} -> {level_right}")
        logger.info(f"Z-Score Caduta Pelvica: {z_pelvic_drop:.2f} -> {level_pelvic}")
        logger.info(f"Z-Score Cadenza: {z_cadence:.2f} -> {level_cadence}")
        logger.info(f"Stato Generale: {overall_status}")
        
        return {
            'left_knee_valgus': {
                'value': float(left_valgus_mean),
                'z_score': float(z_left_valgus),
                'level': level_left,
                'color': color_left
            },
            'right_knee_valgus': {
                'value': float(right_valgus_mean),
                'z_score': float(z_right_valgus),
                'level': level_right,
                'color': color_right
            },
            'pelvic_drop': {
                'value': float(pelvic_drop_mean),
                'z_score': float(z_pelvic_drop),
                'level': level_pelvic,
                'color': color_pelvic
            },
            'cadence': {
                'value': float(cadence_value),
                'z_score': float(z_cadence),
                'level': level_cadence,
                'color': color_cadence
            },
            'overall_status': overall_status,
            'overall_color': overall_color,
            'max_z_score': float(max_z)
        }

