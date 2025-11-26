"""
Script di test per verificare che tutte le dipendenze siano installate correttamente
"""
import sys

def test_imports():
    """Testa tutti gli import necessari"""
    errors = []
    
    print("=" * 60)
    print("Test Import Dipendenze")
    print("=" * 60)
    
    # Test import base
    try:
        import flask
        print(f"✓ Flask {flask.__version__}")
    except ImportError as e:
        print(f"❌ Flask: {e}")
        errors.append("Flask")
    
    try:
        import flask_cors
        print(f"✓ Flask-CORS installato")
    except ImportError as e:
        print(f"❌ Flask-CORS: {e}")
        errors.append("Flask-CORS")
    
    try:
        import numpy
        print(f"✓ NumPy {numpy.__version__}")
    except ImportError as e:
        print(f"❌ NumPy: {e}")
        errors.append("NumPy")
    
    try:
        import cv2
        print(f"✓ OpenCV {cv2.__version__}")
    except ImportError as e:
        print(f"❌ OpenCV: {e}")
        errors.append("OpenCV")
    
    try:
        import scipy
        print(f"✓ SciPy {scipy.__version__}")
    except ImportError as e:
        print(f"❌ SciPy: {e}")
        errors.append("SciPy")
    
    try:
        import mediapipe
        print(f"✓ MediaPipe {mediapipe.__version__}")
    except ImportError as e:
        print(f"❌ MediaPipe: {e}")
        errors.append("MediaPipe")
    
    # Test import moduli locali
    try:
        from config import Config
        print("✓ Config importato")
    except ImportError as e:
        print(f"❌ Config: {e}")
        errors.append("Config")
    
    try:
        from pose_engine import PoseEngine
        print("✓ PoseEngine importato")
    except ImportError as e:
        print(f"❌ PoseEngine: {e}")
        errors.append("PoseEngine")
    
    print("=" * 60)
    
    if errors:
        print(f"❌ Errori trovati: {', '.join(errors)}")
        print("\nPer installare le dipendenze mancanti:")
        print("  pip install -r requirements.txt")
        return False
    else:
        print("✅ Tutte le dipendenze sono installate correttamente!")
        return True

if __name__ == '__main__':
    success = test_imports()
    sys.exit(0 if success else 1)

