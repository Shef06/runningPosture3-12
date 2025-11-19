<script>
  import { analysisStore } from '../../stores/analysisStore.js';
  
  let fileInput;
  let speed = null; // km/h - obbligatorio
  let fps = null; // obbligatorio
  
  $: mainFlow = $analysisStore.mainFlow;
  $: videoFile = $analysisStore.videoFile;
  
  function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
      analysisStore.setVideoFile(file);
    }
  }
  
  function continueToAnalysis() {
    if (!videoFile) return;
    // Valida parametri obbligatori
    if (!speed || speed <= 0) {
      alert('Inserisci la velocità del tapis roulant (km/h)');
      return;
    }
    
    if (!fps || fps <= 0) {
      alert('Inserisci gli FPS del video');
      return;
    }
    
    analysisStore.setCalibration(speed, fps);
    analysisStore.nextStep();
  }
</script>

<div class="step-container">
  <h3>Carica Video e Calibrazione</h3>
  <p class="step-description">
    Carica il video registrato da <strong>vista posteriore</strong> e inserisci i parametri di calibrazione.
  </p>
  
  <div class="instruction-box">
    <h4>📹 Istruzioni per la Registrazione</h4>
    <p><strong>IMPORTANTE:</strong> Il video deve essere registrato esclusivamente da una <strong>vista posteriore</strong>.</p>
    <ul>
      <li>Posizionare la telecamera su un treppiede stabile</li>
      <li>Altezza della telecamera: all'altezza del bacino</li>
      <li>Posizione: direttamente dietro il tapis roulant</li>
      <li>Assicurarsi che tutto il corpo sia visibile nel frame</li>
    </ul>
  </div>
  
  <div class="upload-area">
    <input 
      type="file" 
      bind:this={fileInput}
      accept="video/*" 
      on:change={handleFileSelect}
      id="analysis-video-upload"
      style="display: none;"
    />
    <label for="analysis-video-upload" class="upload-label">
      {#if videoFile}
        <div class="file-selected">
          <span class="icon">✅</span>
          <span class="filename">{videoFile.name}</span>
        </div>
      {:else}
        <div class="upload-placeholder">
          <span class="icon">📁</span>
          <span>Clicca per selezionare video</span>
        </div>
      {/if}
    </label>
  </div>
  
  <div class="calibration-form">
    <h4>Parametri Calibrazione</h4>
    
    <div class="form-group">
      <label for="speed">Velocità Tapis Roulant: <span class="required">*</span></label>
      <input 
        type="number" 
        id="speed" 
        bind:value={speed} 
        min="1" 
        max="50" 
        step="0.1"
        required
        placeholder="es. 12"
      />
      <span class="unit">km/h</span>
    </div>
    
    <div class="form-group">
      <label for="fps">FPS Video: <span class="required">*</span></label>
      <input 
        type="number" 
        id="fps" 
        bind:value={fps} 
        min="15" 
        max="240" 
        step="1"
        required
        placeholder="es. 60"
      />
      <span class="unit">fps</span>
    </div>
  </div>
  
  <button 
    class="btn-primary" 
    on:click={continueToAnalysis}
    disabled={!videoFile || !speed || !fps}
  >
    {#if mainFlow === 'baseline'}
      Continua →
    {:else}
      Avvia Analisi →
    {/if}
  </button>
</div>

<style>
  @import './steps-common.css';

  /* Stili specifici per l'area di upload singolo */
  .upload-label {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    height: 100%;
    padding: 2rem;
    cursor: pointer;
  }

  .upload-placeholder, .file-selected {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    font-size: 1.1rem;
    color: var(--text-main);
  }

  .icon {
    font-size: 1.5rem;
  }

  .filename {
    font-weight: 600;
    color: var(--success-color);
    word-break: break-all;
  }

  .required {
    color: var(--error-color);
  }
  
  input[type="number"]:invalid {
    border-color: var(--error-color);
  }
  
  .instruction-box {
    background: rgba(59, 130, 246, 0.1);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1.5rem;
  }
  
  .instruction-box h4 {
    color: #60a5fa;
    margin-bottom: 0.5rem;
    font-size: 0.95rem;
  }
  
  .instruction-box p {
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    color: var(--text-light);
  }
  
  .instruction-box ul {
    margin: 0.5rem 0 0 1.5rem;
    padding: 0;
    list-style-type: disc;
  }
  
  .instruction-box li {
    margin-bottom: 0.25rem;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.8);
  }

  .calibration-form {
    background: rgba(15, 23, 42, 0.4);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .calibration-form h4 {
    margin-bottom: 1.5rem; 
    color: var(--accent-primary);
    font-size: 1.1rem;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 0.75rem;
  }
</style>