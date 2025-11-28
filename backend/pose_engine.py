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
    Supporta Vista Posteriore (Posterior) e Vista Laterale (Lateral)
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
    
    # Connessioni dello scheletro MediaPipe (per disegnare le ossa)
    # Lista completa delle connessioni standard MediaPipe (33 landmark)
    POSE_CONNECTIONS = [
        # Torso
        (11, 12),  # LEFT_SHOULDER - RIGHT_SHOULDER
        (11, 23),  # LEFT_SHOULDER - LEFT_HIP
        (12, 24),  # RIGHT_SHOULDER - RIGHT_HIP
        (23, 24),  # LEFT_HIP - RIGHT_HIP
        # Braccia sinistra
        (11, 13),  # LEFT_SHOULDER - LEFT_ELBOW
        (13, 15),  # LEFT_ELBOW - LEFT_WRIST
        # Braccia destra
        (12, 14),  # RIGHT_SHOULDER - RIGHT_ELBOW
        (14, 16),  # RIGHT_ELBOW - RIGHT_WRIST
        # Gamba sinistra
        (23, 25),  # LEFT_HIP - LEFT_KNEE
        (25, 27),  # LEFT_KNEE - LEFT_ANKLE
        (27, 29),  # LEFT_ANKLE - LEFT_HEEL
        (27, 31),  # LEFT_ANKLE - LEFT_FOOT_INDEX
        (29, 31),  # LEFT_HEEL - LEFT_FOOT_INDEX
        # Gamba destra
        (24, 26),  # RIGHT_HIP - RIGHT_KNEE
        (26, 28),  # RIGHT_KNEE - RIGHT_ANKLE
        (28, 30),  # RIGHT_ANKLE - RIGHT_HEEL
        (28, 32),  # RIGHT_ANKLE - RIGHT_FOOT_INDEX
        (30, 32),  # RIGHT_HEEL - RIGHT_FOOT_INDEX
    ]
    
    def __init__(self, 
                 model_complexity: int = 2,
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5,
                 use_cache: bool = True,
                 generate_skeleton_video: bool = True):
        """
        Inizializza il PoseEngine
        
        Args:
            model_complexity: 0, 1, o 2 (più alto = più accurato ma più lento)
            min_detection_confidence: Soglia di confidenza per rilevamento
            min_tracking_confidence: Soglia di confidenza per tracking
            use_cache: Se True, usa cache per evitare rielaborazioni
            generate_skeleton_video: Se True, genera video con overlay scheletro
        """
        self.mp_pose = mp.solutions.pose
        self.model_complexity = model_complexity
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.use_cache = use_cache
        self.generate_skeleton_video = generate_skeleton_video
        
        # Crea directory cache se non esiste
        if self.use_cache:
            os.makedirs(self.CACHE_DIR, exist_ok=True)
        
    def _draw_skeleton(self, frame: np.ndarray, landmarks) -> np.ndarray:
        """
        Disegna lo scheletro sul frame usando i landmark MediaPipe
        
        Args:
            frame: Frame del video (BGR)
            landmarks: Landmark MediaPipe (pose_landmarks)
            
        Returns:
            Frame con scheletro disegnato
        """
        if not landmarks or not landmarks.landmark:
            return frame
        
        frame_copy = frame.copy()
        h, w = frame_copy.shape[:2]
        
        # Colori (BGR per OpenCV)
        skeleton_color = (0, 255, 0)  # Verde per le connessioni
        landmark_color = (0, 0, 255)  # Rosso per i landmark
        landmark_radius = 4
        connection_thickness = 2
        
        # Converti landmark in coordinate pixel
        landmark_points = []
        for landmark in landmarks.landmark:
            # Verifica visibilità (visibility > 0.5)
            if landmark.visibility > 0.5:
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                landmark_points.append((x, y, True))
            else:
                landmark_points.append((None, None, False))
        
        # Disegna le connessioni (ossa)
        for connection in self.POSE_CONNECTIONS:
            start_idx, end_idx = connection
            if (start_idx < len(landmark_points) and end_idx < len(landmark_points) and
                landmark_points[start_idx][2] and landmark_points[end_idx][2]):
                start_point = (landmark_points[start_idx][0], landmark_points[start_idx][1])
                end_point = (landmark_points[end_idx][0], landmark_points[end_idx][1])
                cv2.line(frame_copy, start_point, end_point, skeleton_color, connection_thickness)
        
        # Disegna i landmark (giunti) - solo quelli visibili
        for point_data in landmark_points:
            if point_data[2]:  # Se visibile
                cv2.circle(frame_copy, (point_data[0], point_data[1]), landmark_radius, landmark_color, -1)
        
        return frame_copy
    
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
    
    def _get_overstriding(self, ankle: np.ndarray, hip: np.ndarray) -> float:
        """
        Calcola l'overstriding (distanza orizzontale tra caviglia e anca al contatto iniziale)
        Vista Laterale: misura la distanza orizzontale (asse X) tra caviglia e anca
        
        Args:
            ankle: Posizione 3D della caviglia
            hip: Posizione 3D dell'anca
            
        Returns:
            Distanza in unità normalizzate (positivo = caviglia davanti all'anca)
        """
        # Distanza orizzontale (asse X nel piano sagittale)
        horizontal_distance = abs(ankle[0] - hip[0])
        return horizontal_distance
    
    def _get_knee_flexion_angle(self, hip: np.ndarray, knee: np.ndarray, ankle: np.ndarray) -> float:
        """
        Calcola l'angolo di flessione del ginocchio
        Vista Laterale: angolo formato da Anca-Ginocchio-Caviglia nel piano sagittale
        
        Args:
            hip: Posizione 3D dell'anca
            knee: Posizione 3D del ginocchio
            ankle: Posizione 3D della caviglia
            
        Returns:
            Angolo di flessione in gradi (180° = completamente esteso)
        """
        return self._get_angle_2d(hip, knee, ankle)
    
    def _get_trunk_lean(self, shoulder: np.ndarray, hip: np.ndarray) -> float:
        """
        Calcola l'inclinazione del tronco rispetto alla verticale
        Vista Laterale: angolo tra la linea Spalla-Anca e l'asse verticale Y
        
        Args:
            shoulder: Posizione 3D della spalla
            hip: Posizione 3D dell'anca
            
        Returns:
            Angolo di inclinazione in gradi (positivo = inclinato in avanti)
        """
        # Calcola il vettore Spalla-Anca
        trunk_vector = hip - shoulder
        
        # Calcola l'angolo rispetto alla verticale (asse Y)
        # L'asse Y in MediaPipe punta verso il basso, quindi invertiamo
        vertical = np.array([0, -1])  # Vettore verticale verso l'alto
        trunk_2d = np.array([trunk_vector[0], trunk_vector[1]])
        
        # Calcola l'angolo usando prodotto scalare
        cosine_angle = np.dot(trunk_2d, vertical) / (np.linalg.norm(trunk_2d) * np.linalg.norm(vertical) + 1e-6)
        cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
        angle = np.arccos(cosine_angle)
        
        # Converti in gradi e considera il segno (positivo = lean forward)
        angle_deg = np.degrees(angle)
        if trunk_vector[0] > 0:  # Inclinato in avanti
            return angle_deg
        else:  # Inclinato indietro
            return -angle_deg
    
    def _detect_ground_contacts(self, ankle_y: np.ndarray, fps: float) -> List[Tuple[int, int]]:
        """
        Rileva i periodi di contatto al suolo (touchdown to toe-off)
        
        Args:
            ankle_y: Array con coordinate Y della caviglia nel tempo
            fps: Frame per secondo del video
            
        Returns:
            Lista di tuple (frame_touchdown, frame_toeoff)
        """
        # Inverti l'array perché Y cresce verso il basso in MediaPipe
        ankle_y_inverted = -ankle_y
        
        # Trova i minimi locali (quando il piede è a terra)
        # Usa una soglia per determinare quando il piede è "a terra"
        min_height = np.min(ankle_y_inverted)
        max_height = np.max(ankle_y_inverted)
        threshold = min_height + 0.1 * (max_height - min_height)
        
        # Il piede è a terra quando ankle_y_inverted è vicino al minimo
        on_ground = ankle_y_inverted < threshold
        
        # Trova i periodi di contatto continui
        contacts = []
        in_contact = False
        contact_start = 0
        
        for i in range(len(on_ground)):
            if on_ground[i] and not in_contact:
                # Inizio contatto
                contact_start = i
                in_contact = True
            elif not on_ground[i] and in_contact:
                # Fine contatto
                contact_end = i - 1
                if contact_end > contact_start:
                    contacts.append((contact_start, contact_end))
                in_contact = False
        
        # Se l'ultimo frame era ancora in contatto
        if in_contact and len(ankle_y) > contact_start:
            contacts.append((contact_start, len(ankle_y) - 1))
        
        return contacts
    
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
    
    def _get_cache_path(self, video_path: str, fps: Optional[float] = None, view_type: str = 'posterior') -> str:
        """
        Genera il percorso del file cache per un video
        
        Args:
            video_path: Percorso del video
            fps: FPS del video
            view_type: Tipo di vista ('posterior' o 'lateral')
            
        Returns:
            Percorso completo del file cache
        """
        # Ottieni timestamp di modifica del file per invalidare cache se video cambia
        try:
            stat = os.stat(video_path)
            mtime = stat.st_mtime
        except OSError:
            mtime = 0
        
        # Crea hash del percorso video, timestamp, fps, view_type e parametri MediaPipe
        cache_key = f"{video_path}_{mtime}_{fps}_{view_type}_{self.model_complexity}_{self.min_detection_confidence}_{self.min_tracking_confidence}"
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
    
    def process_video(self, video_path: str, fps: Optional[float] = None, view_type: str = 'posterior') -> Dict:
        """
        Processa un video e estrae metriche biomeccaniche
        
        Args:
            video_path: Percorso del video da analizzare
            fps: FPS del video (opzionale, altrimenti usa quelli del video)
            view_type: Tipo di vista ('posterior' o 'lateral')
            
        Returns:
            Dizionario con metriche e serie temporali.
            
            Per vista 'posterior':
            {
                'left_knee_valgus': [frame1, frame2, ...],
                'right_knee_valgus': [...],
                'pelvic_drop': [...],
                'cadence': [...],
                'left_cadence': float,
                'right_cadence': float,
                'avg_cadence': float,
                'fps': float,
                'n_frames': int,
                'view_type': 'posterior'
            }
            
            Per vista 'lateral':
            {
                'overstriding': [...],
                'knee_flexion_ic': [...],
                'trunk_lean': [...],
                'ground_contact_time': [...],
                'avg_gct': float,
                'fps': float,
                'n_frames': int,
                'view_type': 'lateral'
            }
        """
        logger.info(f"=== Inizio processing video: {video_path} ===")
        logger.info(f"Vista: {view_type}")
        
        # Controlla cache se abilitata
        if self.use_cache:
            cache_path = self._get_cache_path(video_path, fps, view_type)
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
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.info(f"Video: {total_frames} frame, {fps:.2f} FPS, {width}x{height}")
        
        # Inizializza VideoWriter per video con scheletro (se richiesto)
        skeleton_video_path = None
        video_writer = None
        if self.generate_skeleton_video:
            from config import Config
            os.makedirs(Config.PROCESSED_VIDEOS_FOLDER, exist_ok=True)
            
            # Genera nome file univoco (sanitizza per evitare problemi con caratteri speciali)
            video_basename = os.path.splitext(os.path.basename(video_path))[0]
            # Sanitizza il nome del file per evitare problemi con caratteri speciali nell'URL
            # Sostituisce caratteri problematici con underscore
            import re
            safe_basename = re.sub(r'[^\w\-_\.]', '_', video_basename)
            # Rimuove punti multipli consecutivi
            safe_basename = re.sub(r'\.+', '.', safe_basename)
            # Se il nome è vuoto dopo la sanitizzazione, usa un nome generico
            if not safe_basename or safe_basename == '_':
                import hashlib
                safe_basename = hashlib.md5(video_path.encode()).hexdigest()[:8]
            skeleton_video_path = os.path.join(
                Config.PROCESSED_VIDEOS_FOLDER,
                f"{safe_basename}_skeleton.mp4"
            )
            logger.debug(f"📹 Nome video originale: {video_basename}")
            logger.debug(f"📹 Nome video sanitizzato: {safe_basename}")
            logger.debug(f"📹 Percorso video scheletro: {skeleton_video_path}")
            
            # Prova diversi codec per compatibilità
            # H.264 è il più compatibile per i browser
            codecs_to_try = [
                ('avc1', 'H.264/AVC'),  # H.264 - migliore compatibilità browser
                ('mp4v', 'MPEG-4'),      # MPEG-4 - fallback
                ('XVID', 'Xvid'),        # Xvid - altro fallback
            ]
            
            video_writer = None
            used_codec = None
            for fourcc_str, codec_name in codecs_to_try:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
                    test_writer = cv2.VideoWriter(skeleton_video_path, fourcc, fps, (width, height))
                    if test_writer.isOpened():
                        video_writer = test_writer
                        used_codec = codec_name
                        logger.info(f"📹 Codec selezionato: {codec_name} ({fourcc_str})")
                        break
                    else:
                        test_writer.release()
                except Exception as e:
                    logger.debug(f"⚠ Codec {codec_name} non disponibile: {e}")
                    continue
            
            if not video_writer:
                # Ultimo tentativo con mp4v
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video_writer = cv2.VideoWriter(skeleton_video_path, fourcc, fps, (width, height))
                used_codec = 'MPEG-4 (mp4v)'
                logger.warning(f"⚠ Usando codec di fallback: {used_codec}")
            
            if not video_writer.isOpened():
                logger.warning(f"⚠ Impossibile creare video writer, disabilito generazione video scheletro")
                video_writer = None
                self.generate_skeleton_video = False
            else:
                logger.info(f"📹 Generazione video con scheletro: {os.path.basename(skeleton_video_path)}")
        
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
        
        # Array per raccogliere dati (inizializzazione diversa per view type)
        if view_type == 'posterior':
            left_knee_valgus_series = []
            right_knee_valgus_series = []
            pelvic_drop_series = []
            left_ankle_y_series = []
            right_ankle_y_series = []
        else:  # lateral
            overstriding_series = []
            knee_flexion_ic_series = []
            trunk_lean_series = []
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
            
            # Disegna scheletro sul frame se richiesto
            if self.generate_skeleton_video and video_writer:
                if results and results.pose_landmarks:
                    frame_with_skeleton = self._draw_skeleton(frame, results.pose_landmarks)
                else:
                    frame_with_skeleton = frame  # Frame senza scheletro se pose non rilevata
                video_writer.write(frame_with_skeleton)
            
            if results and results.pose_world_landmarks:
                landmarks = results.pose_world_landmarks.landmark
                
                # Estrai posizioni 3D comuni
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
                
                if view_type == 'posterior':
                    # Calcola metriche vista posteriore
                    left_valgus = self._get_knee_valgus(l_hip, l_knee, l_ankle)
                    right_valgus = self._get_knee_valgus(r_hip, r_knee, r_ankle)
                    pelvic_drop = self._get_pelvic_drop(l_hip, r_hip)
                    
                    # Salva dati
                    left_knee_valgus_series.append(left_valgus)
                    right_knee_valgus_series.append(right_valgus)
                    pelvic_drop_series.append(pelvic_drop)
                    left_ankle_y_series.append(l_ankle[1])
                    right_ankle_y_series.append(r_ankle[1])
                
                else:  # lateral
                    # Calcola metriche vista laterale
                    # Usa la media di sinistra e destra per i landmark simmetrici
                    hip_center = (l_hip + r_hip) / 2.0
                    knee_center = (l_knee + r_knee) / 2.0
                    ankle_center = (l_ankle + r_ankle) / 2.0
                    
                    l_shoulder = np.array([landmarks[self.LEFT_SHOULDER].x,
                                          landmarks[self.LEFT_SHOULDER].y,
                                          landmarks[self.LEFT_SHOULDER].z])
                    r_shoulder = np.array([landmarks[self.RIGHT_SHOULDER].x,
                                          landmarks[self.RIGHT_SHOULDER].y,
                                          landmarks[self.RIGHT_SHOULDER].z])
                    shoulder_center = (l_shoulder + r_shoulder) / 2.0
                    
                    overstriding = self._get_overstriding(ankle_center, hip_center)
                    knee_flexion = self._get_knee_flexion_angle(hip_center, knee_center, ankle_center)
                    trunk_lean = self._get_trunk_lean(shoulder_center, hip_center)
                    
                    # Salva dati
                    overstriding_series.append(overstriding)
                    knee_flexion_ic_series.append(knee_flexion)
                    trunk_lean_series.append(trunk_lean)
                    left_ankle_y_series.append(l_ankle[1])
                    right_ankle_y_series.append(r_ankle[1])
                
                frames_with_pose += 1
            else:
                # Frame senza pose: usa valori precedenti o zero
                if view_type == 'posterior':
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
                else:  # lateral
                    overstriding_series.append(
                        overstriding_series[-1] if overstriding_series else 0.0
                    )
                    knee_flexion_ic_series.append(
                        knee_flexion_ic_series[-1] if knee_flexion_ic_series else 0.0
                    )
                    trunk_lean_series.append(
                        trunk_lean_series[-1] if trunk_lean_series else 0.0
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
        
        # Chiudi VideoWriter se aperto
        if video_writer:
            video_writer.release()
            if skeleton_video_path:
                if os.path.exists(skeleton_video_path):
                    file_size_mb = os.path.getsize(skeleton_video_path) / (1024 * 1024)
                    logger.info(f"✓ Video con scheletro salvato: {os.path.basename(skeleton_video_path)} ({file_size_mb:.2f} MB)")
                    logger.info(f"  Percorso completo: {skeleton_video_path}")
                else:
                    logger.error(f"❌ Video con scheletro non trovato dopo il salvataggio: {skeleton_video_path}")
                    skeleton_video_path = None  # Imposta a None se il file non esiste
            else:
                logger.warning(f"⚠ Video con scheletro non salvato correttamente (percorso non definito)")
        
        logger.info(f"Processing completato: {frame_count} frame, {frames_with_pose} con pose rilevata")
        logger.info(f"Percentuale successo: {(frames_with_pose/frame_count*100):.1f}%")
        
        # Prepara risultati in base al tipo di vista
        if view_type == 'posterior':
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
            window_seconds = 2.0
            window_frames = int(window_seconds * fps)
            cadence_series = self._calculate_cadence_series(left_peaks, right_peaks, frame_count, fps, window_frames)
            
            logger.info(f"Cadenza rilevata: SX={left_cadence:.1f} spm, DX={right_cadence:.1f} spm, Media={avg_cadence:.1f} spm")
            logger.info(f"Valgismo Ginocchio SX: μ={np.mean(left_knee_valgus_arr):.2f}°, σ={np.std(left_knee_valgus_arr):.2f}°")
            logger.info(f"Valgismo Ginocchio DX: μ={np.mean(right_knee_valgus_arr):.2f}°, σ={np.std(right_knee_valgus_arr):.2f}°")
            logger.info(f"Caduta Pelvica: μ={np.mean(pelvic_drop_arr):.2f}°, σ={np.std(pelvic_drop_arr):.2f}°")
            
            result = {
                'view_type': 'posterior',
                'left_knee_valgus': left_knee_valgus_arr.tolist(),
                'right_knee_valgus': right_knee_valgus_arr.tolist(),
                'pelvic_drop': pelvic_drop_arr.tolist(),
                'cadence': cadence_series.tolist(),
                'left_cadence': float(left_cadence),
                'right_cadence': float(right_cadence),
                'avg_cadence': float(avg_cadence),
                'fps': float(fps),
                'n_frames': frame_count,
                'frames_with_pose': frames_with_pose,
                'skeleton_video_path': skeleton_video_path if skeleton_video_path else None
            }
        
        else:  # lateral
            # Converti in numpy array
            overstriding_arr = np.array(overstriding_series)
            knee_flexion_ic_arr = np.array(knee_flexion_ic_series)
            trunk_lean_arr = np.array(trunk_lean_series)
            left_ankle_y_arr = np.array(left_ankle_y_series)
            right_ankle_y_arr = np.array(right_ankle_y_series)
            
            # Calcola Ground Contact Time (GCT)
            # Usa la media di sinistra e destra
            ankle_y_avg = (left_ankle_y_arr + right_ankle_y_arr) / 2.0
            contacts = self._detect_ground_contacts(ankle_y_avg, fps)
            
            # Calcola GCT per ogni contatto
            gct_values = []
            gct_series = np.zeros(frame_count)
            for start, end in contacts:
                contact_duration = (end - start + 1) / fps
                gct_values.append(contact_duration)
                # Riempi la serie temporale per questo periodo di contatto
                gct_series[start:end+1] = contact_duration
            
            avg_gct = np.mean(gct_values) if len(gct_values) > 0 else 0.0
            
            logger.info(f"Overstriding: μ={np.mean(overstriding_arr):.4f}, σ={np.std(overstriding_arr):.4f}")
            logger.info(f"Flessione Ginocchio @ IC: μ={np.mean(knee_flexion_ic_arr):.2f}°, σ={np.std(knee_flexion_ic_arr):.2f}°")
            logger.info(f"Trunk Lean: μ={np.mean(trunk_lean_arr):.2f}°, σ={np.std(trunk_lean_arr):.2f}°")
            logger.info(f"Ground Contact Time: μ={avg_gct:.3f}s, N={len(gct_values)} contatti")
            
            result = {
                'view_type': 'lateral',
                'overstriding': overstriding_arr.tolist(),
                'knee_flexion_ic': knee_flexion_ic_arr.tolist(),
                'trunk_lean': trunk_lean_arr.tolist(),
                'ground_contact_time': gct_series.tolist(),
                'avg_gct': float(avg_gct),
                'n_contacts': len(gct_values),
                'fps': float(fps),
                'n_frames': frame_count,
                'frames_with_pose': frames_with_pose,
                'skeleton_video_path': skeleton_video_path if skeleton_video_path else None
            }
        
        # Salva in cache se abilitata
        if self.use_cache:
            cache_path = self._get_cache_path(video_path, fps, view_type)
            self._save_to_cache(result, cache_path)
        
        return result
    
    def create_baseline_stats(self, videos_data: List[Dict]) -> Dict:
        """
        Crea statistiche baseline da multipli video processati
        Calcola Media, Deviazione Standard, Min e Max per ogni metrica
        
        Args:
            videos_data: Lista di dizionari restituiti da process_video()
            
        Returns:
            Dizionario con statistiche aggregate.
            
            Per vista 'posterior':
            {
                'view_type': 'posterior',
                'left_knee_valgus': {'mean': float, 'std': float, 'min': float, 'max': float},
                'right_knee_valgus': {...},
                'pelvic_drop': {...},
                'cadence': {...},
                'n_videos': int,
                'total_frames': int
            }
            
            Per vista 'lateral':
            {
                'view_type': 'lateral',
                'overstriding': {'mean': float, 'std': float, 'min': float, 'max': float},
                'knee_flexion_ic': {...},
                'trunk_lean': {...},
                'ground_contact_time': {...},
                'n_videos': int,
                'total_frames': int
            }
        """
        logger.info(f"=== Creazione baseline da {len(videos_data)} video ===")
        
        # Determina il tipo di vista dal primo video
        view_type = videos_data[0].get('view_type', 'posterior')
        logger.info(f"Vista: {view_type}")
        
        # Aggrega tutti i dati in base al tipo di vista
        if view_type == 'posterior':
            all_left_valgus = []
            all_right_valgus = []
            all_pelvic_drop = []
            all_cadence = []
        else:  # lateral
            all_overstriding = []
            all_knee_flexion_ic = []
            all_trunk_lean = []
            all_gct = []
        
        total_frames = 0
        
        for video_data in videos_data:
            if view_type == 'posterior':
                all_left_valgus.extend(video_data['left_knee_valgus'])
                all_right_valgus.extend(video_data['right_knee_valgus'])
                all_pelvic_drop.extend(video_data['pelvic_drop'])
                
                # Per la cadenza, usa la media della serie temporale
                cadence_series = video_data.get('cadence', [])
                if cadence_series and len(cadence_series) > 0:
                    cadence_series_filtered = [c for c in cadence_series if c > 0]
                    if len(cadence_series_filtered) > 0:
                        cadence_mean = np.mean(cadence_series_filtered)
                        all_cadence.append(cadence_mean)
                    else:
                        all_cadence.append(video_data.get('avg_cadence', 0.0))
                else:
                    all_cadence.append(video_data.get('avg_cadence', 0.0))
            
            else:  # lateral
                all_overstriding.extend(video_data['overstriding'])
                all_knee_flexion_ic.extend(video_data['knee_flexion_ic'])
                all_trunk_lean.extend(video_data['trunk_lean'])
                
                # Per GCT, usa la media
                avg_gct = video_data.get('avg_gct', 0.0)
                all_gct.append(avg_gct)
            
            total_frames += video_data['n_frames']
        
        # Calcola statistiche in base al tipo di vista
        if view_type == 'posterior':
            # Converti in numpy array
            all_left_valgus = np.array(all_left_valgus)
            all_right_valgus = np.array(all_right_valgus)
            all_pelvic_drop = np.array(all_pelvic_drop)
            all_cadence = np.array(all_cadence)
            
            baseline_stats = {
                'view_type': 'posterior',
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
            
            logger.info("=== Statistiche Baseline (Vista Posteriore) ===")
            logger.info(f"Valgismo Ginocchio SX: μ={baseline_stats['left_knee_valgus']['mean']:.2f}° ± {baseline_stats['left_knee_valgus']['std']:.2f}°")
            logger.info(f"Valgismo Ginocchio DX: μ={baseline_stats['right_knee_valgus']['mean']:.2f}° ± {baseline_stats['right_knee_valgus']['std']:.2f}°")
            logger.info(f"Caduta Pelvica: μ={baseline_stats['pelvic_drop']['mean']:.2f}° ± {baseline_stats['pelvic_drop']['std']:.2f}°")
            logger.info(f"Cadenza: μ={baseline_stats['cadence']['mean']:.1f} ± {baseline_stats['cadence']['std']:.1f} spm")
        
        else:  # lateral
            # Converti in numpy array
            all_overstriding = np.array(all_overstriding)
            all_knee_flexion_ic = np.array(all_knee_flexion_ic)
            all_trunk_lean = np.array(all_trunk_lean)
            all_gct = np.array(all_gct)
            
            baseline_stats = {
                'view_type': 'lateral',
                'overstriding': {
                    'mean': float(np.mean(all_overstriding)),
                    'std': float(np.std(all_overstriding)),
                    'min': float(np.min(all_overstriding)),
                    'max': float(np.max(all_overstriding))
                },
                'knee_flexion_ic': {
                    'mean': float(np.mean(all_knee_flexion_ic)),
                    'std': float(np.std(all_knee_flexion_ic)),
                    'min': float(np.min(all_knee_flexion_ic)),
                    'max': float(np.max(all_knee_flexion_ic))
                },
                'trunk_lean': {
                    'mean': float(np.mean(all_trunk_lean)),
                    'std': float(np.std(all_trunk_lean)),
                    'min': float(np.min(all_trunk_lean)),
                    'max': float(np.max(all_trunk_lean))
                },
                'ground_contact_time': {
                    'mean': float(np.mean(all_gct)),
                    'std': float(np.std(all_gct)),
                    'min': float(np.min(all_gct)),
                    'max': float(np.max(all_gct))
                },
                'n_videos': len(videos_data),
                'total_frames': total_frames
            }
            
            logger.info("=== Statistiche Baseline (Vista Laterale) ===")
            logger.info(f"Overstriding: μ={baseline_stats['overstriding']['mean']:.4f} ± {baseline_stats['overstriding']['std']:.4f}")
            logger.info(f"Flessione Ginocchio @ IC: μ={baseline_stats['knee_flexion_ic']['mean']:.2f}° ± {baseline_stats['knee_flexion_ic']['std']:.2f}°")
            logger.info(f"Trunk Lean: μ={baseline_stats['trunk_lean']['mean']:.2f}° ± {baseline_stats['trunk_lean']['std']:.2f}°")
            logger.info(f"Ground Contact Time: μ={baseline_stats['ground_contact_time']['mean']:.3f}s ± {baseline_stats['ground_contact_time']['std']:.3f}s")
        
        return baseline_stats
    
    def calculate_z_scores(self, video_data: Dict, baseline_stats: Dict) -> Dict:
        """
        Calcola Z-Score per ogni metrica confrontando con baseline
        Z-Score = (Valore - MediaBaseline) / StdDevBaseline
        
        Args:
            video_data: Dati del video da analizzare (da process_video)
            baseline_stats: Statistiche baseline (da create_baseline_stats)
            
        Returns:
            Dizionario con Z-scores e livelli di anomalia.
            
            Per vista 'posterior':
            {
                'view_type': 'posterior',
                'left_knee_valgus': {'value': float, 'z_score': float, 'level': str, 'color': str},
                'right_knee_valgus': {...},
                'pelvic_drop': {...},
                'cadence': {...},
                'overall_status': 'Ottimale' | 'Attenzione' | 'Critico',
                'overall_color': str,
                'max_z_score': float
            }
            
            Per vista 'lateral':
            {
                'view_type': 'lateral',
                'overstriding': {'value': float, 'z_score': float, 'level': str, 'color': str},
                'knee_flexion_ic': {...},
                'trunk_lean': {...},
                'ground_contact_time': {...},
                'overall_status': 'Ottimale' | 'Attenzione' | 'Critico',
                'overall_color': str,
                'max_z_score': float
            }
        """
        logger.info("=== Calcolo Z-Scores ===")
        
        view_type = baseline_stats.get('view_type', 'posterior')
        logger.info(f"Vista: {view_type}")
        
        # Determina livelli per ogni metrica
        def get_level(z_score):
            abs_z = abs(z_score)
            if abs_z < 1.0:
                return 'Ottimale', '#10b981'  # Verde
            elif abs_z < 2.0:
                return 'Attenzione', '#f59e0b'  # Arancione
            else:
                return 'Critico', '#ef4444'  # Rosso
        
        if view_type == 'posterior':
            # Calcola valori medi dal video
            left_valgus_mean = np.mean(video_data['left_knee_valgus'])
            right_valgus_mean = np.mean(video_data['right_knee_valgus'])
            pelvic_drop_mean = np.mean(video_data['pelvic_drop'])
            
            # Per la cadenza, usa la media della serie temporale
            cadence_series = video_data.get('cadence', [])
            if cadence_series and len(cadence_series) > 0:
                cadence_series_filtered = [c for c in cadence_series if c > 0]
                if len(cadence_series_filtered) > 0:
                    cadence_value = np.mean(cadence_series_filtered)
                    logger.info(f"  Cadenza: usando media serie temporale = {cadence_value:.1f} spm")
                else:
                    cadence_value = video_data.get('avg_cadence', 0.0)
                    logger.warning(f"  Cadenza: serie temporale vuota, usando avg_cadence = {cadence_value:.1f} spm")
            else:
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
            
            level_left, color_left = get_level(z_left_valgus)
            level_right, color_right = get_level(z_right_valgus)
            level_pelvic, color_pelvic = get_level(z_pelvic_drop)
            level_cadence, color_cadence = get_level(z_cadence)
            
            # Determina stato generale
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
                'view_type': 'posterior',
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
        
        else:  # lateral
            # Calcola valori medi dal video
            overstriding_mean = np.mean(video_data['overstriding'])
            knee_flexion_ic_mean = np.mean(video_data['knee_flexion_ic'])
            trunk_lean_mean = np.mean(video_data['trunk_lean'])
            gct_value = video_data.get('avg_gct', 0.0)
            
            # Calcola Z-scores
            z_overstriding = (overstriding_mean - baseline_stats['overstriding']['mean']) / \
                            (baseline_stats['overstriding']['std'] + 1e-6)
            z_knee_flexion = (knee_flexion_ic_mean - baseline_stats['knee_flexion_ic']['mean']) / \
                            (baseline_stats['knee_flexion_ic']['std'] + 1e-6)
            z_trunk_lean = (trunk_lean_mean - baseline_stats['trunk_lean']['mean']) / \
                          (baseline_stats['trunk_lean']['std'] + 1e-6)
            z_gct = (gct_value - baseline_stats['ground_contact_time']['mean']) / \
                   (baseline_stats['ground_contact_time']['std'] + 1e-6)
            
            level_overstriding, color_overstriding = get_level(z_overstriding)
            level_knee_flexion, color_knee_flexion = get_level(z_knee_flexion)
            level_trunk_lean, color_trunk_lean = get_level(z_trunk_lean)
            level_gct, color_gct = get_level(z_gct)
            
            # Determina stato generale
            all_z_scores = [abs(z_overstriding), abs(z_knee_flexion), 
                           abs(z_trunk_lean), abs(z_gct)]
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
            
            logger.info(f"Z-Score Overstriding: {z_overstriding:.2f} -> {level_overstriding}")
            logger.info(f"Z-Score Flessione Ginocchio @ IC: {z_knee_flexion:.2f} -> {level_knee_flexion}")
            logger.info(f"Z-Score Trunk Lean: {z_trunk_lean:.2f} -> {level_trunk_lean}")
            logger.info(f"Z-Score Ground Contact Time: {z_gct:.2f} -> {level_gct}")
            logger.info(f"Stato Generale: {overall_status}")
            
            return {
                'view_type': 'lateral',
                'overstriding': {
                    'value': float(overstriding_mean),
                    'z_score': float(z_overstriding),
                    'level': level_overstriding,
                    'color': color_overstriding
                },
                'knee_flexion_ic': {
                    'value': float(knee_flexion_ic_mean),
                    'z_score': float(z_knee_flexion),
                    'level': level_knee_flexion,
                    'color': color_knee_flexion
                },
                'trunk_lean': {
                    'value': float(trunk_lean_mean),
                    'z_score': float(z_trunk_lean),
                    'level': level_trunk_lean,
                    'color': color_trunk_lean
                },
                'ground_contact_time': {
                    'value': float(gct_value),
                    'z_score': float(z_gct),
                    'level': level_gct,
                    'color': color_gct
                },
                'overall_status': overall_status,
                'overall_color': overall_color,
                'max_z_score': float(max_z)
            }

