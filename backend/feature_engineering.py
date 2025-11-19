"""
Modulo per il calcolo delle features biomeccaniche dai keypoint 3D
Ottimizzato per analisi della corsa da vista posteriore
Include metriche spazio-temporali e piano frontale avanzate
Ottimizzato con caching
"""
import numpy as np
from typing import Tuple, Dict, Optional
from gait_event_detection import GaitEventDetector
import os
import hashlib
import json
import logging
import time

# Logger per questo modulo
logger = logging.getLogger('FEATURE_ENGINEERING')


class BiomechanicalFeatures:
    """Classe per calcolare features biomeccaniche dai keypoint 3D per vista posteriore"""
    
    # Directory per cache
    CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache', 'features')
    
    # Indici dei landmark MediaPipe Pose
    NOSE = 0
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
    
    @staticmethod
    def calculate_angle_3d(point_a: np.ndarray, point_b: np.ndarray, point_c: np.ndarray) -> float:
        """
        Calcola l'angolo tra tre punti 3D (in gradi)
        
        Args:
            point_a: Primo punto [x, y, z]
            point_b: Punto centrale (vertice dell'angolo) [x, y, z]
            point_c: Terzo punto [x, y, z]
            
        Returns:
            Angolo in gradi
        """
        # Vettori dal punto centrale agli estremi
        vector_ba = point_a - point_b
        vector_bc = point_c - point_b
        
        # Calcola l'angolo usando il prodotto scalare
        cos_angle = np.dot(vector_ba, vector_bc) / (
            np.linalg.norm(vector_ba) * np.linalg.norm(vector_bc) + 1e-8
        )
        
        # Limita il valore tra -1 e 1 per evitare errori numerici
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        angle = np.arccos(cos_angle)
        return np.degrees(angle)
    
    @staticmethod
    def calculate_2d_angle_from_horizontal(point_a: np.ndarray, point_b: np.ndarray, plane: str = 'frontal') -> float:
        """
        Calcola l'angolo di una linea rispetto all'orizzontale in un piano specifico
        
        Args:
            point_a: Primo punto [x, y, z]
            point_b: Secondo punto [x, y, z]
            plane: Piano di proiezione ('frontal', 'sagittal')
            
        Returns:
            Angolo in gradi rispetto all'orizzontale
        """
        if plane == 'frontal':
            # Piano frontale: usiamo coordinate x (laterale) e y (verticale)
            dx = point_b[0] - point_a[0]
            dy = point_b[1] - point_a[1]
        elif plane == 'sagittal':
            # Piano sagittale: usiamo coordinate z (antero-posteriore) e y (verticale)
            dx = point_b[2] - point_a[2]
            dy = point_b[1] - point_a[1]
        else:
            raise ValueError(f"Piano non supportato: {plane}")
        
        angle = np.arctan2(dy, dx)
        return np.degrees(angle)
    
    def calculate_contralateral_pelvic_drop(self, keypoints: np.ndarray) -> float:
        """
        Calcola il Contralateral Pelvic Drop (CPD) - angolo della linea bi-iliaca rispetto all'orizzontale
        Ottimizzato per vista posteriore
        
        Args:
            keypoints: Array (33, 4) dei keypoint di un singolo frame
            
        Returns:
            Angolo in gradi (positivo = caduta pelvica controlaterale)
        """
        left_hip = keypoints[self.LEFT_HIP, :3]
        right_hip = keypoints[self.RIGHT_HIP, :3]
        
        # Calcola l'angolo della linea delle anche rispetto all'orizzontale nel piano frontale
        # Nel sistema di coordinate MediaPipe world: x=laterale, y=verticale, z=antero-posteriore
        # Per vista posteriore, guardiamo il piano frontale (x-y)
        dx = right_hip[0] - left_hip[0]  # Differenza laterale
        dy = right_hip[1] - left_hip[1]  # Differenza verticale
        
        # Angolo rispetto all'orizzontale (asse x)
        angle = np.arctan2(dy, abs(dx)) * 180 / np.pi
        
        return angle
    
    def calculate_base_of_support(self, keypoints: np.ndarray) -> float:
        """
        Calcola la Base of Support (BoS) - distanza mediolaterale tra le caviglie durante l'appoggio
        Ottimizzato per vista posteriore
        
        Args:
            keypoints: Array (33, 4) dei keypoint di un singolo frame
            
        Returns:
            Distanza in metri (sempre positiva)
        """
        left_ankle = keypoints[self.LEFT_ANKLE, :3]
        right_ankle = keypoints[self.RIGHT_ANKLE, :3]
        
        # Distanza mediolaterale (asse X nel sistema di coordinate world)
        # Le coordinate world sono in metri
        distance_x = abs(right_ankle[0] - left_ankle[0])
        
        return distance_x
    
    def calculate_rearfoot_eversion(self, keypoints: np.ndarray, side: str = 'left') -> float:
        """
        Calcola l'eversione del retropiede (angolo caviglia-tallone-punta piede)
        Ottimizzato per vista posteriore - piano frontale (assi Y-X)
        
        Args:
            keypoints: Array (33, 4) dei keypoint di un singolo frame
            side: 'left' o 'right'
            
        Returns:
            Angolo di eversione in gradi (positivo = eversione)
        """
        if side == 'left':
            ankle = keypoints[self.LEFT_ANKLE, :3]
            heel = keypoints[self.LEFT_HEEL, :3]
            foot_index = keypoints[self.LEFT_FOOT_INDEX, :3]
        else:
            ankle = keypoints[self.RIGHT_ANKLE, :3]
            heel = keypoints[self.RIGHT_HEEL, :3]
            foot_index = keypoints[self.RIGHT_FOOT_INDEX, :3]
        
        # Vettori nel piano frontale (Y-X)
        # Vettore caviglia-tallone
        vector_ankle_heel = np.array([heel[0] - ankle[0], heel[1] - ankle[1]])
        
        # Vettore caviglia-punta piede
        vector_ankle_index = np.array([foot_index[0] - ankle[0], foot_index[1] - ankle[1]])
        
        # Calcola l'angolo tra i due vettori nel piano frontale
        norm_heel = np.linalg.norm(vector_ankle_heel)
        norm_index = np.linalg.norm(vector_ankle_index)
        
        if norm_heel < 1e-6 or norm_index < 1e-6:
            return 0.0
        
        # Prodotto scalare nel piano frontale
        dot_product = np.dot(vector_ankle_heel, vector_ankle_index)
        cos_angle = dot_product / (norm_heel * norm_index)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        angle = np.arccos(cos_angle) * 180 / np.pi
        
        # Determina la direzione dell'eversione (positivo = eversione)
        # Cross product per determinare il verso
        cross = vector_ankle_heel[0] * vector_ankle_index[1] - vector_ankle_heel[1] * vector_ankle_index[0]
        if cross < 0:
            angle = -angle
        
        return angle
    
    def calculate_lateral_trunk_lean(self, keypoints: np.ndarray) -> float:
        """
        Calcola l'inclinazione laterale del tronco (Lateral Trunk Lean)
        Angolo formato dalla linea spalle-anche rispetto alla verticale
        Ottimizzato per vista posteriore
        
        Args:
            keypoints: Array (33, 4) dei keypoint di un singolo frame
            
        Returns:
            Angolo in gradi rispetto alla verticale (positivo = inclinazione laterale)
        """
        # Centro delle spalle
        left_shoulder = keypoints[self.LEFT_SHOULDER, :3]
        right_shoulder = keypoints[self.RIGHT_SHOULDER, :3]
        shoulder_center = (left_shoulder + right_shoulder) / 2
        
        # Centro delle anche
        left_hip = keypoints[self.LEFT_HIP, :3]
        right_hip = keypoints[self.RIGHT_HIP, :3]
        hip_center = (left_hip + right_hip) / 2
        
        # Vettore dal centro anche al centro spalle nel piano frontale
        dx = shoulder_center[0] - hip_center[0]  # Differenza laterale (asse X)
        dy = shoulder_center[1] - hip_center[1]  # Differenza verticale (asse Y)
        
        # Angolo rispetto alla verticale (asse Y)
        # atan2(dx, dy) dà l'angolo rispetto alla verticale
        angle = np.arctan2(dx, abs(dy)) * 180 / np.pi
        
        return angle
    
    def calculate_kasr(self, keypoints: np.ndarray) -> float:
        """
        Calcola il Knee-to-Ankle Separation Ratio (KASR)
        Rapporto tra distanza mediolaterale ginocchia e distanza mediolaterale caviglie
        Valori < 1.0 indicano valgismo
        
        NOTA: Questa funzione è attualmente NON USATA nel flusso principale.
        È disponibile per analisi future o estensioni del sistema.
        
        Args:
            keypoints: Array (33, 4) dei keypoint di un singolo frame
            
        Returns:
            Rapporto KASR (adimensionale)
        """
        left_knee = keypoints[self.LEFT_KNEE, :3]
        right_knee = keypoints[self.RIGHT_KNEE, :3]
        left_ankle = keypoints[self.LEFT_ANKLE, :3]
        right_ankle = keypoints[self.RIGHT_ANKLE, :3]
        
        # Distanza mediolaterale tra ginocchia (asse X)
        knee_separation = abs(right_knee[0] - left_knee[0])
        
        # Distanza mediolaterale tra caviglie (asse X)
        ankle_separation = abs(right_ankle[0] - left_ankle[0])
        
        # Evita divisione per zero
        if ankle_separation < 1e-6:
            return 1.0
        
        kasr = knee_separation / ankle_separation
        return kasr
    
    def calculate_fppa(self, keypoints: np.ndarray, side: str = 'left') -> float:
        """
        Calcola il Frontal Plane Projection Angle (FPPA)
        Angolo 2D formato da Anca-Ginocchio-Caviglia nel piano frontale (X-Y)
        
        NOTA: Questa funzione è attualmente NON USATA nel flusso principale.
        È disponibile per analisi future o estensioni del sistema.
        Il FPPA è stato rimosso dalle feature principali in favore di metriche più stabili.
        
        Args:
            keypoints: Array (33, 4) dei keypoint di un singolo frame
            side: 'left' o 'right'
            
        Returns:
            Angolo FPPA in gradi
        """
        if side == 'left':
            hip = keypoints[self.LEFT_HIP, :3]
            knee = keypoints[self.LEFT_KNEE, :3]
            ankle = keypoints[self.LEFT_ANKLE, :3]
        else:
            hip = keypoints[self.RIGHT_HIP, :3]
            knee = keypoints[self.RIGHT_KNEE, :3]
            ankle = keypoints[self.RIGHT_ANKLE, :3]
        
        # Proietta nel piano frontale (X-Y)
        hip_2d = np.array([hip[0], hip[1]])
        knee_2d = np.array([knee[0], knee[1]])
        ankle_2d = np.array([ankle[0], ankle[1]])
        
        # Vettori nel piano frontale
        vector_hip_knee = knee_2d - hip_2d
        vector_knee_ankle = ankle_2d - knee_2d
        
        # Calcola l'angolo tra i vettori
        norm_hip_knee = np.linalg.norm(vector_hip_knee)
        norm_knee_ankle = np.linalg.norm(vector_knee_ankle)
        
        if norm_hip_knee < 1e-6 or norm_knee_ankle < 1e-6:
            return 0.0
        
        dot_product = np.dot(vector_hip_knee, vector_knee_ankle)
        cos_angle = dot_product / (norm_hip_knee * norm_knee_ankle)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        angle = np.arccos(cos_angle) * 180 / np.pi
        
        # Determina il segno (valgismo = positivo)
        # Cross product per determinare se il ginocchio è medialmente deviato
        cross = vector_hip_knee[0] * vector_knee_ankle[1] - vector_hip_knee[1] * vector_knee_ankle[0]
        if cross < 0:
            angle = -angle
        
        return angle
    
    def _get_cache_path(self, keypoints_hash: str, fps: float) -> str:
        """Genera il percorso del file cache per le features"""
        cache_key = f"{keypoints_hash}_{fps}"
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
        return os.path.join(self.CACHE_DIR, f"{cache_hash}.npy")
    
    def _load_from_cache(self, cache_path: str) -> Optional[np.ndarray]:
        """Carica features dalla cache se disponibile"""
        if os.path.exists(cache_path):
            try:
                features = np.load(cache_path)
                logger.info(f"✓ Features caricate dalla cache: {os.path.basename(cache_path)}")
                logger.info(f"  Shape features: {features.shape}")
                return features
            except Exception as e:
                logger.warning(f"⚠ Errore nel caricare cache features: {e}")
        return None
    
    def _save_to_cache(self, features: np.ndarray, cache_path: str):
        """Salva features nella cache"""
        try:
            os.makedirs(self.CACHE_DIR, exist_ok=True)
            np.save(cache_path, features)
            logger.info(f"✓ Features salvate in cache: {os.path.basename(cache_path)}")
        except Exception as e:
            logger.warning(f"⚠ Errore nel salvare cache features: {e}")
    
    def _hash_keypoints(self, keypoints: np.ndarray) -> str:
        """Genera hash dei keypoints per identificazione cache (migliorato per evitare collisioni)"""
        # Usa shape, hash dei primi/last frame, e hash di frame campionati per robustezza
        keypoints_bytes = keypoints.tobytes()
        n_frames = keypoints.shape[0]
        
        # Campiona frame distribuiti uniformemente (primo, medio, ultimo)
        sample_indices = [0]
        if n_frames > 1:
            sample_indices.append(n_frames // 2)
        if n_frames > 2:
            sample_indices.append(n_frames - 1)
        
        # Estrai bytes dai frame campionati
        sample_bytes = b''
        for idx in sample_indices:
            frame_bytes = keypoints[idx].tobytes()
            sample_bytes += frame_bytes[:500]  # Primi 500 byte di ogni frame campionato
        
        # Combina shape, sample bytes, e hash completo per robustezza
        shape_str = f"{keypoints.shape[0]}_{keypoints.shape[1]}_{keypoints.shape[2]}"
        combined = shape_str.encode() + sample_bytes + keypoints_bytes[:2000] + keypoints_bytes[-2000:]
        
        return hashlib.md5(combined).hexdigest()
    
    def extract_all_features(self, keypoints_sequence: np.ndarray, 
                            gait_events: Optional[Dict] = None,
                            fps: float = 60.0, use_cache: bool = True) -> np.ndarray:
        """
        Estrae tutte le features biomeccaniche da una sequenza di keypoint
        Ottimizzato per analisi della corsa da vista posteriore con metriche avanzate
        
        Features estratte (per ogni frame):
        1. Contralateral Pelvic Drop (CPD) - gradi
        2. Base of Support (BoS) - metri
        3. Rearfoot Eversion (media sinistra e destra) - gradi
        4. Lateral Trunk Lean - gradi
        5. Ground Contact Time (GCT) - ms (interpolato per frame)
        6. Cadenza - passi/min (interpolato per frame)
        
        Args:
            keypoints_sequence: Array (n_frames, 33, 4) dei keypoint
            gait_events: Dizionario con eventi IC e FO (opzionale, per GCT e cadenza)
            fps: Frame per secondo del video
            
        Returns:
            Array (n_frames, 6) con tutte le features calcolate
        """
        start_time = time.time()
        logger.info(f"=== Inizio calcolo features biomeccaniche ===")
        logger.info(f"  Frame totali: {keypoints_sequence.shape[0]}, FPS: {fps:.2f}")
        
        # Controlla cache
        if use_cache:
            keypoints_hash = self._hash_keypoints(keypoints_sequence)
            cache_path = self._get_cache_path(keypoints_hash, fps)
            cached = self._load_from_cache(cache_path)
            if cached is not None:
                elapsed = time.time() - start_time
                logger.info(f"=== Calcolo features completato (da cache) in {elapsed:.2f}s ===")
                return cached
        
        n_frames = keypoints_sequence.shape[0]
        features = []
        
        # Calcola GCT e cadenza per frame se eventi disponibili
        gct_per_frame = None
        cadence_per_frame = None
        
        if gait_events is not None:
            # Verifica se ci sono eventi rilevati
            left_ic_count = len(gait_events.get('left', {}).get('ic', []))
            right_ic_count = len(gait_events.get('right', {}).get('ic', []))
            
            if left_ic_count == 0 and right_ic_count == 0:
                # Nessun evento rilevato: usa valori default realistici
                logger.warning("⚠️ Nessun evento del passo rilevato, uso valori default per GCT e cadenza")
                logger.warning("   GCT default: 250.0 ms, Cadenza default: 175.0 passi/min")
                gct_per_frame = np.full(n_frames, 250.0)  # 250ms default GCT
                cadence_per_frame = np.full(n_frames, 175.0)  # 175 passi/min default
            else:
                logger.info(f"  Calcolo GCT e cadenza da {left_ic_count + right_ic_count} eventi IC...")
                gct_per_frame = self._calculate_gct_per_frame(gait_events, n_frames, fps)
                cadence_per_frame = self._calculate_cadence_per_frame(gait_events, n_frames, fps)
                logger.info(f"  GCT medio: {np.mean(gct_per_frame):.1f} ms, Cadenza media: {np.mean(cadence_per_frame):.1f} passi/min")
        
        for frame_idx in range(n_frames):
            frame_keypoints = keypoints_sequence[frame_idx]
            
            # Calcola tutte le features per questo frame
            cpd = self.calculate_contralateral_pelvic_drop(frame_keypoints)
            bos = self.calculate_base_of_support(frame_keypoints)
            eversion_left = self.calculate_rearfoot_eversion(frame_keypoints, side='left')
            eversion_right = self.calculate_rearfoot_eversion(frame_keypoints, side='right')
            eversion_avg = (eversion_left + eversion_right) / 2.0
            trunk_lean = self.calculate_lateral_trunk_lean(frame_keypoints)
            
            # GCT e cadenza (interpolati o default)
            gct = gct_per_frame[frame_idx] if gct_per_frame is not None else 0.0
            cadence = cadence_per_frame[frame_idx] if cadence_per_frame is not None else 0.0
            
            frame_features = [
                cpd,           # 0: Contralateral Pelvic Drop (gradi)
                bos,           # 1: Base of Support (metri)
                eversion_avg,  # 2: Rearfoot Eversion media (gradi)
                trunk_lean,    # 3: Lateral Trunk Lean (gradi)
                gct,           # 4: Ground Contact Time (ms)
                cadence        # 5: Cadenza (passi/min)
            ]
            
            features.append(frame_features)
        
        features_array = np.array(features)
        elapsed_time = time.time() - start_time
        
        # Log statistiche per ogni feature
        logger.info(f"=== Statistiche features calcolate ===")
        feature_names = ['CPD', 'BoS', 'Rearfoot Eversion', 'Lateral Trunk Lean', 'GCT', 'Cadence']
        units = ['°', 'm', '°', '°', 'ms', 'passi/min']
        
        for idx, (name, unit) in enumerate(zip(feature_names, units)):
            feature_values = features_array[:, idx]
            valid_values = feature_values[np.isfinite(feature_values)]
            if len(valid_values) > 0:
                mean_val = np.mean(valid_values)
                min_val = np.min(valid_values)
                max_val = np.max(valid_values)
                std_val = np.std(valid_values)
                logger.info(f"  {name}: mean={mean_val:.2f}{unit}, min={min_val:.2f}{unit}, max={max_val:.2f}{unit}, std={std_val:.2f}{unit}")
            else:
                logger.warning(f"  {name}: Nessun valore valido calcolato")
        
        logger.info(f"  Frame utilizzati: {n_frames}")
        logger.info(f"  Shape output: {features_array.shape}")
        logger.info(f"  Tempo totale elaborazione: {elapsed_time:.2f}s")
        logger.info(f"=== Calcolo features completato ===")
        
        # Salva in cache
        if use_cache:
            keypoints_hash = self._hash_keypoints(keypoints_sequence)
            cache_path = self._get_cache_path(keypoints_hash, fps)
            self._save_to_cache(features_array, cache_path)
        
        return features_array
    
    def _calculate_gct_per_frame(self, gait_events: Dict, n_frames: int, fps: float) -> np.ndarray:
        """
        Calcola GCT per ogni frame interpolando dagli eventi
        
        Args:
            gait_events: Dizionario con eventi IC e FO
            n_frames: Numero di frame totali
            fps: Frame per secondo
            
        Returns:
            Array (n_frames,) con GCT in ms per ogni frame
        """
        gct_array = np.zeros(n_frames)
        
        # Calcola GCT per ogni ciclo di falcata
        detector = GaitEventDetector(fps=fps)
        
        for side in ['left', 'right']:
            gct_list = detector.calculate_gct(gait_events, side=side)
            side_events = gait_events[side]
            ic_frames = side_events['ic']
            fo_frames = side_events['fo']
            
            # Per ogni ciclo, assegna il GCT ai frame tra IC e FO
            for i, ic in enumerate(ic_frames):
                if i < len(gct_list):
                    fo_after_ic = [fo for fo in fo_frames if fo > ic]
                    if fo_after_ic:
                        fo = min(fo_after_ic)
                        gct_value = gct_list[i]
                        # Assegna GCT ai frame tra IC e FO
                        for frame_idx in range(ic, min(fo + 1, n_frames)):
                            if gct_array[frame_idx] == 0:  # Non sovrascrivere se già assegnato
                                gct_array[frame_idx] = gct_value
        
        # Interpola i valori mancanti
        if np.any(gct_array > 0):
            # Usa interpolazione lineare per i frame senza GCT
            valid_indices = np.where(gct_array > 0)[0]
            if len(valid_indices) > 1:
                try:
                    from scipy.interpolate import interp1d
                    interp_func = interp1d(valid_indices, gct_array[valid_indices], 
                                         kind='linear', fill_value='extrapolate')
                    all_indices = np.arange(n_frames)
                    gct_array = interp_func(all_indices)
                except (ImportError, Exception):
                    # Fallback: usa media mobile se scipy non disponibile o errore
                    gct_array = self._interpolate_with_mean(gct_array)
        
        return gct_array
    
    def _calculate_cadence_per_frame(self, gait_events: Dict, n_frames: int, fps: float) -> np.ndarray:
        """
        Calcola cadenza per ogni frame interpolando dagli eventi
        
        Args:
            gait_events: Dizionario con eventi IC e FO
            n_frames: Numero di frame totali
            fps: Frame per secondo
            
        Returns:
            Array (n_frames,) con cadenza in passi/min per ogni frame
        """
        cadence_array = np.zeros(n_frames)
        
        detector = GaitEventDetector(fps=fps)
        
        # Calcola cadenza da stride time
        for side in ['left', 'right']:
            stride_times = detector.calculate_stride_time(gait_events, side=side)
            side_events = gait_events[side]
            ic_frames = side_events['ic']
            
            # Calcola cadenza per ogni stride
            for i in range(len(stride_times)):
                if i < len(ic_frames) - 1:
                    stride_time_ms = stride_times[i]
                    if stride_time_ms > 0:
                        # Cadenza = 60000 / stride_time_ms (passi/min)
                        cadence = 60000.0 / stride_time_ms
                        
                        # Assegna cadenza ai frame di questo stride
                        start_frame = ic_frames[i]
                        end_frame = ic_frames[i+1] if i+1 < len(ic_frames) else n_frames
                        for frame_idx in range(start_frame, min(end_frame, n_frames)):
                            if cadence_array[frame_idx] == 0:
                                cadence_array[frame_idx] = cadence
        
        # Interpola i valori mancanti
        if np.any(cadence_array > 0):
            valid_indices = np.where(cadence_array > 0)[0]
            if len(valid_indices) > 1:
                try:
                    from scipy.interpolate import interp1d
                    interp_func = interp1d(valid_indices, cadence_array[valid_indices],
                                         kind='linear', fill_value='extrapolate')
                    all_indices = np.arange(n_frames)
                    cadence_array = interp_func(all_indices)
                except (ImportError, Exception):
                    # Fallback: usa media mobile se scipy non disponibile o errore
                    cadence_array = self._interpolate_with_mean(cadence_array)
        
        return cadence_array
    
    def _interpolate_with_mean(self, array: np.ndarray) -> np.ndarray:
        """Interpola valori mancanti usando media mobile"""
        result = array.copy()
        valid_mask = array > 0
        
        if np.any(valid_mask):
            mean_value = np.mean(array[valid_mask])
            result[~valid_mask] = mean_value
        
        return result

