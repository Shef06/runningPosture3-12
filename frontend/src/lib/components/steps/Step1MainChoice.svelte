<script>
  import { analysisStore } from '../../stores/analysisStore.js';
  
  function selectMainFlow(flow) {
    analysisStore.setMainFlow(flow);
  }
</script>

<div class="step-container">
  <h3>Scegli l'Azione</h3>
  <p class="step-description">
    Seleziona se vuoi creare una nuova baseline o analizzare un video rispetto alla baseline esistente.
  </p>
  
  <div class="choice-buttons">
    <button class="choice-btn baseline-btn" on:click={() => selectMainFlow('baseline')}>
      <div class="icon">🎯</div>
      <div class="title">Genera Nuova Baseline</div>
      <div class="description">
        Crea un modello di riferimento dalla tua corsa ottimale
      </div>
    </button>
    
    <button class="choice-btn analyze-btn" on:click={() => selectMainFlow('analyze')}>
      <div class="icon">🔍</div>
      <div class="title">Analizza Video</div>
      <div class="description">
        Confronta un video con la baseline esistente
      </div>
    </button>
  </div>
</div>

<style>
  @import './steps-common.css';
  
  .baseline-btn:hover {
    border-color: var(--success-color);
  }
  
  .analyze-btn:hover {
    border-color: var(--accent-color);
  }
</style>

