"""
Modulo per il calcolo di metriche di stabilità (Variabilità e Asimmetria)
"""
import numpy as np
from typing import List, Dict, Optional
from gait_event_detection import GaitEventDetector


class StabilityMetrics:
    """Classe per calcolare metriche di variabilità e asimmetria"""
    
    def __init__(self, fps: float = 60.0):
        """
        Inizializza il calcolatore di metriche di stabilità
        
        Args:
            fps: Frame per secondo del video
        """
        self.fps = fps
        self.detector = GaitEventDetector(fps=fps)
    
    def calculate_variability(self, gait_events: Dict, 
                             metric_values: Optional[np.ndarray] = None) -> Dict:
        """
        Calcola la variabilità stride-to-stride usando Coefficiente di Variazione (CV)
        
        Args:
            gait_events: Dizionario con eventi IC e FO
            metric_values: Array opzionale con valori di una metrica per frame
            
        Returns:
            Dizionario con CV per diverse metriche
        """
        variability = {}
        
        # Variabilità GCT
        gct_left = self.detector.calculate_gct(gait_events, side='left')
        gct_right = self.detector.calculate_gct(gait_events, side='right')
        gct_all = gct_left + gct_right
        
        if len(gct_all) > 1:
            variability['gct_cv'] = self._coefficient_of_variation(gct_all)
        else:
            variability['gct_cv'] = 0.0
        
        # Variabilità Stride Time
        stride_time_left = self.detector.calculate_stride_time(gait_events, side='left')
        stride_time_right = self.detector.calculate_stride_time(gait_events, side='right')
        stride_time_all = stride_time_left + stride_time_right
        
        if len(stride_time_all) > 1:
            variability['stride_time_cv'] = self._coefficient_of_variation(stride_time_all)
        else:
            variability['stride_time_cv'] = 0.0
        
        return variability
    
    def calculate_asymmetry(self, gait_events: Dict,
                           cpd_values: Optional[np.ndarray] = None,
                           fppa_values: Optional[np.ndarray] = None) -> Dict:
        """
        Calcola l'asimmetria bilaterale usando Symmetry Index (SI) e Symmetry Angle (SA)
        
        Args:
            gait_events: Dizionario con eventi IC e FO
            cpd_values: Array opzionale con valori CPD per frame
            fppa_values: Array opzionale con valori FPPA per frame
            
        Returns:
            Dizionario con metriche di asimmetria
        """
        asymmetry = {}
        
        # Asimmetria GCT (usando SI)
        gct_left = self.detector.calculate_gct(gait_events, side='left')
        gct_right = self.detector.calculate_gct(gait_events, side='right')
        
        if len(gct_left) > 0 and len(gct_right) > 0:
            gct_left_mean = np.mean(gct_left)
            gct_right_mean = np.mean(gct_right)
            asymmetry['gct_si'] = self._symmetry_index(gct_left_mean, gct_right_mean)
        else:
            asymmetry['gct_si'] = 0.0
        
        # Asimmetria CPD (usando SA se disponibile)
        if cpd_values is not None and len(cpd_values) > 0:
            # Calcola CPD medio per lato durante i cicli
            # Per semplicità, usiamo la media globale e assumiamo che valori positivi
            # indichino caduta pelvica controlaterale
            cpd_mean = np.mean(cpd_values)
            # Per SA, abbiamo bisogno di valori separati per lato
            # Usiamo un'approssimazione basata sulla variabilità
            cpd_std = np.std(cpd_values)
            # SA approssimato: maggiore variabilità = maggiore asimmetria
            asymmetry['cpd_sa'] = min(100.0, (cpd_std / (abs(cpd_mean) + 1e-6)) * 100.0)
        else:
            asymmetry['cpd_sa'] = 0.0
        
        # Asimmetria FPPA (usando SA se disponibile)
        if fppa_values is not None and len(fppa_values) > 0:
            fppa_mean = np.mean(fppa_values)
            fppa_std = np.std(fppa_values)
            asymmetry['fppa_sa'] = min(100.0, (fppa_std / (abs(fppa_mean) + 1e-6)) * 100.0)
        else:
            asymmetry['fppa_sa'] = 0.0
        
        return asymmetry
    
    @staticmethod
    def _coefficient_of_variation(values: List[float]) -> float:
        """
        Calcola il Coefficiente di Variazione (CV)
        
        Formula: CV = (Deviazione Standard / Media) * 100
        
        Args:
            values: Lista di valori
            
        Returns:
            CV in percentuale
        """
        if len(values) == 0:
            return 0.0
        
        values_array = np.array(values)
        mean = np.mean(values_array)
        
        if abs(mean) < 1e-6:
            return 0.0
        
        std = np.std(values_array)
        cv = (std / abs(mean)) * 100.0
        
        return float(cv)
    
    @staticmethod
    def _symmetry_index(left_value: float, right_value: float) -> float:
        """
        Calcola il Symmetry Index (SI) per metriche scalari
        
        Formula: SI = abs(X_dx - X_sx) / (0.5 * (X_dx + X_sx)) * 100
        
        Args:
            left_value: Valore per lato sinistro
            right_value: Valore per lato destro
            
        Returns:
            SI in percentuale
        """
        if abs(left_value) < 1e-6 and abs(right_value) < 1e-6:
            return 0.0
        
        mean_value = 0.5 * (left_value + right_value)
        
        if abs(mean_value) < 1e-6:
            return 0.0
        
        si = (abs(right_value - left_value) / abs(mean_value)) * 100.0
        
        return float(si)
    
    @staticmethod
    def _symmetry_angle(left_value: float, right_value: float) -> float:
        """
        Calcola il Symmetry Angle (SA) per metriche angolari
        
        Formula: SA = abs(45° - arctan(X_sx / X_dx)) / 90 * 100
        
        Args:
            left_value: Valore per lato sinistro
            right_value: Valore per lato destro
            
        Returns:
            SA in percentuale
        """
        if abs(right_value) < 1e-6:
            return 0.0
        
        ratio = left_value / right_value
        angle_rad = np.arctan(ratio)
        angle_deg = np.degrees(angle_rad)
        
        sa = (abs(45.0 - angle_deg) / 90.0) * 100.0
        
        return float(sa)







