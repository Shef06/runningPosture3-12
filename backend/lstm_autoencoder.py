"""
Modulo per il modello LSTM Autoencoder per il rilevamento di anomalie
Ottimizzato con GRU, fine-tuning e calcolo soglie da validation loss
"""
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from typing import Tuple, Optional, Dict
import os
import logging
import time

# Logger per questo modulo
logger = logging.getLogger('LSTM_AUTOENCODER')


class LSTMAutoencoder:
    """Classe per l'Autoencoder LSTM/GRU per l'apprendimento e rilevamento anomalie"""
    
    # Percorso modello pre-addestrato globale
    PRETRAINED_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'pretrained_autoencoder.h5')
    
    def __init__(self, lstm_units=64, latent_dim=32, use_gru=True, use_cudnn=True, 
                 feature_weights: Optional[Dict[int, float]] = None):
        """
        Inizializza l'autoencoder
        
        Args:
            lstm_units: Numero di unità LSTM/GRU
            latent_dim: Dimensione dello spazio latente
            use_gru: Se True usa GRU (più veloce), altrimenti LSTM
            use_cudnn: Se True usa cuDNN per accelerazione GPU (se disponibile)
            feature_weights: Dizionario con pesi per ogni feature (indice -> peso).
                           Se None, usa pesi di default basati sull'importanza biomeccanica.
                           Features: 0=CPD, 1=BoS, 2=Eversion, 3=TrunkLean, 4=GCT, 5=Cadence
        """
        self.lstm_units = lstm_units
        self.latent_dim = latent_dim
        self.use_gru = use_gru
        self.use_cudnn = use_cudnn
        self.model = None
        self.timesteps = None
        self.n_features = None
        self.thresholds = None  # Soglie dinamiche calcolate dalla baseline
        self.validation_loss = None  # Validation loss per calcolo soglie
        
        # Pesi di default per le features (basati sull'importanza biomeccanica)
        # Features: 0=CPD, 1=BoS, 2=Eversion, 3=TrunkLean, 4=GCT, 5=Cadence
        default_weights = {
            0: 0.50,  # CPD (Contralateral Pelvic Drop) - Alta importanza
            1: 0.15,  # BoS (Base of Support) - Media importanza
            2: 0.15,  # Rearfoot Eversion - Media importanza
            3: 0.20,  # Lateral Trunk Lean - Media importanza
            4: 0.05,  # GCT (Ground Contact Time) - Bassa importanza (spesso interpolato)
            5: 0.05   # Cadenza - Bassa importanza (spesso interpolato)
        }
        
        # Usa pesi forniti o default, poi normalizza
        self.feature_weights_raw = feature_weights if feature_weights is not None else default_weights
        self.feature_weights = self._normalize_weights(self.feature_weights_raw)
        
        # Log dei pesi applicati
        logger.info("⚖️ Pesi features applicati agli errori:")
        feature_names = ['CPD', 'BoS', 'Eversion', 'TrunkLean', 'GCT', 'Cadence']
        for idx, name in enumerate(feature_names):
            if idx < len(self.feature_weights):
                logger.info(f"   {name} (idx {idx}): {self.feature_weights[idx]:.3f}")
    
    def _normalize_weights(self, weights: Dict[int, float]) -> np.ndarray:
        """
        Normalizza i pesi delle features per assicurarsi che la somma sia 1.0
        
        Args:
            weights: Dizionario con pesi per ogni feature (indice -> peso)
            
        Returns:
            Array normalizzato con pesi per ogni feature
        """
        # Crea array di pesi (default 1.0 se feature non specificata)
        max_feature_idx = max(weights.keys()) if weights else 5
        weight_array = np.ones(max_feature_idx + 1)
        
        for idx, weight in weights.items():
            if idx >= 0:
                weight_array[idx] = weight
        
        # Normalizza per somma = 1.0
        total_weight = np.sum(weight_array)
        if total_weight > 0:
            weight_array = weight_array / total_weight
        else:
            # Fallback: pesi uniformi
            weight_array = np.ones_like(weight_array) / len(weight_array)
        
        return weight_array
        
    def build_model(self, timesteps: int, n_features: int):
        """
        Costruisce l'architettura dell'Autoencoder LSTM/GRU ottimizzato
        
        Args:
            timesteps: Numero di timestep nella sequenza
            n_features: Numero di feature per timestep
        """
        self.timesteps = timesteps
        self.n_features = n_features
        
        # Input
        inputs = layers.Input(shape=(timesteps, n_features))
        
        # Scegli layer ricorrente (GRU più veloce, LSTM più accurato)
        if self.use_gru:
            # Usa GRU per velocità (circa 30% più veloce)
            RecurrentLayer = layers.GRU
            logger.info("🔧 Usando GRU per accelerazione")
        else:
            RecurrentLayer = layers.LSTM
            logger.info("🔧 Usando LSTM")
        
        # Encoder con dropout per regolarizzazione
        encoded = RecurrentLayer(
            self.lstm_units, 
            activation='tanh', 
            return_sequences=True,
            dropout=0.1,
            recurrent_dropout=0.1
        )(inputs)
        encoded = RecurrentLayer(
            self.latent_dim, 
            activation='tanh', 
            return_sequences=False,
            dropout=0.1,
            recurrent_dropout=0.1
        )(encoded)
        
        # Repeat vector per il decoder
        decoded = layers.RepeatVector(timesteps)(encoded)
        
        # Decoder
        decoded = RecurrentLayer(
            self.latent_dim, 
            activation='tanh', 
            return_sequences=True,
            dropout=0.1,
            recurrent_dropout=0.1
        )(decoded)
        decoded = RecurrentLayer(
            self.lstm_units, 
            activation='tanh', 
            return_sequences=True,
            dropout=0.1,
            recurrent_dropout=0.1
        )(decoded)
        
        # Output
        outputs = layers.TimeDistributed(layers.Dense(n_features, activation='linear'))(decoded)
        
        # Compila il modello con ottimizzatore Adam ottimizzato
        self.model = keras.Model(inputs, outputs)
        optimizer = keras.optimizers.Adam(learning_rate=0.001, beta_1=0.9, beta_2=0.999)
        self.model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
        
        logger.info("=== Architettura modello ===")
        logger.info(f"  Timesteps: {timesteps}, Features: {n_features}")
        logger.info(f"  LSTM/GRU units: {self.lstm_units}, Latent dim: {self.latent_dim}")
        total_params = self.model.count_params()
        logger.info(f"  Parametri totali: {total_params:,}")
        logger.info(self.model.summary())
        
    def prepare_sequences(self, data: np.ndarray, sequence_length: int) -> np.ndarray:
        """
        Prepara le sequenze di dati per l'addestramento (OTTIMIZZATO: usa numpy avanzato)
        
        Args:
            data: Array (n_frames, n_features)
            sequence_length: Lunghezza delle sequenze da creare
            
        Returns:
            Array (n_sequences, sequence_length, n_features)
        """
        logger.info(f"=== Preparazione sequenze (windowing) ===")
        logger.info(f"  Input shape: {data.shape}, Sequence length: {sequence_length}")
        
        # OTTIMIZZAZIONE: usa numpy stride_tricks per creare view invece di copie
        # Molto più veloce per grandi dataset
        n_frames = len(data)
        n_features = data.shape[1]
        n_sequences = n_frames - sequence_length + 1
        
        # Validazione: verifica che ci siano abbastanza frame
        if n_frames < sequence_length:
            logger.error(f"Frame insufficienti: {n_frames} < {sequence_length}")
            raise ValueError(
                f"Frame insufficienti per l'analisi: {n_frames} < {sequence_length}. "
                f"Il video è troppo breve. Serve almeno {sequence_length} frame per creare sequenze valide."
            )
        
        if n_sequences <= 0:
            logger.error(f"Impossibile creare sequenze: n_frames={n_frames}, sequence_length={sequence_length}")
            raise ValueError(
                f"Impossibile creare sequenze: n_frames={n_frames}, sequence_length={sequence_length}. "
                f"Risultato: {n_sequences} sequenze."
            )
        
        # OTTIMIZZAZIONE: usa numpy avanzato per creare sliding window (più veloce)
        try:
            from numpy.lib.stride_tricks import sliding_window_view
            # sliding_window_view è disponibile in numpy >= 1.20
            # Crea sliding window lungo l'asse temporale (axis=0)
            sequences = sliding_window_view(data, window_shape=sequence_length, axis=0)
            
            # Verifica e correggi la shape se necessario
            # sliding_window_view dovrebbe creare (n_sequences, sequence_length, n_features)
            # ma in alcune versioni può creare (n_sequences, n_features, sequence_length)
            if len(sequences.shape) == 3:
                expected_shape = (n_sequences, sequence_length, n_features)
                if sequences.shape == expected_shape:
                    # Shape corretta
                    logger.info(f"  Output shape: {sequences.shape}")
                    logger.info(f"  Numero sequenze generate: {n_sequences}")
                    return sequences
                elif sequences.shape == (n_sequences, n_features, sequence_length):
                    # Shape invertita: trasponi
                    logger.warning(f"⚠️ Shape invertita rilevata: {sequences.shape}, correggo a {expected_shape}")
                    sequences = np.transpose(sequences, (0, 2, 1))
                    logger.info(f"  Output shape: {sequences.shape}")
                    logger.info(f"  Numero sequenze generate: {n_sequences}")
                    return sequences
                else:
                    # Shape inattesa: usa fallback
                    logger.warning(f"⚠️ Shape inattesa: {sequences.shape}, uso metodo tradizionale")
                    sequences = np.array([data[i:i + sequence_length] for i in range(n_sequences)])
                    logger.info(f"  Output shape: {sequences.shape}")
                    logger.info(f"  Numero sequenze generate: {n_sequences}")
                    return sequences
            else:
                # Shape non 3D: usa fallback
                logger.warning(f"⚠️ Shape non 3D: {sequences.shape}, uso metodo tradizionale")
                sequences = np.array([data[i:i + sequence_length] for i in range(n_sequences)])
                logger.info(f"  Output shape: {sequences.shape}")
                logger.info(f"  Numero sequenze generate: {n_sequences}")
                return sequences
        except (ImportError, AttributeError):
            # Fallback: metodo tradizionale (più lento ma compatibile)
            logger.info("  Uso metodo tradizionale per creazione sequenze")
            sequences = np.array([data[i:i + sequence_length] for i in range(n_sequences)])
            logger.info(f"  Output shape: {sequences.shape}")
            logger.info(f"  Numero sequenze generate: {n_sequences}")
            return sequences
    
    def load_pretrained_model(self) -> bool:
        """
        Carica il modello pre-addestrato globale se disponibile
        
        Returns:
            True se il modello è stato caricato, False altrimenti
        """
        if os.path.exists(self.PRETRAINED_MODEL_PATH):
            try:
                self.model = keras.models.load_model(self.PRETRAINED_MODEL_PATH)
                # Carica metadati
                metadata_path = self.PRETRAINED_MODEL_PATH.replace('.h5', '_metadata.npy')
                if os.path.exists(metadata_path):
                    metadata = np.load(metadata_path, allow_pickle=True).item()
                    self.timesteps = metadata.get('timesteps')
                    self.n_features = metadata.get('n_features')
                    self.lstm_units = metadata.get('lstm_units', self.lstm_units)
                    self.latent_dim = metadata.get('latent_dim', self.latent_dim)
                    # Carica i pesi delle features se disponibili
                    if 'feature_weights_raw' in metadata:
                        self.feature_weights_raw = metadata['feature_weights_raw']
                        self.feature_weights = self._normalize_weights(self.feature_weights_raw)
                logger.info(f"✓ Modello pre-addestrato caricato: {os.path.basename(self.PRETRAINED_MODEL_PATH)}")
                return True
            except Exception as e:
                logger.warning(f"⚠ Errore nel caricare modello pre-addestrato: {e}")
        return False
    
    def train(self, data: np.ndarray, sequence_length: int = 30, epochs: int = 5, 
              batch_size: int = 64, validation_split: float = 0.2, fine_tune: bool = True):
        """
        Addestra l'autoencoder sui dati della baseline (ottimizzato con fine-tuning)
        
        Args:
            data: Array (n_frames, n_features) dei dati di training
            sequence_length: Lunghezza delle sequenze
            epochs: Numero di epoche di training (default 5 per fine-tuning)
            batch_size: Dimensione del batch (ottimizzato a 64)
            validation_split: Frazione dei dati da usare per la validazione
            fine_tune: Se True, carica modello pre-addestrato e fa fine-tuning
        """
        # Prepara le sequenze
        sequences = self.prepare_sequences(data, sequence_length)
        
        print(f"Forma delle sequenze: {sequences.shape}")
        
        # Prova a caricare modello pre-addestrato per fine-tuning
        if fine_tune and self.model is None:
            if self.load_pretrained_model():
                # Fine-tuning: congela encoder, addestra solo decoder
                logger.info("🔧 Fine-tuning: addestramento solo decoder...")
                # Congela encoder (primi 2 layer GRU/LSTM)
                for layer in self.model.layers[:2]:
                    layer.trainable = False
                # Ricompila per applicare cambiamenti
                optimizer = keras.optimizers.Adam(learning_rate=0.0001, beta_1=0.9, beta_2=0.999)  # LR più basso per fine-tuning
                self.model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
            else:
                # Nessun modello pre-addestrato, costruisci nuovo modello
                logger.info("🔧 Nessun modello pre-addestrato trovato, addestramento da zero...")
                self.build_model(sequence_length, data.shape[1])
        elif self.model is None:
            # Costruisci nuovo modello
            self.build_model(sequence_length, data.shape[1])
        else:
            # Modello già caricato, verifica compatibilità
            if self.timesteps != sequence_length or self.n_features != data.shape[1]:
                logger.warning("⚠ Modello esistente non compatibile, ricostruendo...")
                self.build_model(sequence_length, data.shape[1])
        
        # Early stopping più aggressivo per fine-tuning
        early_stopping = keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=3 if fine_tune else 10,
            restore_best_weights=True,
            min_delta=1e-6
        )
        
        # ReduceLROnPlateau per ottimizzazione learning rate
        reduce_lr = keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=2,
            min_lr=1e-7,
            verbose=1
        )
        
        # Addestra il modello
        logger.info(f"=== Inizio training autoencoder ===")
        logger.info(f"  Sequenze training: {sequences.shape[0]}")
        logger.info(f"  Batch size: {batch_size}, Epochs: {epochs}")
        logger.info(f"  Validation split: {validation_split*100:.1f}%")
        logger.info(f"  Early stopping: patience={early_stopping.patience}")
        
        start_time = time.time()
        history = self.model.fit(
            sequences, sequences,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=[early_stopping, reduce_lr],
            verbose=1
        )
        elapsed_time = time.time() - start_time
        
        # Log risultati training per ogni epoca
        logger.info(f"=== Risultati training ===")
        train_losses = history.history['loss']
        val_losses = history.history['val_loss']
        
        for epoch, (train_loss, val_loss) in enumerate(zip(train_losses, val_losses), 1):
            logger.info(f"  Epoca {epoch}/{len(train_losses)}: train_loss={train_loss:.6f}, val_loss={val_loss:.6f}")
        
        # Salva validation loss per calcolo soglie
        if len(history.history['val_loss']) > 0:
            self.validation_loss = min(history.history['val_loss'])
            final_train_loss = train_losses[-1]
            final_val_loss = val_losses[-1]
            logger.info(f"  Loss finale: train={final_train_loss:.6f}, val={final_val_loss:.6f}")
            logger.info(f"  Validation loss minimo: {self.validation_loss:.6f}")
        
        # Verifica early stopping
        if len(train_losses) < epochs:
            logger.info(f"  Early stopping attivato all'epoca {len(train_losses)}/{epochs}")
        
        logger.info(f"  Tempo totale addestramento: {elapsed_time:.2f}s ({elapsed_time/60:.1f} min)")
        logger.info(f"=== Training completato ===")
        
        return history
    
    def predict(self, data: np.ndarray, sequence_length: int = 30) -> np.ndarray:
        """
        Predice (ricostruisce) le sequenze
        
        Args:
            data: Array (n_frames, n_features)
            sequence_length: Lunghezza delle sequenze
            
        Returns:
            Array ricostruito
        """
        if self.model is None:
            raise ValueError("Il modello deve essere addestrato o caricato prima della predizione")
        
        sequences = self.prepare_sequences(data, sequence_length)
        return self.model.predict(sequences)
    
    def calculate_reconstruction_error(self, data: np.ndarray, sequence_length: int = 30) -> float:
        """
        Calcola l'errore di ricostruzione (MSE pesato) per rilevare anomalie
        Usa pesi diversi per ogni feature basati sull'importanza biomeccanica
        
        Args:
            data: Array (n_frames, n_features)
            sequence_length: Lunghezza delle sequenze
            
        Returns:
            Errore MSE medio pesato
        """
        logger.info(f"=== Calcolo anomaly score ===")
        logger.info(f"  Input shape: {data.shape}, Sequence length: {sequence_length}")
        
        sequences = self.prepare_sequences(data, sequence_length)
        logger.info(f"  Sequenze create: {sequences.shape[0]}")
        
        logger.info(f"  Esecuzione predizione modello...")
        reconstructed = self.model.predict(sequences, verbose=0)
        
        # Calcola errore quadratico per ogni timestep e feature
        squared_errors = np.square(sequences - reconstructed)  # Shape: (n_sequences, timesteps, n_features)
        
        # Applica pesi alle features (solo se abbiamo il numero corretto di features)
        n_features = sequences.shape[2]
        if n_features <= len(self.feature_weights):
            # Crea array di pesi con la dimensione corretta
            weights = self.feature_weights[:n_features]
            # Normalizza i pesi per il numero effettivo di features
            weights = weights / np.sum(weights) * n_features
            
            # Applica pesi: moltiplica per pesi lungo l'asse delle features (axis=2)
            weighted_errors = squared_errors * weights[np.newaxis, np.newaxis, :]
            logger.info(f"  Pesi features applicati: {n_features} features")
        else:
            # Se numero features non corrisponde, usa pesi uniformi
            weighted_errors = squared_errors
            logger.warning(f"  ⚠️ Numero features non corrisponde, uso pesi uniformi")
        
        # Calcola MSE pesato per ogni sequenza (media su timesteps e features pesate)
        mse_per_sequence = np.mean(weighted_errors, axis=(1, 2))
        
        # Statistiche MSE
        mse_mean = float(np.mean(mse_per_sequence))
        mse_min = float(np.min(mse_per_sequence))
        mse_max = float(np.max(mse_per_sequence))
        mse_std = float(np.std(mse_per_sequence))
        
        logger.info(f"  MSE per sequenza: mean={mse_mean:.6f}, min={mse_min:.6f}, max={mse_max:.6f}, std={mse_std:.6f}")
        logger.info(f"  MSE medio finale (anomaly score): {mse_mean:.6f}")
        
        # Confronto con soglia se disponibile
        if self.thresholds:
            e_max = self.thresholds['e_max']
            level, color = self.get_anomaly_level(mse_mean, self.thresholds)
            logger.info(f"  Soglia E_max: {e_max:.6f}")
            logger.info(f"  Livello anomalia: {level} (score={mse_mean:.6f}, soglia={e_max:.6f})")
        else:
            logger.warning(f"  ⚠️ Soglie non disponibili per confronto")
        
        logger.info(f"=== Calcolo anomaly score completato ===")
        
        # Ritorna la media degli MSE pesati
        return mse_mean
    
    def calculate_baseline_errors(self, data: np.ndarray, sequence_length: int = 30) -> np.ndarray:
        """
        Calcola gli errori di ricostruzione (MSE pesato) per ogni sequenza dei dati di baseline
        Usa pesi diversi per ogni feature basati sull'importanza biomeccanica
        
        Args:
            data: Array (n_frames, n_features) dei dati di baseline
            sequence_length: Lunghezza delle sequenze
            
        Returns:
            Array di errori MSE pesati per ogni sequenza
        """
        if self.model is None:
            raise ValueError("Il modello deve essere addestrato prima")
        
        sequences = self.prepare_sequences(data, sequence_length)
        reconstructed = self.model.predict(sequences, verbose=0)
        
        # Calcola errore quadratico per ogni timestep e feature
        squared_errors = np.square(sequences - reconstructed)  # Shape: (n_sequences, timesteps, n_features)
        
        # Applica pesi alle features (solo se abbiamo il numero corretto di features)
        n_features = sequences.shape[2]
        if n_features <= len(self.feature_weights):
            # Crea array di pesi con la dimensione corretta
            weights = self.feature_weights[:n_features]
            # Normalizza i pesi per il numero effettivo di features
            weights = weights / np.sum(weights) * n_features
            
            # Applica pesi: moltiplica per pesi lungo l'asse delle features (axis=2)
            weighted_errors = squared_errors * weights[np.newaxis, np.newaxis, :]
        else:
            # Se numero features non corrisponde, usa pesi uniformi
            weighted_errors = squared_errors
        
        # Calcola MSE pesato per ogni sequenza (media su timesteps e features pesate)
        mse_per_sequence = np.mean(weighted_errors, axis=(1, 2))
        
        return mse_per_sequence
    
    def calculate_dynamic_thresholds(self, data: np.ndarray, sequence_length: int = 30, 
                                      use_statistical: bool = True, 
                                      use_validation_loss: bool = True) -> dict:
        """
        Calcola le soglie dinamiche basate sulla distribuzione degli errori di baseline
        OTTIMIZZATO: usa validation loss se disponibile per evitare inference completa
        
        Args:
            data: Array (n_frames, n_features) dei dati di baseline
            sequence_length: Lunghezza delle sequenze
            use_statistical: Se True usa μ + 3σ, altrimenti usa E_max
            use_validation_loss: Se True e validation_loss disponibile, usa quello invece di inference
            
        Returns:
            Dizionario con le soglie calcolate
        """
        logger.info(f"=== Calcolo soglie dinamiche ===")
        
        # OTTIMIZZAZIONE: usa validation loss se disponibile (molto più veloce)
        if use_validation_loss and self.validation_loss is not None:
            logger.info("🚀 Metodo: validation loss (ottimizzato)")
            # Usa validation loss come base, con fattore di sicurezza
            mu = self.validation_loss
            # Stima sigma basata su validation loss (approssimazione)
            sigma = mu * 0.3  # Assumiamo ~30% di variabilità
            e_max = mu + 3 * sigma
            
            # Calcola soglie basate su validation loss (senza tolleranza)
            thresholds = {
                'e_max': float(e_max),
                'mu': float(mu),
                'sigma': float(sigma),
                'min_error': float(mu * 0.5),  # Stima
                'max_error': float(e_max * 1.2),  # Stima
                'optimal': float(e_max),  # < E_max
                'good': float(e_max * 1.1),  # E_max < x < E_max * 1.1
                'moderate': float(e_max * 1.2),  # E_max * 1.1 < x < E_max * 1.2
                'attention': float(e_max * 1.3),  # E_max * 1.2 < x < E_max * 1.3
                'critical': float(e_max * 1.3)  # >= E_max * 1.3
            }
            
            logger.info(f"  Validation loss (μ): {mu:.6f}")
            logger.info(f"  Deviazione std stimata (σ): {sigma:.6f}")
            logger.info(f"  E_max (soglia ottimale): {e_max:.6f}")
            logger.info(f"  Metodo: μ + 3σ (statistico)")
            logger.info(f"  Soglie calcolate:")
            logger.info(f"    Ottimale: < {thresholds['optimal']:.6f}")
            logger.info(f"    Buono: < {thresholds['good']:.6f}")
            logger.info(f"    Moderato: < {thresholds['moderate']:.6f}")
            logger.info(f"    Attenzione: < {thresholds['attention']:.6f}")
            logger.info(f"    Critico: >= {thresholds['critical']:.6f}")
            
            return thresholds
        
        # Metodo tradizionale: calcola errori su tutte le sequenze (più lento)
        logger.info("📊 Metodo: inference completa (statistico)")
        start_time = time.time()
        errors = self.calculate_baseline_errors(data, sequence_length)
        elapsed_time = time.time() - start_time
        logger.info(f"  Tempo calcolo errori: {elapsed_time:.2f}s")
        logger.info(f"  Sequenze analizzate: {len(errors)}")
        
        if use_statistical:
            # Metodo statistico: μ + 3σ (copre 99.7% dei dati)
            mu = np.mean(errors)
            sigma = np.std(errors)
            e_max = mu + 3 * sigma
            method_name = "μ + 3σ (statistico)"
        else:
            # Metodo semplice: errore massimo osservato
            e_max = np.max(errors)
            method_name = "E_max (massimo osservato)"
        
        # Calcola statistiche per logging
        mu = np.mean(errors)
        sigma = np.std(errors)
        min_error = np.min(errors)
        max_error = np.max(errors)
        
        thresholds = {
            'e_max': float(e_max),
            'mu': float(mu),
            'sigma': float(sigma),
            'min_error': float(min_error),
            'max_error': float(max_error),
            'optimal': float(e_max),  # < E_max
            'good': float(e_max * 1.1),  # E_max < x < E_max * 1.1
            'moderate': float(e_max * 1.2),  # E_max * 1.1 < x < E_max * 1.2
            'attention': float(e_max * 1.3),  # E_max * 1.2 < x < E_max * 1.3
            'critical': float(e_max * 1.3)  # >= E_max * 1.3
        }
        
        logger.info(f"  Media (μ): {mu:.6f}, Deviazione std (σ): {sigma:.6f}")
        logger.info(f"  Range errori: [{min_error:.6f}, {max_error:.6f}]")
        logger.info(f"  E_max (soglia ottimale): {e_max:.6f}")
        logger.info(f"  Metodo: {method_name}")
        logger.info(f"  Soglie calcolate:")
        logger.info(f"    Ottimale: < {thresholds['optimal']:.6f}")
        logger.info(f"    Buono: < {thresholds['good']:.6f}")
        logger.info(f"    Moderato: < {thresholds['moderate']:.6f}")
        logger.info(f"    Attenzione: < {thresholds['attention']:.6f}")
        logger.info(f"    Critico: >= {thresholds['critical']:.6f}")
        logger.info(f"=== Calcolo soglie completato ===")
        
        return thresholds
    
    def get_anomaly_level(self, error: float, thresholds: dict) -> tuple:
        """
        Determina il livello di anomalia basato sulle soglie dinamiche
        
        Args:
            error: Errore di ricostruzione calcolato
            thresholds: Dizionario con le soglie
            
        Returns:
            Tupla (level, color)
        """
        if error < thresholds['optimal']:
            return ("Ottimale", "#2ecc71")  # verde
        elif error < thresholds['good']:
            return ("Buono", "#90EE90")  # verde chiaro
        elif error < thresholds['moderate']:
            return ("Moderato", "#f39c12")  # giallo/arancione
        elif error < thresholds['attention']:
            return ("Attenzione", "#e67e22")  # arancione
        else:
            return ("Critico", "#e74c3c")  # rosso
    
    def save_model(self, filepath: str, thresholds: dict = None):
        """
        Salva il modello su disco
        
        Args:
            filepath: Percorso dove salvare il modello
            thresholds: Dizionario con le soglie dinamiche (opzionale)
        """
        if self.model is None:
            raise ValueError("Nessun modello da salvare")
        
        # Salva il modello
        self.model.save(filepath)
        
        # Salva anche i metadati
        metadata_path = filepath.replace('.h5', '_metadata.npy')
        metadata = {
            'timesteps': self.timesteps,
            'n_features': self.n_features,
            'lstm_units': self.lstm_units,
            'latent_dim': self.latent_dim,
            'thresholds': thresholds,  # Aggiungi le soglie
            'feature_weights_raw': self.feature_weights_raw  # Salva i pesi delle features
        }
        np.save(metadata_path, metadata)
        
        logger.info(f"Modello salvato in: {os.path.basename(filepath)}")
        if thresholds:
            logger.info(f"Soglie dinamiche salvate: E_max = {thresholds['e_max']:.6f}")
        logger.info(f"Pesi features salvati: {len(self.feature_weights)} features")
    
    def load_model(self, filepath: str):
        """
        Carica il modello da disco
        
        Args:
            filepath: Percorso del modello da caricare
        """
        # Carica il modello
        self.model = keras.models.load_model(filepath)
        
        # Carica i metadati
        metadata_path = filepath.replace('.h5', '_metadata.npy')
        if os.path.exists(metadata_path):
            metadata = np.load(metadata_path, allow_pickle=True).item()
            self.timesteps = metadata['timesteps']
            self.n_features = metadata['n_features']
            self.lstm_units = metadata['lstm_units']
            self.latent_dim = metadata['latent_dim']
            self.thresholds = metadata.get('thresholds', None)  # Carica le soglie
            
            # Carica i pesi delle features se disponibili
            if 'feature_weights_raw' in metadata:
                self.feature_weights_raw = metadata['feature_weights_raw']
                self.feature_weights = self._normalize_weights(self.feature_weights_raw)
                logger.info(f"✓ Pesi features caricati: {len(self.feature_weights)} features")
            else:
                # Se non ci sono pesi salvati, usa i default (già inizializzati nel __init__)
                logger.warning("⚠ Pesi features non trovati nei metadati, uso pesi default")
            
            if self.thresholds:
                logger.info(f"Soglie dinamiche caricate: E_max = {self.thresholds['e_max']:.6f}")
        
        logger.info(f"Modello caricato da: {os.path.basename(filepath)}")

    def get_error_series(self, data: np.ndarray, sequence_length: int = 30) -> Dict[str, np.ndarray]:
        """
        Calcola la serie temporale degli errori per grafici
        Restituisce sia l'errore totale (AS) che l'errore per feature nel tempo
        """
        sequences = self.prepare_sequences(data, sequence_length)
        reconstructed = self.model.predict(sequences, verbose=0)
        
        # Calcola errore quadratico (MSE) per ogni sequenza
        # Shape: (n_sequences, timesteps, n_features)
        squared_errors = np.square(sequences - reconstructed)
        
        # 1. Anomaly Score Totale nel tempo (media pesata delle features)
        # Applica pesi
        n_features = sequences.shape[2]
        if n_features <= len(self.feature_weights):
            weights = self.feature_weights[:n_features]
            weights = weights / np.sum(weights) * n_features
            weighted_errors = squared_errors * weights[np.newaxis, np.newaxis, :]
        else:
            weighted_errors = squared_errors
            
        # Media su timesteps e features per ottenere un valore per ogni istante t
        # (n_sequences,)
        as_over_time = np.mean(weighted_errors, axis=(1, 2))
        
        # 2. MSE per singola feature nel tempo
        # Media solo sui timesteps -> (n_sequences, n_features)
        mse_per_feature = np.mean(squared_errors, axis=1)
        
        return {
            'total_as': as_over_time,
            'per_feature': mse_per_feature
        }

