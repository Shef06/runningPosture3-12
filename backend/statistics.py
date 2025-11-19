"""
Modulo per il calcolo di statistiche e metriche aggregate
Centralizza tutti i calcoli statistici per evitare duplicazioni
"""
import numpy as np
from typing import Dict, List, Optional, Tuple


def calculate_stats(values: np.ndarray) -> Dict[str, float]:
    """
    Calcola statistiche complete (mean, min, max, std) per un array di valori
    
    Args:
        values: Array numpy di valori
        
    Returns:
        Dizionario con mean, min, max, std
    """
    if len(values) == 0:
        return {'mean': 0.0, 'min': 0.0, 'max': 0.0, 'std': 0.0}
    
    # Filtra NaN e Inf
    valid_values = values[np.isfinite(values)]
    
    if len(valid_values) == 0:
        return {'mean': 0.0, 'min': 0.0, 'max': 0.0, 'std': 0.0}
    
    mean = float(np.mean(valid_values))
    min_val = float(np.min(valid_values))
    max_val = float(np.max(valid_values))
    std = float(np.std(valid_values))
    
    return {
        'mean': mean,
        'min': min_val,
        'max': max_val,
        'std': std
    }


def calculate_biomechanical_stats_from_keypoints(keypoints: np.ndarray) -> Dict:
    """
    Calcola statistiche per metriche biomeccaniche legacy dai keypoint
    (angoli ginocchio, pelvic drop, trunk inclination)
    
    Args:
        keypoints: Array (n_frames, 33, 4) dei keypoint
        
    Returns:
        Dizionario con statistiche per ogni metrica
    """
    from feature_engineering import BiomechanicalFeatures
    
    feature_extractor = BiomechanicalFeatures()
    n_frames = keypoints.shape[0]
    
    # Indici landmark
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    
    left_knee_angles = []
    right_knee_angles = []
    pelvic_drops = []
    trunk_inclinations = []
    
    for frame_idx in range(n_frames):
        frame_keypoints = keypoints[frame_idx]
        
        # Angoli ginocchio
        left_hip = frame_keypoints[LEFT_HIP, :3]
        left_knee = frame_keypoints[LEFT_KNEE, :3]
        left_ankle = frame_keypoints[LEFT_ANKLE, :3]
        right_hip = frame_keypoints[RIGHT_HIP, :3]
        right_knee = frame_keypoints[RIGHT_KNEE, :3]
        right_ankle = frame_keypoints[RIGHT_ANKLE, :3]
        
        left_knee_angle = BiomechanicalFeatures.calculate_angle_3d(left_hip, left_knee, left_ankle)
        right_knee_angle = BiomechanicalFeatures.calculate_angle_3d(right_hip, right_knee, right_ankle)
        
        left_knee_angles.append(left_knee_angle)
        right_knee_angles.append(right_knee_angle)
        
        # Pelvic drop (differenza verticale tra anche)
        pelvic_drop = abs(left_hip[1] - right_hip[1])
        pelvic_drops.append(pelvic_drop)
        
        # Trunk inclination
        left_shoulder = frame_keypoints[LEFT_SHOULDER, :3]
        right_shoulder = frame_keypoints[RIGHT_SHOULDER, :3]
        shoulder_center = (left_shoulder + right_shoulder) / 2
        hip_center = (left_hip + right_hip) / 2
        
        trunk_lean = feature_extractor.calculate_lateral_trunk_lean(frame_keypoints)
        trunk_inclinations.append(trunk_lean)
    
    return {
        'leftKneeAngle': calculate_stats(np.array(left_knee_angles)),
        'rightKneeAngle': calculate_stats(np.array(right_knee_angles)),
        'pelvicDrop': calculate_stats(np.array(pelvic_drops)),
        'trunkInclination': calculate_stats(np.array(trunk_inclinations))
    }


def calculate_all_feature_stats(features: np.ndarray) -> Dict:
    """
    Calcola statistiche complete per tutte le feature
    
    Args:
        features: Array (n_frames, 6) con features [cpd, bos, eversion, trunk_lean, gct, cadence]
        
    Returns:
        Dizionario con statistiche per ogni feature
    """
    return {
        'cpd': calculate_stats(features[:, 0]),
        'bos': calculate_stats(features[:, 1]),
        'rearfoot_eversion': calculate_stats(features[:, 2]),
        'lateral_trunk_lean': calculate_stats(features[:, 3]),
        'gct': calculate_stats(features[:, 4]),
        'cadence': calculate_stats(features[:, 5])
    }


def format_statistics_for_frontend(stats: Dict, unit: str = '', decimals: int = 2) -> Dict:
    """
    Formatta le statistiche per il frontend (arrotondamento e unità)
    
    Args:
        stats: Dizionario con mean, min, max, std
        unit: Unità di misura (es. '°', 'ms', 'm')
        decimals: Numero di decimali
        
    Returns:
        Dizionario formattato
    """
    return {
        'mean': round(stats['mean'], decimals),
        'min': round(stats['min'], decimals),
        'max': round(stats['max'], decimals),
        'std': round(stats['std'], decimals),
        'unit': unit
    }

