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
from datetime import datetime
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


@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint per verificare lo stato del server"""
    return jsonify({
        'status': 'success',
        'message': 'Running Analyzer Server attivo'
    })


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
        
        logger.info(f"📊 Parametri baseline: Velocità={speed} km/h, FPS={fps}")
        
        # Inizializza PoseEngine
        engine = PoseEngine(
            model_complexity=Config.MEDIAPIPE_MODEL_COMPLEXITY,
            min_detection_confidence=Config.MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=Config.MEDIAPIPE_MIN_TRACKING_CONFIDENCE
        )
        
        # Processa tutti i 5 video
        logger.info("Fase 1: Processing video con PoseEngine...")
        videos_data = []
        for i, video_path in enumerate(video_paths):
            logger.info(f"Processing video {i+1}/5: {os.path.basename(video_path)}")
            video_data = engine.process_video(video_path, fps=fps)
            videos_data.append(video_data)
        
        # Crea statistiche baseline
        logger.info("Fase 2: Creazione statistiche baseline...")
        baseline_stats = engine.create_baseline_stats(videos_data)
        
        # Aggiungi parametri di calibrazione
        baseline_stats['speed_kmh'] = float(speed)
        baseline_stats['fps'] = float(fps)
        baseline_stats['created_at'] = datetime.now().isoformat()
        
        # Salva baseline JSON
        logger.info(f"Salvataggio baseline in: {BASELINE_JSON_PATH}")
        with open(BASELINE_JSON_PATH, 'w') as f:
            json.dump(baseline_stats, f, indent=2)
        
        # Pulisci video temporanei
        for video_path in video_paths:
            if os.path.exists(video_path):
                os.remove(video_path)
        
        logger.info("✅ Baseline creata con successo!")
        
        # Prepara risposta per frontend
        return jsonify({
            'status': 'success',
            'message': 'Baseline creata con successo',
            'baselineCreated': True,
            'baselineRanges': {
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
        })
        
    except Exception as e:
        logger.error(f"Errore nella creazione baseline: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Errore interno: {str(e)}'
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
        
        try:
            speed = float(request.form['speed'])
            fps = float(request.form['fps'])
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'Velocità e FPS devono essere numeri validi'
            }), 400
        
        logger.info(f"📊 Parametri analisi: Velocità={speed} km/h, FPS={fps}")
        
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
        
        logger.info(f"📊 Baseline: Velocità={baseline_speed} km/h, FPS={baseline_fps}")
        
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
        video_data = engine.process_video(filepath, fps=baseline_fps)
        
        # Calcola Z-Scores
        logger.info("Fase 2: Calcolo Z-Scores...")
        z_scores = engine.calculate_z_scores(video_data, baseline_stats)
        
        # Pulisci video temporaneo
        if os.path.exists(filepath):
            os.remove(filepath)
        
        logger.info(f"✅ Analisi completata! Stato: {z_scores['overall_status']}")
        
        # Prepara risposta per frontend
        return jsonify({
            'status': 'success',
            'anomaly_level': z_scores['overall_status'],
            'anomaly_color': z_scores['overall_color'],
            'anomaly_score': z_scores['max_z_score'],
            
            # Metriche principali
            'metrics': {
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
            },
            
            # Dati per grafici temporali
            'charts': {
                'timeline': list(range(video_data['n_frames'])),
                'left_knee_valgus': video_data['left_knee_valgus'],
                'right_knee_valgus': video_data['right_knee_valgus'],
                'pelvic_drop': video_data['pelvic_drop']
            },
            
            # Info video
            'video_info': {
                'n_frames': video_data['n_frames'],
                'frames_with_pose': video_data['frames_with_pose'],
                'fps': video_data['fps'],
                'duration': video_data['n_frames'] / video_data['fps']
            }
        })
        
    except Exception as e:
        logger.error(f"Errore nell'analisi: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Errore interno: {str(e)}'
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
    logger.info(f"Upload folder: {Config.UPLOAD_FOLDER}")
    logger.info(f"Model folder: {Config.MODEL_FOLDER}")
    logger.info(f"Baseline path: {BASELINE_JSON_PATH}")
    logger.info("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )

