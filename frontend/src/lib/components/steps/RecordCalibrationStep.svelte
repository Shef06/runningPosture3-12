<script>
  import { analysisStore } from '../../stores/analysisStore.js';
  
  let fps = 30;
  
  function continueToAnalysis() {
    // Passo null per speed, e fps come secondo argomento
    analysisStore.setCalibration(null, fps);
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
      <label for="fps">FPS Video:</label>
      <input 
        type="number" 
        id="fps" 
        bind:value={fps} 
        min="15" 
        max="120" 
        step="1"
      />
      <span class="unit">fps</span>
      <p class="hint">Frame per secondo della registrazione</p>
    </div>
  </div>
  
  <button class="btn-primary" on:click={continueToAnalysis}>
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
</style>