"""
Script per creare il modello pre-addestrato globale
Questo modello viene addestrato una volta su dati aggregati e poi usato per fine-tuning
"""
import os
import sys
import numpy as np
from lstm_autoencoder import LSTMAutoencoder
from config import Config

# Inizializza cartelle
Config.init_app()

def create_pretrained_model():
    """
    Crea un modello pre-addestrato globale addestrato su dati sintetici/di esempio
    Questo modello può essere poi usato per fine-tuning rapido su nuovi atleti
    """
    print("=" * 60)
    print("🔧 Creazione modello pre-addestrato globale")
    print("=" * 60)
    
    # Genera dati sintetici di esempio (simula features biomeccaniche)
    # In produzione, questo potrebbe essere addestrato su un dataset aggregato di più atleti
    print("\n📊 Generazione dati sintetici di esempio...")
    n_samples = 5000  # Numero di frame sintetici
    n_features = 8  # 8 features biomeccaniche
    
    # Genera sequenze temporali realistiche con pattern di camminata/corsa
    np.random.seed(42)  # Per riproducibilità
    
    # Simula pattern ciclici (passo)
    t = np.linspace(0, 20, n_samples)  # 20 secondi di dati
    features = np.zeros((n_samples, n_features))
    
    # CPD: variazione sinusoidale
    features[:, 0] = 2 + 1.5 * np.sin(2 * np.pi * t / 2) + 0.3 * np.random.randn(n_samples)
    
    # BoS: variazione durante il passo
    features[:, 1] = 0.15 + 0.05 * np.sin(2 * np.pi * t / 2) + 0.01 * np.random.randn(n_samples)
    
    # Eversione: variazione
    features[:, 2] = 5 + 3 * np.sin(2 * np.pi * t / 2.5) + 0.5 * np.random.randn(n_samples)
    
    # Trunk lean: variazione
    features[:, 3] = 1 + 0.5 * np.sin(2 * np.pi * t / 2.2) + 0.2 * np.random.randn(n_samples)
    
    # GCT: variazione ciclica
    features[:, 4] = 200 + 30 * np.sin(2 * np.pi * t / 2) + 5 * np.random.randn(n_samples)
    
    # Cadenza: relativamente costante
    features[:, 5] = 180 + 10 * np.sin(2 * np.pi * t / 3) + 2 * np.random.randn(n_samples)
    
    # KASR: variazione
    features[:, 6] = 1.0 + 0.1 * np.sin(2 * np.pi * t / 2.3) + 0.05 * np.random.randn(n_samples)
    
    # FPPA: variazione
    features[:, 7] = 5 + 2 * np.sin(2 * np.pi * t / 2.1) + 0.3 * np.random.randn(n_samples)
    
    print(f"✓ Dati sintetici generati: {features.shape}")
    
    # Crea e addestra modello
    print("\n🔧 Costruzione e addestramento modello...")
    autoencoder = LSTMAutoencoder(
        lstm_units=Config.LSTM_UNITS,
        latent_dim=Config.LATENT_DIM,
        use_gru=True,  # Usa GRU per velocità
        use_cudnn=True
    )
    
    # Addestra da zero (più epoche per modello globale)
    history = autoencoder.train(
        data=features,
        sequence_length=30,
        epochs=20,  # Più epoche per modello pre-addestrato
        batch_size=64,
        fine_tune=False  # Addestramento da zero
    )
    
    # Salva modello pre-addestrato
    pretrained_path = LSTMAutoencoder.PRETRAINED_MODEL_PATH
    os.makedirs(os.path.dirname(pretrained_path), exist_ok=True)
    
    autoencoder.save_model(pretrained_path, thresholds=None)  # Nessuna soglia per modello globale
    
    # Salva metadati
    metadata_path = pretrained_path.replace('.h5', '_metadata.npy')
    metadata = {
        'timesteps': 30,
        'n_features': n_features,
        'lstm_units': Config.LSTM_UNITS,
        'latent_dim': Config.LATENT_DIM,
        'use_gru': True
    }
    np.save(metadata_path, metadata)
    
    print(f"\n✓ Modello pre-addestrato salvato: {pretrained_path}")
    print(f"✓ Metadati salvati: {metadata_path}")
    print(f"\n📊 Statistiche addestramento:")
    print(f"   Final loss: {history.history['loss'][-1]:.6f}")
    print(f"   Final val_loss: {history.history['val_loss'][-1]:.6f}")
    print("\n" + "=" * 60)
    print("✅ Modello pre-addestrato creato con successo!")
    print("   Questo modello verrà usato per fine-tuning rapido su nuovi atleti")
    print("=" * 60)

if __name__ == '__main__':
    create_pretrained_model()

