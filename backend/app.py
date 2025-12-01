"""
Server Flask per l'API REST dell'applicazione Running Analyzer
Versione con approccio geometrico/statistico (no Deep Learning)
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sys
import json
import logging
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import Config
from pose_engine import PoseEngine

# Configurazione logging
def setup_logging():
    """Configura il sistema di logging"""
    log_format = '[%(asctime)s] [%(name)s] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger('APP')

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Inizializza le cartelle
Config.init_app()

# Percorso del file baseline JSON
BASELINE_JSON_PATH = os.path.join(Config.MODEL_FOLDER, 'baseline.json')

# Percorsi frontend
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
FRONTEND_DIST_DIR = os.path.join(FRONTEND_DIR, 'dist')


def allowed_file(filename):
    """Controlla se il file ha un'estensione permessa"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def safe_remove_file(filepath):
    """
    Rimuove un file in modo sicuro, gestendo errori di permesso su Windows
    
    Args:
        filepath: Percorso del file da rimuovere
        
    Returns:
        bool: True se rimosso con successo, False altrimenti
    """
    if not os.path.exists(filepath):
        return True
    
    try:
        os.remove(filepath)
        logger.debug(f"✓ File rimosso: {os.path.basename(filepath)}")
        return True
    except PermissionError as e:
        # Su Windows, il file potrebbe essere ancora aperto da un altro processo (browser, player, ecc.)
        logger.warning(f"⚠ Impossibile rimuovere file {os.path.basename(filepath)}: {e}")
        logger.warning(f"  Il file è probabilmente ancora aperto da un altro processo.")
        logger.warning(f"  Verrà rimosso automaticamente quando non sarà più in uso.")
        return False
    except OSError as e:
        logger.warning(f"⚠ Errore nella rimozione file {os.path.basename(filepath)}: {e}")
        return False


@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint per verificare lo stato del server"""
    return jsonify({
        'status': 'success',
        'message': 'Running Analyzer Server attivo'
    })


@app.route('/api/processed_video/<path:filename>', methods=['GET'])
def get_processed_video(filename):
    """Endpoint per servire i video processati con scheletro"""
    from config import Config
    from urllib.parse import unquote
    
    # Decodifica il nome del file dall'URL (gestisce caratteri speciali)
    filename = unquote(filename)
    
    # Sanitizza il nome del file per sicurezza (rimuove path traversal)
    filename = os.path.basename(filename)  # Rimuove eventuali percorsi
    
    video_path = os.path.join(Config.PROCESSED_VIDEOS_FOLDER, filename)
    
    logger.debug(f"📹 Richiesta video: {filename}")
    logger.debug(f"📹 Percorso completo: {video_path}")
    logger.debug(f"📹 File esiste: {os.path.exists(video_path)}")
    
    if not os.path.exists(video_path):
        logger.warning(f"⚠ Video non trovato: {video_path}")
        # Lista tutti i file nella directory per debug
        if os.path.exists(Config.PROCESSED_VIDEOS_FOLDER):
            files = os.listdir(Config.PROCESSED_VIDEOS_FOLDER)
            logger.debug(f"📁 File disponibili in processed_videos: {files}")
        return jsonify({
            'status': 'error',
            'message': f'Video non trovato: {filename}'
        }), 404
    
    # Verifica che il file sia nella directory corretta (sicurezza)
    if not os.path.abspath(video_path).startswith(os.path.abspath(Config.PROCESSED_VIDEOS_FOLDER)):
        logger.warning(f"⚠ Tentativo di accesso non autorizzato: {video_path}")
        return jsonify({
            'status': 'error',
            'message': 'Accesso negato'
        }), 403
    
    logger.info(f"✅ Invio video: {filename}")
    
    # Aggiungi headers per supporto video streaming e CORS
    response = send_from_directory(Config.PROCESSED_VIDEOS_FOLDER, filename)
    response.headers['Accept-Ranges'] = 'bytes'
    response.headers['Content-Type'] = 'video/mp4'
    response.headers['Cache-Control'] = 'public, max-age=3600'
    return response


@app.route('/api/create_baseline', methods=['POST'])
def create_baseline():
    """
    Endpoint per creare la baseline da 5 video di riferimento
    
    Workflow:
    1. Riceve 5 video di baseline
    2. Usa PoseEngine per processarli (geometrico)
    3. Calcola statistiche aggregate (Media, StdDev, Min, Max)
    4. Salva un file JSON con le statistiche
    """
    logger.info("=" * 60)
    logger.info("📥 Richiesta creazione baseline ricevuta")
    try:
        # Controlla i file
        if 'videos' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'Nessun video fornito'
            }), 400
        
        files = request.files.getlist('videos')
        
        # Verifica 5 video
        if len(files) != 5:
            return jsonify({
                'status': 'error',
                'message': f'Sono richiesti esattamente 5 video, ricevuti {len(files)}'
            }), 400
        
        # Salva i video
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
        
        logger.info(f"=== Creazione Baseline ===")
        logger.info(f"Video salvati: {[os.path.basename(vp) for vp in video_paths]}")
        
        # Verifica che i video esistano e siano leggibili
        for vp in video_paths:
            if not os.path.exists(vp):
                return jsonify({
                    'status': 'error',
                    'message': f'Video non trovato: {os.path.basename(vp)}'
                }), 400
            if os.path.getsize(vp) == 0:
                return jsonify({
                    'status': 'error',
                    'message': f'Video vuoto: {os.path.basename(vp)}'
                }), 400
        
        # Valida parametri
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
        
        # View type (opzionale, default='posterior')
        view_type = request.form.get('view_type', 'posterior')
        if view_type not in ['posterior', 'lateral']:
            return jsonify({
                'status': 'error',
                'message': 'view_type deve essere "posterior" o "lateral"'
            }), 400
        
        try:
            speed = float(request.form['speed'])
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
        
        logger.info(f"📊 Parametri baseline: Vista={view_type}, Velocità={speed} km/h, FPS={fps}")
        logger.info(f"📁 Directory models: {Config.MODEL_FOLDER}")
        logger.info(f"📁 Directory uploads: {Config.UPLOAD_FOLDER}")
        
        # Funzione helper per processare un singolo video (thread-safe)
        def process_single_video(i, video_path):
            """Processa un singolo video creando una nuova istanza di PoseEngine (thread-safe)"""
            try:
                logger.info(f"Processing video {i+1}/5: {os.path.basename(video_path)}")
                # Crea nuova istanza per ogni thread (MediaPipe non è thread-safe)
                logger.debug(f"  Creazione PoseEngine per video {i+1}...")
                engine = PoseEngine(
                    model_complexity=Config.MEDIAPIPE_MODEL_COMPLEXITY,
                    min_detection_confidence=Config.MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
                    min_tracking_confidence=Config.MEDIAPIPE_MIN_TRACKING_CONFIDENCE
                )
                logger.debug(f"  PoseEngine creato, avvio processing video {i+1}...")
                result = engine.process_video(video_path, fps=fps, view_type=view_type)
                logger.debug(f"  Processing video {i+1} completato")
                return i, result
            except Exception as e:
                logger.error(f"  ❌ Errore in process_single_video per video {i+1}: {type(e).__name__}: {str(e)}", exc_info=True)
                raise
        
        # Processa tutti i 5 video in parallelo
        logger.info("Fase 1: Processing video con PoseEngine (parallelo)...")
        videos_data = [None] * len(video_paths)
        errors = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Sottometti tutti i task
            future_to_index = {
                executor.submit(process_single_video, i, vp): i 
                for i, vp in enumerate(video_paths)
            }
            
            # Raccogli risultati man mano che completano
            for future in as_completed(future_to_index):
                i = future_to_index[future]
                try:
                    idx, video_data = future.result()
                    videos_data[idx] = video_data
                    logger.info(f"✓ Completato video {idx+1}/5: {os.path.basename(video_paths[idx])}")
                except Exception as e:
                    error_msg = f"Errore nell'elaborazione video {i+1}/5 ({os.path.basename(video_paths[i])}): {str(e)}"
                    logger.error(f"⚠ {error_msg}", exc_info=True)
                    errors.append(error_msg)
        
        # Verifica che tutti i video siano stati processati
        videos_data = [v for v in videos_data if v is not None]
        if len(videos_data) != len(video_paths):
            error_details = "; ".join(errors) if errors else "Errore sconosciuto"
            logger.error(f"❌ Fallimento processing: {len(videos_data)}/{len(video_paths)} video processati. Errori: {error_details}")
            return jsonify({
                'status': 'error',
                'message': f'Errore: solo {len(videos_data)}/{len(video_paths)} video processati con successo. Dettagli: {error_details}'
            }), 500
        
        # Crea statistiche baseline
        logger.info("Fase 2: Creazione statistiche baseline...")
        try:
            # Crea un'istanza di engine solo per create_baseline_stats (non usa MediaPipe)
            engine = PoseEngine()
            logger.debug("  Calcolo statistiche aggregate...")
            baseline_stats = engine.create_baseline_stats(videos_data)
            logger.info(f"  ✓ Statistiche calcolate: {len(baseline_stats)} metriche")
        except Exception as e:
            logger.error(f"❌ Errore nella creazione statistiche baseline: {type(e).__name__}: {str(e)}", exc_info=True)
            raise
        
        # Aggiungi parametri di calibrazione
        baseline_stats['view_type'] = view_type
        baseline_stats['speed_kmh'] = float(speed)
        baseline_stats['fps'] = float(fps)
        baseline_stats['created_at'] = datetime.now().isoformat()
        
        # Salva baseline JSON
        logger.info(f"Fase 3: Salvataggio baseline in: {BASELINE_JSON_PATH}")
        try:
            # Assicurati che la directory esista
            os.makedirs(os.path.dirname(BASELINE_JSON_PATH), exist_ok=True)
            with open(BASELINE_JSON_PATH, 'w') as f:
                json.dump(baseline_stats, f, indent=2)
            logger.info(f"  ✓ Baseline salvata con successo")
        except Exception as e:
            logger.error(f"❌ Errore nel salvataggio baseline: {type(e).__name__}: {str(e)}", exc_info=True)
            raise
        
        # Pulisci video temporanei
        for video_path in video_paths:
            safe_remove_file(video_path)
        
        logger.info("✅ Baseline creata con successo!")
        
        # Prepara URL video con scheletro (usa l'ultimo video processato come esempio)
        skeleton_video_url = None
        if videos_data and len(videos_data) > 0:
            last_video_data = videos_data[-1]
            if last_video_data.get('skeleton_video_path'):
                skeleton_path = last_video_data['skeleton_video_path']
                if os.path.exists(skeleton_path):
                    skeleton_filename = os.path.basename(skeleton_path)
                    # URL encode il nome del file per gestire caratteri speciali
                    from urllib.parse import quote
                    skeleton_video_url = f'/api/processed_video/{quote(skeleton_filename)}'
                    logger.info(f"📹 Video esempio con scheletro disponibile: {skeleton_filename}")
                    logger.info(f"📹 URL video: {skeleton_video_url}")
                else:
                    logger.warning(f"⚠ Video scheletro non trovato: {skeleton_path}")
        
        # Prepara risposta per frontend
        response_data = {
            'status': 'success',
            'message': 'Baseline creata con successo',
            'baselineCreated': True,
            'viewType': view_type,
            'skeleton_video_url': skeleton_video_url,
            'baselineRanges': {}
        }
        
        if view_type == 'posterior':
            response_data['baselineRanges'] = {
                'leftKneeValgus': {
                    'min': baseline_stats['left_knee_valgus']['min'],
                    'max': baseline_stats['left_knee_valgus']['max'],
                    'mean': baseline_stats['left_knee_valgus']['mean'],
                    'std': baseline_stats['left_knee_valgus']['std'],
                    'unit': '°'
                },
                'rightKneeValgus': {
                    'min': baseline_stats['right_knee_valgus']['min'],
                    'max': baseline_stats['right_knee_valgus']['max'],
                    'mean': baseline_stats['right_knee_valgus']['mean'],
                    'std': baseline_stats['right_knee_valgus']['std'],
                    'unit': '°'
                },
                'kneeValgusSymmetry': {
                    'min': baseline_stats.get('knee_valgus_symmetry', {}).get('min', 0.0),
                    'max': baseline_stats.get('knee_valgus_symmetry', {}).get('max', 100.0),
                    'mean': baseline_stats.get('knee_valgus_symmetry', {}).get('mean', 100.0),
                    'std': baseline_stats.get('knee_valgus_symmetry', {}).get('std', 0.0),
                    'unit': '%'
                },
                'pelvicDrop': {
                    'min': baseline_stats['pelvic_drop']['min'],
                    'max': baseline_stats['pelvic_drop']['max'],
                    'mean': baseline_stats['pelvic_drop']['mean'],
                    'std': baseline_stats['pelvic_drop']['std'],
                    'unit': '°'
                },
                'cadence': {
                    'min': baseline_stats['cadence']['min'],
                    'max': baseline_stats['cadence']['max'],
                    'mean': baseline_stats['cadence']['mean'],
                    'std': baseline_stats['cadence']['std'],
                    'unit': 'spm'
                }
            }
        else:  # lateral
            response_data['baselineRanges'] = {
                'overstriding': {
                    'min': baseline_stats['overstriding']['min'],
                    'max': baseline_stats['overstriding']['max'],
                    'mean': baseline_stats['overstriding']['mean'],
                    'std': baseline_stats['overstriding']['std'],
                    'unit': 'm'
                },
                'kneeFlexionIC': {
                    'min': baseline_stats['knee_flexion_ic']['min'],
                    'max': baseline_stats['knee_flexion_ic']['max'],
                    'mean': baseline_stats['knee_flexion_ic']['mean'],
                    'std': baseline_stats['knee_flexion_ic']['std'],
                    'unit': '°'
                },
                'trunkLean': {
                    'min': baseline_stats['trunk_lean']['min'],
                    'max': baseline_stats['trunk_lean']['max'],
                    'mean': baseline_stats['trunk_lean']['mean'],
                    'std': baseline_stats['trunk_lean']['std'],
                    'unit': '°'
                },
                'groundContactTime': {
                    'min': baseline_stats['ground_contact_time']['min'],
                    'max': baseline_stats['ground_contact_time']['max'],
                    'mean': baseline_stats['ground_contact_time']['mean'],
                    'std': baseline_stats['ground_contact_time']['std'],
                    'unit': 's'
                }
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"❌ Errore nella creazione baseline: {error_type}: {error_msg}", exc_info=True)
        logger.error(f"Traceback completo:\n{error_traceback}")
        return jsonify({
            'status': 'error',
            'message': f'Errore interno: {error_type}: {error_msg}',
            'error_type': error_type,
            'traceback': error_traceback if app.config.get('DEBUG', False) else None
        }), 500


@app.route('/api/detect_anomaly', methods=['POST'])
def detect_anomaly():
    """
    Endpoint per analizzare un video confrontandolo con la baseline
    
    Workflow:
    1. Riceve 1 video
    2. Carica baseline JSON
    3. Usa PoseEngine per processare il video
    4. Calcola Z-Scores confrontando con baseline
    5. Restituisce report con stato e grafici
    """
    try:
        # Controlla file video
        if 'video' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'Nessun video fornito'
            }), 400
        
        file = request.files['video']
        
        if not file or not allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'message': 'File video non valido'
            }), 400
        
        # Salva video
        filename = secure_filename(file.filename)
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        logger.info(f"=== Analisi Video ===")
        logger.info(f"Video: {filename}")
        
        # Valida parametri
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
        
        # View type (opzionale, default='posterior')
        view_type = request.form.get('view_type', 'posterior')
        if view_type not in ['posterior', 'lateral']:
            return jsonify({
                'status': 'error',
                'message': 'view_type deve essere "posterior" o "lateral"'
            }), 400
        
        try:
            speed = float(request.form['speed'])
            fps = float(request.form['fps'])
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'Velocità e FPS devono essere numeri validi'
            }), 400
        
        logger.info(f"📊 Parametri analisi: Vista={view_type}, Velocità={speed} km/h, FPS={fps}")
        
        # Carica baseline
        if not os.path.exists(BASELINE_JSON_PATH):
            return jsonify({
                'status': 'error',
                'message': 'Baseline non trovata. Crea prima una baseline con 5 video.'
            }), 400
        
        logger.info("Caricamento baseline...")
        with open(BASELINE_JSON_PATH, 'r') as f:
            baseline_stats = json.load(f)
        
        baseline_speed = baseline_stats['speed_kmh']
        baseline_fps = baseline_stats['fps']
        baseline_view_type = baseline_stats.get('view_type', 'posterior')
        
        logger.info(f"📊 Baseline: Vista={baseline_view_type}, Velocità={baseline_speed} km/h, FPS={baseline_fps}")
        
        # Valida corrispondenza view_type
        if view_type != baseline_view_type:
            return jsonify({
                'status': 'error',
                'message': f'Il tipo di vista non corrisponde alla baseline. Baseline: {baseline_view_type}, Fornito: {view_type}.'
            }), 400
        
        # Valida corrispondenza parametri (tolleranza 0.5)
        if abs(speed - baseline_speed) > 0.5:
            return jsonify({
                'status': 'error',
                'message': f'Velocità non corrisponde alla baseline. Baseline: {baseline_speed} km/h, Fornito: {speed} km/h.'
            }), 400
        
        # Inizializza PoseEngine
        engine = PoseEngine(
            model_complexity=Config.MEDIAPIPE_MODEL_COMPLEXITY,
            min_detection_confidence=Config.MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=Config.MEDIAPIPE_MIN_TRACKING_CONFIDENCE
        )
        
        # Processa video
        logger.info("Fase 1: Processing video con PoseEngine...")
        video_data = engine.process_video(filepath, fps=baseline_fps, view_type=view_type)
        
        # Calcola Z-Scores
        logger.info("Fase 2: Calcolo Z-Scores...")
        z_scores = engine.calculate_z_scores(video_data, baseline_stats)
        
        # Pulisci video temporaneo
        safe_remove_file(filepath)
        
        logger.info(f"✅ Analisi completata! Stato: {z_scores['overall_status']}")
        
        # Prepara URL video con scheletro se disponibile
        skeleton_video_url = None
        if video_data.get('skeleton_video_path'):
            skeleton_path = video_data['skeleton_video_path']
            if os.path.exists(skeleton_path):
                skeleton_filename = os.path.basename(skeleton_path)
                # URL encode il nome del file per gestire caratteri speciali
                from urllib.parse import quote
                skeleton_video_url = f'/api/processed_video/{quote(skeleton_filename)}'
                logger.info(f"📹 Video con scheletro disponibile: {skeleton_filename}")
                logger.info(f"📹 URL video: {skeleton_video_url}")
            else:
                logger.warning(f"⚠ Video scheletro non trovato: {skeleton_path}")
        
        # Prepara risposta per frontend
        response_data = {
            'status': 'success',
            'viewType': view_type,
            'anomaly_level': z_scores['overall_status'],
            'anomaly_color': z_scores['overall_color'],
            'anomaly_score': z_scores['max_z_score'],
            'skeleton_video_url': skeleton_video_url,
            'metrics': {},
            'charts': {
                'timeline': list(range(video_data['n_frames']))
            },
            'video_info': {
                'n_frames': video_data['n_frames'],
                'frames_with_pose': video_data['frames_with_pose'],
                'fps': video_data['fps'],
                'duration': video_data['n_frames'] / video_data['fps']
            }
        }
        
        if view_type == 'posterior':
            response_data['metrics'] = {
                'left_knee_valgus': {
                    'value': z_scores['left_knee_valgus']['value'],
                    'z_score': z_scores['left_knee_valgus']['z_score'],
                    'level': z_scores['left_knee_valgus']['level'],
                    'color': z_scores['left_knee_valgus']['color'],
                    'baseline_mean': baseline_stats['left_knee_valgus']['mean'],
                    'baseline_std': baseline_stats['left_knee_valgus']['std'],
                    'unit': '°'
                },
                'right_knee_valgus': {
                    'value': z_scores['right_knee_valgus']['value'],
                    'z_score': z_scores['right_knee_valgus']['z_score'],
                    'level': z_scores['right_knee_valgus']['level'],
                    'color': z_scores['right_knee_valgus']['color'],
                    'baseline_mean': baseline_stats['right_knee_valgus']['mean'],
                    'baseline_std': baseline_stats['right_knee_valgus']['std'],
                    'unit': '°'
                },
                'knee_valgus_symmetry': {
                    'value': z_scores.get('knee_valgus_symmetry', {}).get('value', 0.0),
                    'z_score': z_scores.get('knee_valgus_symmetry', {}).get('z_score', 0.0),
                    'level': z_scores.get('knee_valgus_symmetry', {}).get('level', 'Ottimale'),
                    'color': z_scores.get('knee_valgus_symmetry', {}).get('color', '#10b981'),
                    'baseline_mean': baseline_stats.get('knee_valgus_symmetry', {}).get('mean', 100.0),
                    'baseline_std': baseline_stats.get('knee_valgus_symmetry', {}).get('std', 0.0),
                    'unit': '%'
                },
                'pelvic_drop': {
                    'value': z_scores['pelvic_drop']['value'],
                    'z_score': z_scores['pelvic_drop']['z_score'],
                    'level': z_scores['pelvic_drop']['level'],
                    'color': z_scores['pelvic_drop']['color'],
                    'baseline_mean': baseline_stats['pelvic_drop']['mean'],
                    'baseline_std': baseline_stats['pelvic_drop']['std'],
                    'unit': '°'
                },
                'cadence': {
                    'value': z_scores['cadence']['value'],
                    'z_score': z_scores['cadence']['z_score'],
                    'level': z_scores['cadence']['level'],
                    'color': z_scores['cadence']['color'],
                    'baseline_mean': baseline_stats['cadence']['mean'],
                    'baseline_std': baseline_stats['cadence']['std'],
                    'unit': 'spm'
                }
            }
            response_data['charts'].update({
                'left_knee_valgus': video_data['left_knee_valgus'],
                'right_knee_valgus': video_data['right_knee_valgus'],
                'pelvic_drop': video_data['pelvic_drop'],
                'cadence': video_data.get('cadence', []),
                'knee_valgus_symmetry': video_data.get('knee_valgus_symmetry', [])
            })
        
        else:  # lateral
            response_data['metrics'] = {
                'overstriding': {
                    'value': z_scores['overstriding']['value'],
                    'z_score': z_scores['overstriding']['z_score'],
                    'level': z_scores['overstriding']['level'],
                    'color': z_scores['overstriding']['color'],
                    'baseline_mean': baseline_stats['overstriding']['mean'],
                    'baseline_std': baseline_stats['overstriding']['std'],
                    'unit': 'm'
                },
                'knee_flexion_ic': {
                    'value': z_scores['knee_flexion_ic']['value'],
                    'z_score': z_scores['knee_flexion_ic']['z_score'],
                    'level': z_scores['knee_flexion_ic']['level'],
                    'color': z_scores['knee_flexion_ic']['color'],
                    'baseline_mean': baseline_stats['knee_flexion_ic']['mean'],
                    'baseline_std': baseline_stats['knee_flexion_ic']['std'],
                    'unit': '°'
                },
                'trunk_lean': {
                    'value': z_scores['trunk_lean']['value'],
                    'z_score': z_scores['trunk_lean']['z_score'],
                    'level': z_scores['trunk_lean']['level'],
                    'color': z_scores['trunk_lean']['color'],
                    'baseline_mean': baseline_stats['trunk_lean']['mean'],
                    'baseline_std': baseline_stats['trunk_lean']['std'],
                    'unit': '°'
                },
                'ground_contact_time': {
                    'value': z_scores['ground_contact_time']['value'],
                    'z_score': z_scores['ground_contact_time']['z_score'],
                    'level': z_scores['ground_contact_time']['level'],
                    'color': z_scores['ground_contact_time']['color'],
                    'baseline_mean': baseline_stats['ground_contact_time']['mean'],
                    'baseline_std': baseline_stats['ground_contact_time']['std'],
                    'unit': 's'
                }
            }
            response_data['charts'].update({
                'overstriding': video_data['overstriding'],
                'knee_flexion_ic': video_data['knee_flexion_ic'],
                'trunk_lean': video_data['trunk_lean'],
                'ground_contact_time': video_data['ground_contact_time']
            })
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Errore nell'analisi: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Errore interno: {str(e)}'
        }), 500


@app.route('/api/save_baseline', methods=['POST'])
def save_baseline():
    """
    Endpoint per salvare una baseline con un nome personalizzato
    
    Body JSON:
    {
        'name': 'Nome della baseline (opzionale)',
        'baseline_data': {...}  # Dati della baseline da salvare
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Nessun dato fornito'
            }), 400
        
        # Genera nome file con timestamp se non fornito
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name = data.get('name', f'baseline_{timestamp}')
        
        # Sanitizza il nome del file
        import re
        safe_name = re.sub(r'[^\w\-_\.]', '_', name)
        safe_name = re.sub(r'\.+', '.', safe_name)
        
        # Crea percorso file
        filename = f"{safe_name}.json"
        filepath = os.path.join(Config.SAVED_ANALYSES_FOLDER, filename)
        
        # Aggiungi metadata
        baseline_data = data.get('baseline_data', {})
        baseline_data['saved_at'] = datetime.now().isoformat()
        baseline_data['saved_name'] = name
        baseline_data['type'] = 'baseline'
        
        # Se disponibile, carica anche i dati raw dalla baseline.json standard
        if os.path.exists(BASELINE_JSON_PATH):
            try:
                with open(BASELINE_JSON_PATH, 'r') as f:
                    raw_baseline = json.load(f)
                baseline_data['raw_baseline_stats'] = raw_baseline
            except Exception as e:
                logger.warning(f"⚠ Impossibile caricare baseline raw: {e}")
        
        # Salva file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(baseline_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Baseline salvata: {filename}")
        
        return jsonify({
            'status': 'success',
            'message': f'Baseline salvata come "{name}"',
            'filename': filename,
            'filepath': filepath
        })
        
    except Exception as e:
        logger.error(f"❌ Errore nel salvataggio baseline: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Errore nel salvataggio: {str(e)}'
        }), 500


@app.route('/api/save_analysis', methods=['POST'])
def save_analysis():
    """
    Endpoint per salvare un'analisi con un nome personalizzato
    
    Body JSON:
    {
        'name': 'Nome dell\'analisi (opzionale)',
        'analysis_data': {...}  # Dati dell'analisi da salvare
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Nessun dato fornito'
            }), 400
        
        # Genera nome file con timestamp se non fornito
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name = data.get('name', f'analisi_{timestamp}')
        
        # Sanitizza il nome del file
        import re
        safe_name = re.sub(r'[^\w\-_\.]', '_', name)
        safe_name = re.sub(r'\.+', '.', safe_name)
        
        # Crea percorso file
        filename = f"{safe_name}.json"
        filepath = os.path.join(Config.SAVED_ANALYSES_FOLDER, filename)
        
        # Aggiungi metadata
        analysis_data = data.get('analysis_data', {})
        analysis_data['saved_at'] = datetime.now().isoformat()
        analysis_data['saved_name'] = name
        analysis_data['type'] = 'analysis'
        
        # Salva file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Analisi salvata: {filename}")
        
        return jsonify({
            'status': 'success',
            'message': f'Analisi salvata come "{name}"',
            'filename': filename,
            'filepath': filepath
        })
        
    except Exception as e:
        logger.error(f"❌ Errore nel salvataggio analisi: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Errore nel salvataggio: {str(e)}'
        }), 500


# Serve frontend statico (se buildato)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve il frontend buildato"""
    if os.path.exists(FRONTEND_DIST_DIR):
        if path != "" and os.path.exists(os.path.join(FRONTEND_DIST_DIR, path)):
            return send_from_directory(FRONTEND_DIST_DIR, path)
        else:
            return send_from_directory(FRONTEND_DIST_DIR, 'index.html')
    else:
        return jsonify({
            'message': 'Frontend non buildato. Esegui "npm run build" nella cartella frontend.'
        }), 404


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("  🏃 RUNNING ANALYZER - Backend Server")
    logger.info("  Approccio: Geometrico/Statistico (No Deep Learning)")
    logger.info("=" * 60)
    
    # Verifica dipendenze critiche
    try:
        import scipy
        logger.info(f"✓ SciPy {scipy.__version__} installato")
    except ImportError:
        logger.error("❌ SciPy non installato! Esegui: pip install scipy==1.11.4")
        sys.exit(1)
    
    try:
        import mediapipe
        logger.info(f"✓ MediaPipe {mediapipe.__version__} installato")
    except ImportError as e:
        logger.error(f"❌ MediaPipe non installato! Errore: {e}")
        sys.exit(1)
    
    # Verifica directory
    logger.info(f"📁 Upload folder: {Config.UPLOAD_FOLDER}")
    logger.info(f"📁 Model folder: {Config.MODEL_FOLDER}")
    logger.info(f"📁 Baseline path: {BASELINE_JSON_PATH}")
    
    if not os.path.exists(Config.UPLOAD_FOLDER):
        logger.warning(f"⚠ Upload folder non esiste, creazione...")
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    if not os.path.exists(Config.MODEL_FOLDER):
        logger.warning(f"⚠ Model folder non esiste, creazione...")
        os.makedirs(Config.MODEL_FOLDER, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("🚀 Server in avvio su http://0.0.0.0:5000")
    logger.info("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )

