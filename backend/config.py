"""
Configurazione dell'applicazione backend
"""
import os

class Config:
    """Configurazione base dell'applicazione"""
    
    # Cartelle per il salvataggio dei file
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MODEL_FOLDER = os.path.join(BASE_DIR, 'models')
    PROCESSED_VIDEOS_FOLDER = os.path.join(BASE_DIR, 'processed_videos')
    SAVED_ANALYSES_FOLDER = os.path.join(BASE_DIR, 'saved_analyses')
    GHOST_FRAMES_FOLDER = os.path.join(BASE_DIR, 'ghost_frames')
    
    # Estensioni video permesse
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    
    # Dimensione massima file (500 MB)
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024
    
    # Configurazione MediaPipe
    MEDIAPIPE_MODEL_COMPLEXITY = 1
    MEDIAPIPE_MIN_DETECTION_CONFIDENCE = 0.5
    MEDIAPIPE_MIN_TRACKING_CONFIDENCE = 0.5
    
    # Configurazione modello LSTM/GRU (ottimizzato)
    LSTM_UNITS = 64
    LATENT_DIM = 32
    EPOCHS = 50  # Max epoche (fine-tuning usa solo 3-5)
    BATCH_SIZE = 32  # Base (ottimizzato a 64 in training)
    
    @staticmethod
    def init_app():
        """Inizializza le cartelle necessarie"""
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.MODEL_FOLDER, exist_ok=True)
        os.makedirs(Config.PROCESSED_VIDEOS_FOLDER, exist_ok=True)
        os.makedirs(Config.SAVED_ANALYSES_FOLDER, exist_ok=True)
        os.makedirs(Config.GHOST_FRAMES_FOLDER, exist_ok=True)

