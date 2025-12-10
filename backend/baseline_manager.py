"""
Modulo per gestione Baseline Incrementale con Persistenza Storica
Permette di migliorare progressivamente la baseline aggiungendo corse buone nel tempo
"""
import json
import os
import logging
import shutil
from datetime import datetime
from typing import Dict, Optional, List
import numpy as np

logger = logging.getLogger('BASELINE_MANAGER')


class BaselineHistory:
    """
    Gestisce lo storico delle baseline e l'aggiornamento incrementale
    Salva un file JSON con statistiche globali e riferimenti alla migliore corsa
    """
    
    def __init__(self, history_file_path: str, ghost_frames_folder: str):
        """
        Inizializza il BaselineHistory
        
        Args:
            history_file_path: Percorso del file baseline_history.json
            ghost_frames_folder: Cartella per i ghost frames
        """
        self.history_file_path = history_file_path
        self.ghost_frames_folder = ghost_frames_folder
        self.history_data = None
        
    def load(self) -> Dict:
        """
        Carica lo storico della baseline dal file JSON
        Se il file non esiste, crea una struttura vuota
        
        Returns:
            Dizionario con lo storico della baseline
        """
        if os.path.exists(self.history_file_path):
            try:
                with open(self.history_file_path, 'r') as f:
                    self.history_data = json.load(f)
                logger.info(f"✓ Baseline history caricato: {self.history_file_path}")
                logger.info(f"  Corse totali: {self.history_data.get('run_count', 0)}")
                logger.info(f"  Best run ID: {self.history_data.get('best_run_id', 'N/A')}")
                return self.history_data
            except Exception as e:
                logger.error(f"❌ Errore nel caricare baseline history: {e}")
                return self._create_empty_history()
        else:
            logger.info("📝 Baseline history non trovato, creazione nuovo...")
            return self._create_empty_history()
    
    def _create_empty_history(self) -> Dict:
        """Crea una struttura vuota per lo storico della baseline"""
        self.history_data = {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'run_count': 0,
            'best_run_id': None,
            'best_run_error': float('inf'),
            'view_type': None,
            'speed_kmh': None,
            'fps': None,
            'global_stats': {},
            'runs_history': []
        }
        return self.history_data
    
    def _calculate_run_error(self, metrics: Dict, view_type: str) -> float:
        """
        Calcola un punteggio di errore totale per una corsa
        Usa i Z-scores assoluti come misura dell'errore
        
        Args:
            metrics: Dizionario con le metriche della corsa
            view_type: Tipo di vista ('posterior' o 'lateral')
            
        Returns:
            Punteggio di errore totale (più basso = migliore)
        """
        total_error = 0.0
        count = 0
        
        if view_type == 'posterior':
            metric_keys = ['left_knee_valgus', 'right_knee_valgus', 'pelvic_drop', 
                          'cadence', 'knee_valgus_symmetry']
        else:  # lateral
            metric_keys = ['overstriding', 'knee_flexion_ic', 'trunk_lean', 
                          'ground_contact_time']
        
        for key in metric_keys:
            if key in metrics and 'z_score' in metrics[key]:
                total_error += abs(metrics[key]['z_score'])
                count += 1
        
        # Media degli errori assoluti
        if count > 0:
            return total_error / count
        return float('inf')
    
    def _update_global_stats_incremental(self, new_metrics: Dict, view_type: str):
        """
        Aggiorna le statistiche globali usando la media incrementale
        Formula: new_avg = (old_avg * count + new_value) / (count + 1)
        
        Args:
            new_metrics: Metriche della nuova corsa
            view_type: Tipo di vista
        """
        if 'global_stats' not in self.history_data:
            self.history_data['global_stats'] = {}
        
        global_stats = self.history_data['global_stats']
        current_count = self.history_data['run_count']
        
        if view_type == 'posterior':
            metric_keys = ['left_knee_valgus', 'right_knee_valgus', 'pelvic_drop', 
                          'cadence', 'knee_valgus_symmetry']
        else:  # lateral
            metric_keys = ['overstriding', 'knee_flexion_ic', 'trunk_lean', 
                          'ground_contact_time']
        
        for key in metric_keys:
            if key not in new_metrics:
                continue
            
            new_value = new_metrics[key].get('value', None)
            if new_value is None:
                continue
            
            # Inizializza se non esiste
            if key not in global_stats:
                global_stats[key] = {
                    'mean': new_value,
                    'std': 0.0,
                    'min': new_value,
                    'max': new_value,
                    'values': [new_value]  # Mantieni gli ultimi N valori per calcolare std
                }
            else:
                # Media incrementale
                old_mean = global_stats[key]['mean']
                new_mean = (old_mean * current_count + new_value) / (current_count + 1)
                global_stats[key]['mean'] = new_mean
                
                # Aggiorna min/max
                global_stats[key]['min'] = min(global_stats[key]['min'], new_value)
                global_stats[key]['max'] = max(global_stats[key]['max'], new_value)
                
                # Aggiungi valore alla lista (mantieni ultimi 100 per std)
                values = global_stats[key].get('values', [])
                values.append(new_value)
                if len(values) > 100:
                    values = values[-100:]  # Mantieni solo ultimi 100
                global_stats[key]['values'] = values
                
                # Calcola deviazione standard
                if len(values) > 1:
                    global_stats[key]['std'] = float(np.std(values))
                
                logger.debug(f"  {key}: old_mean={old_mean:.2f}, new_value={new_value:.2f}, new_mean={new_mean:.2f}")
        
        logger.info("✓ Statistiche globali aggiornate con media incrementale")
    
    def update(self, analysis_data: Dict, analysis_id: str, 
               skeleton_video_path: Optional[str] = None,
               is_best_candidate: bool = False) -> Dict:
        """
        Aggiorna lo storico della baseline con una nuova corsa
        
        Args:
            analysis_data: Dati completi dell'analisi (da detect_anomaly)
            analysis_id: ID univoco dell'analisi
            skeleton_video_path: Percorso del video con scheletro (per ghost frames)
            is_best_candidate: Se True, forza il controllo come miglior candidato
            
        Returns:
            Dizionario con risultati dell'aggiornamento
        """
        logger.info("=" * 60)
        logger.info("📊 AGGIORNAMENTO BASELINE INCREMENTALE")
        logger.info("=" * 60)
        
        # Carica storico se non già caricato
        if self.history_data is None:
            self.load()
        
        # Estrai info
        view_type = analysis_data.get('viewType', analysis_data.get('view_type', 'posterior'))
        metrics = analysis_data.get('metrics', {})
        overall_status = analysis_data.get('anomaly_level', analysis_data.get('overall_status', 'Unknown'))
        
        logger.info(f"Analysis ID: {analysis_id}")
        logger.info(f"View Type: {view_type}")
        logger.info(f"Overall Status: {overall_status}")
        
        # Verifica compatibilità view_type
        if self.history_data['view_type'] is None:
            # Prima corsa - inizializza
            self.history_data['view_type'] = view_type
            self.history_data['speed_kmh'] = analysis_data.get('speed_kmh')
            self.history_data['fps'] = analysis_data.get('fps')
            logger.info("🎯 Prima corsa - inizializzazione baseline history")
        elif self.history_data['view_type'] != view_type:
            logger.error(f"❌ View type incompatibile: storico={self.history_data['view_type']}, nuovo={view_type}")
            return {
                'status': 'error',
                'message': f'View type incompatibile. Storico usa {self.history_data["view_type"]}, analisi usa {view_type}.'
            }
        
        # Calcola errore totale della corsa
        run_error = self._calculate_run_error(metrics, view_type)
        logger.info(f"📊 Errore corsa: {run_error:.4f} (media Z-scores assoluti)")
        
        # Verifica se è la migliore corsa finora
        is_new_best = False
        old_best_error = self.history_data.get('best_run_error', float('inf'))
        
        if is_best_candidate or run_error < old_best_error:
            is_new_best = True
            logger.info(f"🏆 NUOVA MIGLIORE CORSA!")
            logger.info(f"   Vecchio errore: {old_best_error:.4f}")
            logger.info(f"   Nuovo errore: {run_error:.4f}")
            
            # Aggiorna riferimento alla migliore corsa
            self.history_data['best_run_id'] = analysis_id
            self.history_data['best_run_error'] = run_error
            
            # Se disponibile, aggiorna ghost frames dalla migliore corsa
            if skeleton_video_path and os.path.exists(skeleton_video_path):
                logger.info("👻 Aggiornamento Ghost Vision dalla nuova migliore corsa...")
                try:
                    ghost_result = self._update_ghost_frames(
                        skeleton_video_path, 
                        analysis_id,
                        analysis_data.get('fps', 30.0)
                    )
                    if ghost_result:
                        self.history_data['ghost_frames'] = ghost_result
                        logger.info(f"✓ Ghost frames aggiornati: {ghost_result['frames_processed']} frame")
                except Exception as e:
                    logger.error(f"⚠ Errore nell'aggiornamento ghost frames: {e}")
        else:
            logger.info(f"ℹ️ Corsa valida ma non la migliore (errore: {run_error:.4f} vs best: {old_best_error:.4f})")
        
        # Aggiorna statistiche globali con media incrementale
        logger.info("🔄 Aggiornamento statistiche globali...")
        self._update_global_stats_incremental(metrics, view_type)
        
        # Incrementa contatore corse
        self.history_data['run_count'] += 1
        
        # Aggiungi entry nello storico delle corse
        run_entry = {
            'analysis_id': analysis_id,
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'run_error': run_error,
            'is_best': is_new_best,
            'metrics_summary': {
                key: {
                    'value': metrics[key].get('value'),
                    'z_score': metrics[key].get('z_score'),
                    'level': metrics[key].get('level')
                }
                for key in metrics.keys()
            }
        }
        
        # Mantieni solo ultime 50 corse nello storico (per non far crescere troppo il file)
        if 'runs_history' not in self.history_data:
            self.history_data['runs_history'] = []
        self.history_data['runs_history'].append(run_entry)
        if len(self.history_data['runs_history']) > 50:
            self.history_data['runs_history'] = self.history_data['runs_history'][-50:]
        
        # Aggiorna timestamp
        self.history_data['updated_at'] = datetime.now().isoformat()
        
        # Salva su disco
        self._save()
        
        logger.info("=" * 60)
        logger.info("✅ BASELINE INCREMENTALE AGGIORNATA")
        logger.info(f"📊 Totale corse: {self.history_data['run_count']}")
        logger.info(f"🏆 Migliore corsa: {self.history_data['best_run_id']}")
        logger.info(f"📉 Miglior errore: {self.history_data['best_run_error']:.4f}")
        logger.info("=" * 60)
        
        return {
            'status': 'success',
            'message': 'Baseline aggiornata con successo',
            'run_count': self.history_data['run_count'],
            'is_new_best': is_new_best,
            'run_error': run_error,
            'best_run_error': self.history_data['best_run_error'],
            'best_run_id': self.history_data['best_run_id'],
            'global_stats': self.history_data['global_stats']
        }
    
    def _update_ghost_frames(self, skeleton_video_path: str, analysis_id: str, fps: float) -> Optional[Dict]:
        """
        Genera nuovi ghost frames dal video della migliore corsa
        
        Args:
            skeleton_video_path: Percorso del video con scheletro
            analysis_id: ID dell'analisi
            fps: FPS del video
            
        Returns:
            Dizionario con info sui ghost frames generati o None se errore
        """
        try:
            from pose_engine import PoseEngine
            
            # Pulisci cartella ghost frames esistente
            if os.path.exists(self.ghost_frames_folder):
                logger.info(f"🧹 Pulizia ghost frames esistenti...")
                shutil.rmtree(self.ghost_frames_folder)
            os.makedirs(self.ghost_frames_folder, exist_ok=True)
            
            # Crea engine per generare ghost frames
            ghost_engine = PoseEngine(
                model_complexity=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
                enable_segmentation=True
            )
            
            # Genera ghost frames
            # NOTA: Per ora usiamo il video originale dell'analisi
            # In futuro potremmo salvare il video originale per ogni analisi
            logger.info(f"👻 Generazione ghost frames da: {skeleton_video_path}")
            
            # Il video con scheletro non ha la segmentation mask, quindi non possiamo usarlo
            # Per ora salviamo solo i metadati
            # TODO: Salvare il video originale per poter rigenerare ghost frames
            
            return {
                'analysis_id': analysis_id,
                'source_video': skeleton_video_path,
                'frames_processed': 0,
                'note': 'Ghost frames generation requires original video (not skeleton video)'
            }
            
        except Exception as e:
            logger.error(f"❌ Errore nella generazione ghost frames: {e}")
            return None
    
    def _save(self):
        """Salva lo storico della baseline su disco"""
        try:
            # Assicurati che la directory esista
            os.makedirs(os.path.dirname(self.history_file_path), exist_ok=True)
            
            # Rimuovi 'values' dalle statistiche prima di salvare (troppo grande)
            history_to_save = self.history_data.copy()
            if 'global_stats' in history_to_save:
                for key in history_to_save['global_stats']:
                    if 'values' in history_to_save['global_stats'][key]:
                        del history_to_save['global_stats'][key]['values']
            
            with open(self.history_file_path, 'w') as f:
                json.dump(history_to_save, f, indent=2)
            logger.info(f"💾 Baseline history salvato: {self.history_file_path}")
        except Exception as e:
            logger.error(f"❌ Errore nel salvare baseline history: {e}")
            raise
    
    def get_current_baseline(self) -> Dict:
        """
        Restituisce la baseline corrente (statistiche globali)
        in formato compatibile con il sistema esistente
        
        Returns:
            Dizionario con statistiche baseline
        """
        if self.history_data is None:
            self.load()
        
        if self.history_data['run_count'] == 0:
            return None
        
        baseline_stats = {
            'view_type': self.history_data['view_type'],
            'speed_kmh': self.history_data['speed_kmh'],
            'fps': self.history_data['fps'],
            'n_videos': self.history_data['run_count'],
            'created_at': self.history_data['created_at'],
            'updated_at': self.history_data['updated_at'],
            'total_frames': 0,  # Non tracciato in baseline incrementale
            'is_incremental': True,
            'best_run_id': self.history_data['best_run_id'],
            'best_run_error': self.history_data['best_run_error']
        }
        
        # Aggiungi statistiche globali
        for key, stats in self.history_data['global_stats'].items():
            baseline_stats[key] = {
                'mean': stats['mean'],
                'std': stats['std'],
                'min': stats['min'],
                'max': stats['max']
            }
        
        # Aggiungi ghost frames info se disponibile
        if 'ghost_frames' in self.history_data:
            baseline_stats['ghost_frames'] = self.history_data['ghost_frames']
        
        return baseline_stats
    
    def get_stats_summary(self) -> Dict:
        """
        Restituisce un summary dello storico della baseline
        
        Returns:
            Dizionario con statistiche di riepilogo
        """
        if self.history_data is None:
            self.load()
        
        return {
            'run_count': self.history_data['run_count'],
            'best_run_id': self.history_data['best_run_id'],
            'best_run_error': self.history_data['best_run_error'],
            'view_type': self.history_data['view_type'],
            'created_at': self.history_data['created_at'],
            'updated_at': self.history_data['updated_at'],
            'global_stats_keys': list(self.history_data.get('global_stats', {}).keys()),
            'recent_runs': self.history_data.get('runs_history', [])[-5:]  # Ultimi 5
        }


