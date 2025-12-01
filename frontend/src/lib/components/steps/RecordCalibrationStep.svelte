<script>
  import { analysisStore } from '../../stores/analysisStore.js';
  
  let speed = null; // km/h - obbligatorio
  let fps = 30;
  
  function continueToAnalysis() {
    // Valida parametri obbligatori
    if (!speed || speed <= 0) {
      analysisStore.setError('Inserisci la velocità del tapis roulant (km/h)');
      return;
    }
    
    if (!fps || fps <= 0) {
      analysisStore.setError('Inserisci gli FPS del video');
      return;
    }
    
    // Converti a numero per sicurezza
    const speedNum = typeof speed === 'string' ? parseFloat(speed) : speed;
    const fpsNum = typeof fps === 'string' ? parseFloat(fps) : fps;
    
    // Valida range
    if (isNaN(speedNum) || speedNum < 0.1 || speedNum > 50) {
      analysisStore.setError('Velocità deve essere tra 0.1 e 50 km/h');
      return;
    }
    
    if (isNaN(fpsNum) || fpsNum < 15 || fpsNum > 240) {
      analysisStore.setError('FPS deve essere tra 15 e 240');
      return;
    }
    
    analysisStore.setCalibration(speedNum, fpsNum);
    analysisStore.nextStep();
  }
</script>

<div class="step-container">
  <h3>Calibrazione Parametri</h3>
  <p class="step-description">
    Inserisci i parametri della videocamera per l'analisi.
  </p>
  
  <div class="calibration-form">
    <div class="form-group">
      <label for="speed">Velocità Tapis Roulant: <span class="required">*</span></label>
      <input 
        type="number" 
        id="speed" 
        bind:value={speed} 
        min="0.1" 
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
      <p class="hint">Frame per secondo della registrazione</p>
    </div>
  </div>
  
  <button 
    class="btn-primary" 
    on:click={continueToAnalysis}
    disabled={!speed || !fps}
  >
    Avvia Registrazione →
  </button>
</div>

<style>
  @import './steps-common.css';
  .btn-primary {
    background: var(--error-color);
  }
  
  .btn-primary:hover {
    background: #c0392b;
  }
  
  .form-group {
    margin-bottom: 1.25rem;
  }
  
  input[type="number"] {
    font-size: 1.05rem;
  }
  
  .required {
    color: var(--error-color);
  }
  
  input[type="number"]:invalid {
    border-color: var(--error-color);
  }
</style>