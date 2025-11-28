<script>
  import { analysisStore } from '../../stores/analysisStore.js';
  
  function selectViewType(viewType) {
    analysisStore.setViewType(viewType);
  }
</script>

<div class="step-container">
  <h3>Scegli la Vista</h3>
  <p class="step-description">
    Seleziona la prospettiva del video per ottimizzare l'analisi biomeccanica.
  </p>
  
  <div class="choice-buttons">
    <button class="choice-btn posterior-btn" on:click={() => selectViewType('posterior')}>
      <div class="icon">🧍</div>
      <div class="title">Vista Posteriore</div>
      <div class="description">
        Analizza valgismo ginocchia e caduta pelvica (vista da dietro)
      </div>
      <div class="metrics-list">
        <span class="metric-tag">Valgismo Ginocchio</span>
        <span class="metric-tag">Caduta Pelvica</span>
        <span class="metric-tag">Cadenza</span>
      </div>
    </button>
    
    <button class="choice-btn lateral-btn" on:click={() => selectViewType('lateral')}>
      <div class="icon">🚶</div>
      <div class="title">Vista Laterale</div>
      <div class="description">
        Analizza overstriding, flessione ginocchio e inclinazione tronco (vista di profilo)
      </div>
      <div class="metrics-list">
        <span class="metric-tag">Overstriding</span>
        <span class="metric-tag">Flessione Ginocchio @ IC</span>
        <span class="metric-tag">Trunk Lean</span>
        <span class="metric-tag">Ground Contact Time</span>
      </div>
    </button>
  </div>
</div>

<style>
  @import './steps-common.css';
  
  .posterior-btn:hover {
    border-color: #8b5cf6;
  }
  
  .lateral-btn:hover {
    border-color: #10b981;
  }
  
  .metrics-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 1rem;
  }
  
  .metric-tag {
    display: inline-block;
    font-size: 0.7rem;
    padding: 0.3rem 0.6rem;
    background: rgba(59, 130, 246, 0.15);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 6px;
    color: var(--text-muted);
    font-weight: 500;
  }
</style>

