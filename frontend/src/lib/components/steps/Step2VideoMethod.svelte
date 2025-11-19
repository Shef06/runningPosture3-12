<script>
  import { analysisStore } from '../../stores/analysisStore.js';
  
  $: mainFlow = $analysisStore.mainFlow;
  
  function selectMethod(method) {
    analysisStore.setVideoMethod(method);
  }
</script>

<div class="step-container">
  <h3>Scegli Metodo di Acquisizione</h3>
  <p class="step-description">
    {#if mainFlow === 'baseline'}
      Come vuoi fornire i video per creare la baseline?
    {:else}
      Come vuoi fornire il video da analizzare?
    {/if}
  </p>
  
  <div class="choice-buttons">
    <button class="choice-btn upload-btn" on:click={() => selectMethod('upload')}>
      <div class="icon">📁</div>
      <div class="title">Carica Video</div>
      <div class="description">
        Carica un file video dal tuo computer
      </div>
    </button>
    
    <button class="choice-btn record-btn" on:click={() => selectMethod('record')}>
      <div class="icon">📹</div>
      <div class="title">Registra Video</div>
      <div class="description">
        Registra un nuovo video utilizzando la webcam
      </div>
    </button>
  </div>
</div>

<style>
  @import './steps-common.css';
  
  .upload-btn:hover {
    border-color: var(--accent-color);
  }
  
  .record-btn:hover {
    border-color: var(--error-color);
  }
</style>

