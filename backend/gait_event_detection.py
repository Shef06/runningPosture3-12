"""
Modulo per il rilevamento degli eventi del passo (Gait Event Detection)
Ottimizzato per vista posteriore usando coordinate 3D MediaPipe
"""
import numpy as np
from typing import List, Tuple, Dict
import logging

# Logger per questo modulo
logger = logging.getLogger('GAIT_EVENT_DETECTION')

# Importa scipy solo se disponibile (opzionale)
try:
    from scipy import signal
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


class GaitEventDetector:
    """Classe per rilevare Initial Contact (IC) e Foot Off (FO) da pose_world_landmarks"""
    
    # Indici dei landmark MediaPipe Pose
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_HEEL = 29
    RIGHT_HEEL = 30
    LEFT_FOOT_INDEX = 31
    RIGHT_FOOT_INDEX = 32
    
    def __init__(self, fps: float = 60.0, min_contact_duration: float = 0.1):
        """
        Inizializza il detector
        
        Args:
            fps: Frame per secondo del video
            min_contact_duration: Durata minima del contatto al suolo in secondi
        """
        self.fps = fps
        self.min_contact_frames = int(min_contact_duration * fps)
    
    def detect_events(self, keypoints_sequence: np.ndarray) -> Dict:
        """
        Rileva gli eventi del passo (IC e FO) per entrambi i piedi
        
        Args:
            keypoints_sequence: Array (n_frames, 33, 4) dei keypoint
            
        Returns:
            Dizionario con eventi per piede sinistro e destro:
            {
                'left': {'ic': [frame_indices], 'fo': [frame_indices]},
                'right': {'ic': [frame_indices], 'fo': [frame_indices]}
            }
        """
        n_frames = keypoints_sequence.shape[0]
        logger.info(f"=== Inizio rilevamento eventi del passo ===")
        logger.info(f"  Frame totali: {n_frames}, FPS: {self.fps:.2f}")
        
        # Estrai coordinate Z (profondità) per talloni e caviglie
        left_heel_z = keypoints_sequence[:, self.LEFT_HEEL, 2]  # Coordinata Z del tallone sinistro
        right_heel_z = keypoints_sequence[:, self.RIGHT_HEEL, 2]
        left_ankle_z = keypoints_sequence[:, self.LEFT_ANKLE, 2]
        right_ankle_z = keypoints_sequence[:, self.RIGHT_ANKLE, 2]
        
        # Usa la media tra tallone e caviglia per maggiore robustezza
        left_foot_z = (left_heel_z + left_ankle_z) / 2.0
        right_foot_z = (right_heel_z + right_ankle_z) / 2.0
        
        # Rileva eventi per entrambi i piedi
        logger.info(f"  Rilevamento eventi piede sinistro...")
        left_events = self._detect_foot_events(left_foot_z, side='left')
        logger.info(f"  Rilevamento eventi piede destro...")
        right_events = self._detect_foot_events(right_foot_z, side='right')
        
        # Log statistiche eventi
        left_ic_count = len(left_events['ic'])
        left_fo_count = len(left_events['fo'])
        right_ic_count = len(right_events['ic'])
        right_fo_count = len(right_events['fo'])
        
        logger.info(f"=== Statistiche eventi rilevati ===")
        logger.info(f"  Piedi sinistro: IC={left_ic_count}, FO={left_fo_count}")
        logger.info(f"  Piedi destro: IC={right_ic_count}, FO={right_fo_count}")
        logger.info(f"  Totale IC: {left_ic_count + right_ic_count}, Totale FO: {left_fo_count + right_fo_count}")
        
        # Calcola tempi medi di contatto se disponibili
        if left_ic_count > 0 and left_fo_count > 0:
            gct_left = self.calculate_gct({'left': left_events, 'right': right_events}, side='left')
            if len(gct_left) > 0:
                avg_gct_left = np.mean(gct_left)
                logger.info(f"  GCT medio piede sinistro: {avg_gct_left:.1f} ms")
        
        if right_ic_count > 0 and right_fo_count > 0:
            gct_right = self.calculate_gct({'left': left_events, 'right': right_events}, side='right')
            if len(gct_right) > 0:
                avg_gct_right = np.mean(gct_right)
                logger.info(f"  GCT medio piede destro: {avg_gct_right:.1f} ms")
        
        # Warning se pochi eventi rilevati
        if left_ic_count < 3 or right_ic_count < 3:
            logger.warning(f"⚠️ Pochi eventi IC rilevati (sinistro={left_ic_count}, destro={right_ic_count})")
            logger.warning(f"   Potrebbe indicare problemi nella rilevazione o video troppo breve")
        
        logger.info(f"=== Rilevamento eventi completato ===")
        
        return {
            'left': left_events,
            'right': right_events
        }
    
    def _detect_foot_events(self, foot_z: np.ndarray, side: str = 'left') -> Dict:
        """
        Rileva IC e FO per un singolo piede analizzando la coordinata Z
        
        Metodo: Analizza la velocità lungo l'asse Z e i punti di inversione
        
        Args:
            foot_z: Array (n_frames,) con coordinate Z del piede
            side: 'left' o 'right'
            
        Returns:
            Dizionario con liste di frame indices per IC e FO
        """
        n_frames = len(foot_z)
        
        # Calcola la velocità lungo Z (derivata prima)
        # Usa differenza finita centrata per maggiore stabilità
        velocity_z = np.gradient(foot_z)
        
        # Calcola l'accelerazione (derivata seconda)
        acceleration_z = np.gradient(velocity_z)
        
        # Filtra il rumore con un filtro passa-basso
        # Usa filtro Butterworth per smoothing se scipy disponibile
        if SCIPY_AVAILABLE:
            try:
                from scipy.signal import butter, filtfilt
                b, a = butter(3, 0.1, btype='low')
                velocity_z_filtered = filtfilt(b, a, velocity_z)
                acceleration_z_filtered = filtfilt(b, a, acceleration_z)
            except:
                # Fallback: smoothing semplice se filtro fallisce
                window_size = max(3, int(self.fps * 0.05))  # ~5% del secondo
                velocity_z_filtered = self._simple_smooth(velocity_z, window_size)
                acceleration_z_filtered = self._simple_smooth(acceleration_z, window_size)
        else:
            # Fallback: smoothing semplice se scipy non disponibile
            window_size = max(3, int(self.fps * 0.05))  # ~5% del secondo
            velocity_z_filtered = self._simple_smooth(velocity_z, window_size)
            acceleration_z_filtered = self._simple_smooth(acceleration_z, window_size)
        
        # Trova i punti di inversione della velocità
        # IC: quando la velocità Z cambia da positiva a negativa (piede si ferma/contatta)
        # FO: quando la velocità Z cambia da negativa a positiva (piede si solleva)
        
        ic_frames = []
        fo_frames = []
        
        # Trova zero crossings nella velocità (cambi di direzione)
        for i in range(1, n_frames - 1):
            # Initial Contact: velocità passa da positiva a negativa
            # (piede si muoveva in avanti, ora si ferma/contatta)
            if velocity_z_filtered[i-1] > 0 and velocity_z_filtered[i] <= 0:
                # Verifica che l'accelerazione sia negativa (decelerazione)
                if acceleration_z_filtered[i] < 0:
                    ic_frames.append(i)
            
            # Foot Off: velocità passa da negativa a positiva
            # (piede era fermo/contattava, ora si solleva)
            elif velocity_z_filtered[i-1] < 0 and velocity_z_filtered[i] >= 0:
                # Verifica che l'accelerazione sia positiva (accelerazione)
                if acceleration_z_filtered[i] > 0:
                    fo_frames.append(i)
        
        # Filtra eventi troppo vicini (durata contatto minima)
        ic_before_filter = len(ic_frames)
        fo_before_filter = len(fo_frames)
        ic_frames = self._filter_close_events(ic_frames, fo_frames, min_duration=self.min_contact_frames)
        fo_frames = self._filter_close_events(fo_frames, ic_frames, min_duration=self.min_contact_frames)
        
        # Ordina e rimuovi duplicati
        ic_frames = sorted(list(set(ic_frames)))
        fo_frames = sorted(list(set(fo_frames)))
        
        # Log filtraggio
        if ic_before_filter != len(ic_frames) or fo_before_filter != len(fo_frames):
            logger.info(f"  Filtro eventi {side}: IC {ic_before_filter}→{len(ic_frames)}, FO {fo_before_filter}→{len(fo_frames)}")
        
        return {
            'ic': ic_frames,
            'fo': fo_frames
        }
    
    def _simple_smooth(self, data: np.ndarray, window_size: int) -> np.ndarray:
        """Smoothing semplice con media mobile"""
        if window_size < 3:
            return data
        
        smoothed = np.zeros_like(data)
        half_window = window_size // 2
        
        for i in range(len(data)):
            start = max(0, i - half_window)
            end = min(len(data), i + half_window + 1)
            smoothed[i] = np.mean(data[start:end])
        
        return smoothed
    
    def _filter_close_events(self, events: List[int], other_events: List[int], min_duration: int) -> List[int]:
        """
        Filtra eventi troppo vicini ad altri eventi
        
        Args:
            events: Lista di frame indices da filtrare
            other_events: Lista di altri eventi da usare come riferimento
            min_duration: Durata minima in frame tra eventi
            
        Returns:
            Lista filtrata di eventi
        """
        if not events or not other_events:
            return events
        
        filtered = []
        for event in events:
            # Verifica che non ci siano altri eventi troppo vicini
            too_close = False
            for other in other_events:
                if abs(event - other) < min_duration:
                    too_close = True
                    break
            
            if not too_close:
                filtered.append(event)
        
        return filtered
    
    def calculate_gct(self, events: Dict, side: str = 'left') -> List[float]:
        """
        Calcola Ground Contact Time (GCT) per ogni ciclo di falcata
        
        Args:
            events: Dizionario con eventi IC e FO
            side: 'left' o 'right'
            
        Returns:
            Lista di GCT in millisecondi per ogni ciclo
        """
        side_events = events[side]
        ic_frames = side_events['ic']
        fo_frames = side_events['fo']
        
        gct_list = []
        
        # Per ogni IC, trova il FO successivo
        for ic in ic_frames:
            # Trova il FO più vicino dopo questo IC
            fo_after_ic = [fo for fo in fo_frames if fo > ic]
            
            if fo_after_ic:
                fo = min(fo_after_ic)
                gct_frames = fo - ic
                gct_ms = (gct_frames / self.fps) * 1000.0  # Converti in millisecondi
                gct_list.append(gct_ms)
        
        return gct_list
    
    def calculate_stride_time(self, events: Dict, side: str = 'left') -> List[float]:
        """
        Calcola il tempo di falcata (da IC a IC successivo)
        
        Args:
            events: Dizionario con eventi IC e FO
            side: 'left' o 'right'
            
        Returns:
            Lista di tempi di falcata in millisecondi
        """
        side_events = events[side]
        ic_frames = sorted(side_events['ic'])
        
        stride_times = []
        
        for i in range(len(ic_frames) - 1):
            stride_frames = ic_frames[i+1] - ic_frames[i]
            stride_time_ms = (stride_frames / self.fps) * 1000.0
            stride_times.append(stride_time_ms)
        
        return stride_times

