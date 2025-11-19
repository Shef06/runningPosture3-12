"""
Server Flask per l'API REST dell'applicazione di analisi biomeccanica
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sys
import webbrowser
import threading
import time
import numpy as np
import logging
from datetime import datetime
from config import Config
from keypoint_extractor import KeypointExtractor
from feature_engineering import BiomechanicalFeatures
from lstm_autoencoder import LSTMAutoencoder
from gait_event_detection import GaitEventDetector
from stability_metrics import StabilityMetrics
from statistics import calculate_stats, calculate_biomechanical_stats_from_keypoints, calculate_all_feature_stats, format_statistics_for_frontend

# Configurazione logging centralizzata
def setup_logging():
    """Configura il sistema di logging con formato personalizzato"""
    # Formato: [timestamp] [MODULE_NAME] messaggio
    log_format = '[%(asctime)s] [%(name)s] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Configura il root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout)  # Output su terminale
        ]
    )
    
    # Imposta livello INFO per tutti i logger
    logging.getLogger().setLevel(logging.INFO)
    
    # Riduci verbosità di alcune librerie
    logging.getLogger('tensorflow').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

# Inizializza logging all'avvio
setup_logging()

# Logger per questo modulo
logger = logging.getLogger('APP')


app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Inizializza le cartelle
Config.init_app()

# Percorso del modello baseline
BASELINE_MODEL_PATH = os.path.join(Config.MODEL_FOLDER, 'baseline_model.h5')

# Percorso del frontend buildato (cerca in diverse posizioni possibili)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
FRONTEND_DIST_DIR = os.path.join(FRONTEND_DIR, 'dist')  # Svelte puro con Vite usa 'dist'
FRONTEND_BUILD_DIR = os.path.join(FRONTEND_DIR, 'build')
FRONTEND_SVELTEKIT_CLIENT_DIR = os.path.join(FRONTEND_DIR, '.svelte-kit', 'output', 'client')
FRONTEND_SVELTEKIT_PRERENDERED_DIR = os.path.join(FRONTEND_DIR, '.svelte-kit', 'output', 'prerendered')

# Funzione per trovare la directory di build
def find_build_directory():
    """Cerca la directory di build del frontend in diverse posizioni possibili"""
    possible_dirs = [
        FRONTEND_DIST_DIR,  # Priorità: Svelte puro con Vite
        FRONTEND_BUILD_DIR,
        FRONTEND_SVELTEKIT_CLIENT_DIR,
        FRONTEND_SVELTEKIT_PRERENDERED_DIR,
        os.path.join(FRONTEND_DIR, '.svelte-kit', 'output', 'static'),
    ]
    
    for dir_path in possible_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            try:
                # Verifica che contenga almeno un file HTML
                files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
                if any(f.endswith('.html') for f in files):
                    return dir_path
                # Prova anche nella sottocartella client
                client_dir = os.path.join(dir_path, 'client')
                if os.path.exists(client_dir) and os.path.isdir(client_dir):
                    client_files = [f for f in os.listdir(client_dir) if os.path.isfile(os.path.join(client_dir, f))]
                    if any(f.endswith('.html') for f in client_files):
                        return client_dir
            except (PermissionError, OSError):
                continue
    return None

# Cerca automaticamente i file buildati
BUILD_DIR = find_build_directory()
SERVE_BUILD = BUILD_DIR is not None


def allowed_file(filename):
    """Controlla se il file ha un'estensione permessa"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint per verificare lo stato del server"""
    return jsonify({
        'status': 'success',
        'message': 'Server attivo e funzionante'
    })


@app.route('/api/create_baseline', methods=['POST'])
def create_baseline():
    """
    Endpoint per creare la baseline da 5 video di riferimento
    
    Workflow:
    1. Riceve 5 video di baseline
    2. Estrae i keypoint 3D con MediaPipe
    3. Calcola gli angoli articolari
    4. Addestra l'Autoencoder LSTM
    5. Salva il modello
    """
    try:
        # Controlla se sono stati inviati i file
        if 'videos' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'Nessun video fornito'
            }), 400
        
        files = request.files.getlist('videos')
        
        # Verifica che siano esattamente 5 video
        if len(files) != 5:
            return jsonify({
                'status': 'error',
                'message': f'Sono richiesti esattamente 5 video, ricevuti {len(files)}'
            }), 400
        
        # Salva i video caricati
        video_paths = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
                file.save(filepath)
                video_paths.append(filepath)
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'File non valido: {file.filename}'
                }), 400
        
        logger.info(f"=== Creazione baseline ===")
        logger.info(f"Video salvati: {[os.path.basename(vp) for vp in video_paths]}")
        
        # Valida parametri obbligatori
        if 'speed' not in request.form or not request.form['speed']:
            return jsonify({
                'status': 'error',
                'message': 'Velocità del tapis roulant (speed) è obbligatoria'
            }), 400
        
        if 'fps' not in request.form or not request.form['fps']:
            return jsonify({
                'status': 'error',
                'message': 'FPS del video (fps) è obbligatorio'
            }), 400
        
        try:
            speed = float(request.form['speed'])  # km/h
            fps = float(request.form['fps'])
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'Velocità e FPS devono essere numeri validi'
            }), 400
        
        if speed <= 0 or speed > 50:
            return jsonify({
                'status': 'error',
                'message': 'Velocità deve essere tra 0 e 50 km/h'
            }), 400
        
        if fps <= 0 or fps > 240:
            return jsonify({
                'status': 'error',
                'message': 'FPS deve essere tra 0 e 240'
            }), 400
        
        logger.info(f"📊 Parametri baseline: Velocità={speed} km/h, FPS={fps}")
        
        # Fase 1: Estrazione keypoint 3D con MediaPipe (OTTIMIZZATO: parallelo + cache)
        logger.info("Fase 1: Estrazione keypoint 3D (ottimizzato con parallelizzazione)...")
        extractor = KeypointExtractor(
            model_complexity=Config.MEDIAPIPE_MODEL_COMPLEXITY,
            min_detection_confidence=Config.MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=Config.MEDIAPIPE_MIN_TRACKING_CONFIDENCE,
            use_cache=True,  # Abilita cache
            max_workers=None  # Auto-detect numero worker
        )
        
        # Estrai keypoint con resampling agli FPS specificati (PARALLELO)
        keypoints = extractor.extract_from_multiple_videos(video_paths, target_fps=fps, parallel=True)
        
        if keypoints is None:
            return jsonify({
                'status': 'error',
                'message': 'Errore nell\'estrazione dei keypoint dai video'
            }), 500
        
        logger.info(f"Keypoint estratti: {keypoints.shape}")
        
        # Fase 1.5: Rilevamento eventi del passo (per GCT e cadenza)
        logger.info("Fase 1.5: Rilevamento eventi del passo...")
        gait_detector = GaitEventDetector(fps=fps)
        gait_events = gait_detector.detect_events(keypoints)
        logger.info(f"Eventi rilevati: IC sinistro={len(gait_events['left']['ic'])}, IC destro={len(gait_events['right']['ic'])}")
        
        # Fase 2: Feature Engineering (calcolo features biomeccaniche avanzate) (OTTIMIZZATO: cache)
        logger.info("Fase 2: Calcolo features biomeccaniche avanzate (ottimizzato con cache)...")
        feature_extractor = BiomechanicalFeatures()
        features = feature_extractor.extract_all_features(keypoints, gait_events=gait_events, fps=fps, use_cache=True)
        
        logger.info(f"Features calcolate: {features.shape}")
        
        # Fase 3: Addestramento Autoencoder LSTM/GRU (OTTIMIZZATO: fine-tuning + GRU)
        logger.info("Fase 3: Addestramento modello GRU Autoencoder (ottimizzato con fine-tuning)...")
        autoencoder = LSTMAutoencoder(
            lstm_units=Config.LSTM_UNITS,
            latent_dim=Config.LATENT_DIM,
            use_gru=True,  # Usa GRU per velocità (circa 30% più veloce)
            use_cudnn=True  # Abilita cuDNN se GPU disponibile
        )
        
        # Addestra il modello con fine-tuning (solo 3-5 epoche invece di 50)
        history = autoencoder.train(
            data=features,
            sequence_length=30,  # Sequenze di 30 frame
            epochs=min(5, Config.EPOCHS),  # Massimo 5 epoche per fine-tuning
            batch_size=max(64, Config.BATCH_SIZE),  # Batch size ottimizzato (64)
            fine_tune=True  # Abilita fine-tuning da modello pre-addestrato
        )
        
        # Fase 4: Calcola le soglie dinamiche (OTTIMIZZATO: usa validation loss)
        logger.info("Fase 4: Calcolo soglie dinamiche dalla baseline (ottimizzato con validation loss)...")
        thresholds = autoencoder.calculate_dynamic_thresholds(
            data=features,
            sequence_length=30,
            use_statistical=True,  # Usa μ + 3σ invece di E_max semplice
            use_validation_loss=True  # OTTIMIZZAZIONE: usa validation loss invece di inference completa
        )
        
        # Fase 4.5: Calcola feature ranges (min/max) per ogni feature
        logger.info("Fase 4.5: Calcolo feature ranges dalla baseline...")
        feature_ranges = {
            'cpd': {
                'min': float(np.min(features[:, 0])),
                'max': float(np.max(features[:, 0]))
            },
            'bos': {
                'min': float(np.min(features[:, 1])),
                'max': float(np.max(features[:, 1]))
            },
            'rearfoot_eversion': {
                'min': float(np.min(features[:, 2])),
                'max': float(np.max(features[:, 2]))
            },
            'lateral_trunk_lean': {
                'min': float(np.min(features[:, 3])),
                'max': float(np.max(features[:, 3]))
            },
            'gct': {
                'min': float(np.min(features[:, 4])),
                'max': float(np.max(features[:, 4]))
            },
            'cadence': {
                'min': float(np.min(features[:, 5])),
                'max': float(np.max(features[:, 5]))
            }
        }
        logger.info(f"Feature ranges calcolati: CPD=[{feature_ranges['cpd']['min']:.2f}, {feature_ranges['cpd']['max']:.2f}], "
              f"BoS=[{feature_ranges['bos']['min']:.3f}, {feature_ranges['bos']['max']:.3f}]")
        
        # Salva il modello CON le soglie e i parametri di calibrazione
        logger.info("Salvataggio modello baseline...")
        autoencoder.save_model(BASELINE_MODEL_PATH, thresholds=thresholds)
        
        # Salva anche i parametri di calibrazione (speed, fps) e feature ranges nei metadati
        import json
        calibration_path = BASELINE_MODEL_PATH.replace('.h5', '_calibration.json')
        calibration_data = {
            'speed_kmh': float(speed),
            'fps': float(fps),
            'feature_ranges': feature_ranges  # Aggiungi feature ranges
        }
        with open(calibration_path, 'w') as f:
            json.dump(calibration_data, f, indent=2)
        logger.info(f"Parametri calibrazione salvati: Velocità={speed} km/h, FPS={fps}")
        
        # Pulisci i file video temporanei
        for video_path in video_paths:
            if os.path.exists(video_path):
                os.remove(video_path)
        
        # Calcola anche statistiche complete per la baseline (per visualizzazione)
        logger.info("Fase 5: Calcolo statistiche baseline per visualizzazione...")
        baseline_feature_stats = calculate_all_feature_stats(features)
        baseline_biomechanical_stats = calculate_biomechanical_stats_from_keypoints(keypoints)
        
        logger.info("=== Baseline creata con successo ===")
        
        # Formatta statistiche baseline
        formatted_baseline_feature_stats = {
            'cpd': format_statistics_for_frontend(baseline_feature_stats['cpd'], unit='°', decimals=2),
            'bos': format_statistics_for_frontend(baseline_feature_stats['bos'], unit='m', decimals=3),
            'rearfoot_eversion': format_statistics_for_frontend(baseline_feature_stats['rearfoot_eversion'], unit='°', decimals=2),
            'lateral_trunk_lean': format_statistics_for_frontend(baseline_feature_stats['lateral_trunk_lean'], unit='°', decimals=2),
            'gct': format_statistics_for_frontend(baseline_feature_stats['gct'], unit='ms', decimals=1),
            'cadence': format_statistics_for_frontend(baseline_feature_stats['cadence'], unit='passi/min', decimals=1)
        }
        
        formatted_baseline_biomechanical_stats = {
            'leftKneeAngle': format_statistics_for_frontend(baseline_biomechanical_stats['leftKneeAngle'], unit='°', decimals=2),
            'rightKneeAngle': format_statistics_for_frontend(baseline_biomechanical_stats['rightKneeAngle'], unit='°', decimals=2),
            'pelvicDrop': format_statistics_for_frontend(
                {k: v * 100 for k, v in baseline_biomechanical_stats['pelvicDrop'].items()},
                unit='%', decimals=2
            ),
            'trunkInclination': format_statistics_for_frontend(baseline_biomechanical_stats['trunkInclination'], unit='°', decimals=2)
        }
        
        return jsonify({
            'status': 'success',
            'message': 'Baseline creata e modello addestrato con successo',
            'details': {
                'n_frames_total': int(keypoints.shape[0]),
                'n_features': int(features.shape[1]),
                'final_loss': float(history.history['loss'][-1]),
                'final_val_loss': float(history.history['val_loss'][-1]),
                'thresholds': thresholds,  # Includi le soglie nella risposta
                'feature_ranges': feature_ranges,  # Includi feature ranges nella risposta
                'feature_metrics': formatted_baseline_feature_stats,  # Statistiche complete feature
                'biomechanics': formatted_baseline_biomechanical_stats,  # Statistiche complete biomeccaniche
                'speed_kmh': float(speed),
                'fps': float(fps)
            }
        })
        
    except Exception as e:
        logger.error(f"Errore in create_baseline: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Errore interno: {str(e)}'
        }), 500


@app.route('/api/detect_anomaly', methods=['POST'])
def detect_anomaly():
    """
    Endpoint per rilevare anomalie in un nuovo video
    
    Workflow:
    1. Riceve 1 video da analizzare
    2. Estrae i keypoint 3D con MediaPipe
    3. Calcola gli angoli articolari
    4. Carica il modello baseline
    5. Calcola l'errore di ricostruzione (anomaly score)
    """
    try:
        # Controlla se è stato inviato un file
        if 'video' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'Nessun video fornito'
            }), 400
        
        file = request.files['video']
        
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'Nessun file selezionato'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'message': 'Tipo di file non supportato'
            }), 400
        
        # Salva il video caricato
        filename = secure_filename(file.filename)
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        logger.info(f"=== Analisi video per anomalie ===")
        logger.info(f"Video da analizzare: {os.path.basename(filepath)}")
        
        # Verifica che esista il modello baseline
        if not os.path.exists(BASELINE_MODEL_PATH):
            return jsonify({
                'status': 'error',
                'message': 'Modello baseline non trovato. Crea prima una baseline.'
            }), 404
        
        # Valida parametri obbligatori
        if 'speed' not in request.form or not request.form['speed']:
            return jsonify({
                'status': 'error',
                'message': 'Velocità del tapis roulant (speed) è obbligatoria'
            }), 400
        
        if 'fps' not in request.form or not request.form['fps']:
            return jsonify({
                'status': 'error',
                'message': 'FPS del video (fps) è obbligatorio'
            }), 400
        
        try:
            speed = float(request.form['speed'])  # km/h
            fps = float(request.form['fps'])
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'Velocità e FPS devono essere numeri validi'
            }), 400
        
        # Carica i parametri di calibrazione della baseline (inclusi feature ranges)
        import json
        calibration_path = BASELINE_MODEL_PATH.replace('.h5', '_calibration.json')
        if not os.path.exists(calibration_path):
            return jsonify({
                'status': 'error',
                'message': 'Parametri di calibrazione baseline non trovati. Ricrea la baseline.'
            }), 404
        
        with open(calibration_path, 'r') as f:
            baseline_calibration = json.load(f)
        
        baseline_speed = baseline_calibration['speed_kmh']
        baseline_fps = baseline_calibration['fps']
        baseline_feature_ranges = baseline_calibration.get('feature_ranges', None)
        
        if baseline_feature_ranges:
            logger.info(f"✓ Feature ranges caricati dalla baseline")
        else:
            logger.warning("⚠️ Feature ranges non trovati nella calibrazione (baseline vecchia)")
        
        logger.info(f"📊 Parametri analisi: Velocità={speed} km/h, FPS={fps}")
        logger.info(f"📊 Parametri baseline: Velocità={baseline_speed} km/h, FPS={baseline_fps}")
        
        # Valida che la velocità corrisponda (tolleranza 0.5 km/h)
        if abs(speed - baseline_speed) > 0.5:
            return jsonify({
                'status': 'error',
                'message': f'Velocità non corrisponde alla baseline. Baseline: {baseline_speed} km/h, Fornito: {speed} km/h. '
                          f'La velocità deve corrispondere esattamente per un\'analisi accurata.'
            }), 400
        
        # Fase 1: Estrazione keypoint 3D con resampling agli FPS della baseline
        logger.info("Fase 1: Estrazione keypoint 3D...")
        extractor = KeypointExtractor(
            model_complexity=Config.MEDIAPIPE_MODEL_COMPLEXITY,
            min_detection_confidence=Config.MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=Config.MEDIAPIPE_MIN_TRACKING_CONFIDENCE
        )
        
        # Estrai keypoint con resampling agli FPS della baseline
        keypoints = extractor.extract_from_video(filepath, target_fps=baseline_fps)
        
        if keypoints is None:
            return jsonify({
                'status': 'error',
                'message': 'Errore nell\'estrazione dei keypoint dal video'
            }), 500
        
        logger.info(f"Keypoint estratti: {keypoints.shape}")
        
        # Fase 1.5: Rilevamento eventi del passo (per GCT e cadenza)
        logger.info("Fase 1.5: Rilevamento eventi del passo...")
        gait_detector = GaitEventDetector(fps=baseline_fps)
        gait_events = gait_detector.detect_events(keypoints)
        logger.info(f"Eventi rilevati: IC sinistro={len(gait_events['left']['ic'])}, IC destro={len(gait_events['right']['ic'])}")
        
        # Fase 2: Feature Engineering (calcolo features biomeccaniche avanzate)
        logger.info("Fase 2: Calcolo features biomeccaniche avanzate...")
        feature_extractor = BiomechanicalFeatures()
        features = feature_extractor.extract_all_features(keypoints, gait_events=gait_events, fps=baseline_fps)
        
        logger.info(f"Features calcolate: {features.shape}")
        
        # Fase 3: Caricamento modello e predizione
        logger.info("Fase 3: Calcolo anomaly score...")
        autoencoder = LSTMAutoencoder(
            lstm_units=Config.LSTM_UNITS,
            latent_dim=Config.LATENT_DIM
        )
        autoencoder.load_model(BASELINE_MODEL_PATH)
        
        # Calcola l'errore di ricostruzione
        anomaly_score = autoencoder.calculate_reconstruction_error(
            data=features,
            sequence_length=30
        )
        
        logger.info(f"Anomaly score: {anomaly_score:.6f}")
        
        # Fase 4: Calcola statistiche complete per tutte le metriche (TUTTO NEL BACKEND)
        logger.info("Fase 4: Calcolo statistiche complete...")
        
        # Statistiche per feature principali
        feature_stats = calculate_all_feature_stats(features)
        
        # Statistiche per metriche biomeccaniche legacy (angoli, ecc.)
        biomechanical_stats = calculate_biomechanical_stats_from_keypoints(keypoints)
        
        # Formatta per frontend
        formatted_feature_stats = {
            'cpd': format_statistics_for_frontend(feature_stats['cpd'], unit='°', decimals=2),
            'bos': format_statistics_for_frontend(feature_stats['bos'], unit='m', decimals=3),
            'rearfoot_eversion': format_statistics_for_frontend(feature_stats['rearfoot_eversion'], unit='°', decimals=2),
            'lateral_trunk_lean': format_statistics_for_frontend(feature_stats['lateral_trunk_lean'], unit='°', decimals=2),
            'gct': format_statistics_for_frontend(feature_stats['gct'], unit='ms', decimals=1),
            'cadence': format_statistics_for_frontend(feature_stats['cadence'], unit='passi/min', decimals=1)
        }
        
        formatted_biomechanical_stats = {
            'leftKneeAngle': format_statistics_for_frontend(biomechanical_stats['leftKneeAngle'], unit='°', decimals=2),
            'rightKneeAngle': format_statistics_for_frontend(biomechanical_stats['rightKneeAngle'], unit='°', decimals=2),
            'pelvicDrop': format_statistics_for_frontend(
                {k: v * 100 for k, v in biomechanical_stats['pelvicDrop'].items()},  # Converti in percentuale
                unit='%', decimals=2
            ),
            'trunkInclination': format_statistics_for_frontend(biomechanical_stats['trunkInclination'], unit='°', decimals=2)
        }
        
        # Mantieni anche valori medi per compatibilità
        metrics_avg = {
            'gct_mean': float(np.mean(features[:, 4])),  # GCT in ms
            'cadence_mean': float(np.mean(features[:, 5])),  # Cadenza in passi/min
            'cpd_mean': float(np.mean(features[:, 0])),  # CPD in gradi
            'bos_mean': float(np.mean(features[:, 1])),  # BoS in metri
            'rearfoot_eversion_mean': float(np.mean(features[:, 2])),  # Eversione in gradi
            'lateral_trunk_lean_mean': float(np.mean(features[:, 3]))  # Trunk lean in gradi
        }
        
        logger.info(f"Statistiche calcolate: CPD mean={formatted_feature_stats['cpd']['mean']:.2f}°, "
              f"BoS mean={formatted_feature_stats['bos']['mean']:.3f}m")
        
        # Fase 5: Calcola metriche di stabilità (variabilità e asimmetria)
        logger.info("Fase 5: Calcolo metriche di stabilità...")
        stability_calculator = StabilityMetrics(fps=baseline_fps)
        
        # Variabilità
        variability = stability_calculator.calculate_variability(gait_events)
        
        # Asimmetria (usa valori CPD dalla serie temporale)
        cpd_values = features[:, 0]
        asymmetry = stability_calculator.calculate_asymmetry(
            gait_events,
            cpd_values=cpd_values,
            fppa_values=None  # FPPA rimosso
        )
        
        logger.info(f"Variabilità: GCT CV={variability.get('gct_cv', 0):.2f}%, "
              f"Stride Time CV={variability.get('stride_time_cv', 0):.2f}%")
        logger.info(f"Asimmetria: GCT SI={asymmetry.get('gct_si', 0):.2f}%, "
              f"CPD SA={asymmetry.get('cpd_sa', 0):.2f}%")
        
        # Usa le soglie dinamiche se disponibili
        if autoencoder.thresholds:
            level, color = autoencoder.get_anomaly_level(anomaly_score, autoencoder.thresholds)
            logger.info(f"Livello anomalia (dinamico): {level} (soglia E_max: {autoencoder.thresholds['e_max']:.6f})")
            thresholds_used = True
            e_max = float(autoencoder.thresholds['e_max'])
        else:
            # Fallback alle soglie fisse se le dinamiche non sono disponibili
            logger.warning("⚠️ Soglie dinamiche non disponibili, uso soglie fisse")
            if anomaly_score < 0.01:
                level = "Ottimale"
                color = "green"
            elif anomaly_score < 0.05:
                level = "Buono"
                color = "lightgreen"
            elif anomaly_score < 0.1:
                level = "Moderato"
                color = "yellow"
            elif anomaly_score < 0.2:
                level = "Attenzione"
                color = "orange"
            else:
                level = "Critico"
                color = "red"
            thresholds_used = False
            e_max = None
        
        # Pulisci il file video temporaneo
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Prepara risposta completa con TUTTI i dati già elaborati
        response_data = {
            'status': 'success',
            'anomaly_score': float(anomaly_score),
            'anomaly_level': level,
            'anomaly_color': color,
            'thresholds_used': thresholds_used,
            'e_max': e_max,
            'feature_ranges': baseline_feature_ranges,
            'metadata': {
                'speed': float(speed),
                'fps_analyzed': float(fps),
                'n_frames': int(keypoints.shape[0]),
                'n_features': int(features.shape[1]),
                'duration': float(keypoints.shape[0] / baseline_fps) if baseline_fps > 0 else 0.0
            },
            # Statistiche complete per feature principali (già formattate)
            'feature_metrics': formatted_feature_stats,
            # Statistiche complete per metriche biomeccaniche legacy (già formattate)
            'biomechanics': formatted_biomechanical_stats,
            # Valori medi per compatibilità (deprecato, usare feature_metrics)
            'metrics_avg': {
                'gct_mean': round(metrics_avg['gct_mean'], 1),
                'cadence_mean': round(metrics_avg['cadence_mean'], 1),
                'cpd_mean': round(metrics_avg['cpd_mean'], 2),
                'bos_mean': round(metrics_avg['bos_mean'], 3),
                'rearfoot_eversion_mean': round(metrics_avg['rearfoot_eversion_mean'], 2),
                'lateral_trunk_lean_mean': round(metrics_avg['lateral_trunk_lean_mean'], 2)
            },
            # Metriche di stabilità
            'metrics_stability': {
                'gct_cv': round(variability.get('gct_cv', 0.0), 2),
                'stride_time_cv': round(variability.get('stride_time_cv', 0.0), 2)
            },
            # Metriche di asimmetria
            'metrics_asymmetry': {
                'gct_si': round(asymmetry.get('gct_si', 0.0), 2),
                'cpd_sa': round(asymmetry.get('cpd_sa', 0.0), 2)
            },
            'baseline_speed_kmh': float(baseline_speed),
            'baseline_fps': float(baseline_fps)
        }
        
        logger.info("=== Analisi video completata ===")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Errore in detect_anomaly: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Errore interno: {str(e)}'
        }), 500


# Flag globale per evitare doppia apertura in modalità debug
_browser_opened = False
_BROWSER_LOCK_FILE = os.path.join(BASE_DIR, '.browser_opened.lock')

def open_browser():
    """Apre il file index.html direttamente dalla cartella dist"""
    global _browser_opened
    
    # Usa un file di lock per evitare doppia apertura anche con Flask reloader
    lock_file = _BROWSER_LOCK_FILE
    
    # Controlla se il file di lock esiste (creato da un altro processo)
    if os.path.exists(lock_file):
        # Controlla se il file è recente (meno di 5 secondi)
        try:
            file_age = time.time() - os.path.getmtime(lock_file)
            if file_age < 5:
                return  # Un altro processo ha già aperto il browser di recente
            else:
                # Il file è vecchio, rimuovilo
                os.remove(lock_file)
        except (OSError, FileNotFoundError):
            pass
    
    # Crea il file di lock
    try:
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
    except (OSError, IOError):
        pass
    
    # Evita doppia apertura anche con flag globale
    if _browser_opened:
        return
    _browser_opened = True
    
    time.sleep(1.5)  # Aspetta che il server si avvii
    
    # Cerca index.html nella directory di build
    index_path = None
    if BUILD_DIR:
        # Prova prima nella directory principale
        test_path = os.path.join(BUILD_DIR, 'index.html')
        if os.path.exists(test_path):
            index_path = test_path
        else:
            # Prova nella sottocartella client
            client_path = os.path.join(BUILD_DIR, 'client', 'index.html')
            if os.path.exists(client_path):
                index_path = client_path
    
    if index_path:
        # Converti il percorso in formato file:// per Windows
        # Normalizza il percorso assoluto
        abs_path = os.path.abspath(index_path)
        # Converti backslash in forward slash e aggiungi file://
        file_url = 'file:///' + abs_path.replace('\\', '/')
        webbrowser.open(file_url)
        print(f"\n✓ Browser aperto su: {file_url}")
        print(f"  File: {abs_path}")
    else:
        print("\n⚠ File index.html non trovato nella directory di build")
        print(f"  Cercato in: {BUILD_DIR if BUILD_DIR else 'N/A'}")
    
    # Rimuovi il file di lock dopo l'apertura
    try:
        if os.path.exists(lock_file):
            os.remove(lock_file)
    except (OSError, FileNotFoundError):
        pass


if __name__ == '__main__':
    if SERVE_BUILD and BUILD_DIR:
        print("=" * 50)
        print("✓ File buildati trovati!")
        print("Modalità BUILD: Apertura file HTML direttamente")
        print(f"Directory build: {BUILD_DIR}")
        print("(JavaScript iniettato inline - compatibile con file://)")
        print("=" * 50)
        # Avvia il thread per aprire il browser
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
    else:
        print("=" * 50)
        print("ℹ Modalità DEV: Avvio solo il backend")
        print("File buildati non trovati.")
        print("Per aprire i file buildati, esegui 'npm run build' nella cartella frontend.")
        print("Oppure esegui 'npm run dev' per avviare il server di sviluppo.")
        print("=" * 50)
    
    print("\nServer Flask avviato su http://localhost:5000")
    print("(Il frontend viene aperto direttamente dal file system)")
    # Disabilita use_reloader per evitare doppia apertura del browser
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

