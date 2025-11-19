<script>
  import { analysisStore } from '../../stores/analysisStore.js';
  
  let fps = 30;
  let height = 180;
  let mass = 70;
  
  function continueToAnalysis() {
    analysisStore.setCalibration(fps, height, mass);
    analysisStore.nextStep();
  }
</script>

<div class="step-container">
  <h3>Calibrazione Parametri</h3>
  <p class="step-description">
    Inserisci i parametri dell'atleta per l'analisi biomeccanica.
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
      <p class="hint">Frame per secondo del video registrato</p>
    </div>
    
    <div class="form-group">
      <label for="height">Altezza Atleta:</label>
      <input 
        type="number" 
        id="height" 
        bind:value={height} 
        min="100" 
        max="250" 
        step="1"
      />
      <span class="unit">cm</span>
      <p class="hint">Altezza dell'atleta in centimetri</p>
    </div>
    
    <div class="form-group">
      <label for="mass">Massa Atleta:</label>
      <input 
        type="number" 
        id="mass" 
        bind:value={mass} 
        min="30" 
        max="200" 
        step="1"
      />
      <span class="unit">kg</span>
      <p class="hint">Massa corporea dell'atleta</p>
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

