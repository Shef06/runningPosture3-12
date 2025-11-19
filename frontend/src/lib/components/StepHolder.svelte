<script>
  import { analysisStore } from '../stores/analysisStore.js';
  import Step1MainChoice from './steps/Step1MainChoice.svelte';
  import Step2VideoMethod from './steps/Step2VideoMethod.svelte';
  import Step3CameraSetup from './steps/Step3CameraSetup.svelte';
  import Step3Calibration from './steps/Step3Calibration.svelte';
  import Step3BaselineUpload from './steps/Step3BaselineUpload.svelte';
  import Step4Calibration from './steps/Step4Calibration.svelte';
  import Step4Analysis from './steps/Step4Analysis.svelte';
  import Step5Analysis from './steps/Step5Analysis.svelte';
  import Step6Results from './steps/Step6Results.svelte';
  
  $: currentStep = $analysisStore.currentStep;
  $: mainFlow = $analysisStore.mainFlow;
  $: videoMethod = $analysisStore.videoMethod;
  $: loading = $analysisStore.loading;
  
  $: stepInfo = calculateStepInfo(currentStep, mainFlow, videoMethod);
  
  $: showBaselineLoading = loading && mainFlow === 'baseline';
  $: showAnalysisLoading = loading && mainFlow === 'analyze';
  
  function calculateStepInfo(step, flow, method) {
    if (!flow || !method) {
      return { current: step, total: 6 };
    }
    
    if (method === 'upload') {
      const stepMap = {
        1: { current: 1, total: 5 },
        2: { current: 2, total: 5 },
        3: { current: 3, total: 5 },
        4: { current: 4, total: 5 },
        6: { current: 5, total: 5 }
      };
      return stepMap[step] || { current: step, total: 5 };
    }
    
    if (method === 'record') {
      return { current: step, total: 6 };
    }
    
    return { current: step, total: 6 };
  }
  
  function goBack() {
    analysisStore.prevStep();
  }
  
  function getStepComponent() {
    if (currentStep === 1) return Step1MainChoice;
    if (currentStep === 2) return Step2VideoMethod;
    if (currentStep === 3) {
      if (videoMethod === 'record') return Step3CameraSetup;
      else {
        if (mainFlow === 'baseline') return Step3BaselineUpload;
        else return Step3Calibration;
      }
    }
    if (currentStep === 4) {
      if (videoMethod === 'record') return Step4Calibration;
      else return Step4Analysis;
    }
    if (currentStep === 5) return Step5Analysis;
    if (currentStep === 6) return Step6Results;
    return Step1MainChoice;
  }
  
  function restartFlow() {
    analysisStore.reset();
  }
</script>

<div class="step-holder">
  <div class="step-header">
    <div class="header-left">
      <h2>Configurazione</h2>
      <p class="step-subtitle">Passaggio {stepInfo.current} di {stepInfo.total}</p>
    </div>
    <div class="header-right">
      {#if currentStep > 1}
        <button class="btn-back" on:click={goBack}>
          Indietro
        </button>
      {/if}
    </div>
  </div>
  
  <div class="step-content">
    <svelte:component this={getStepComponent()} />
    
    {#if showBaselineLoading || showAnalysisLoading}
      <div class="loading-overlay">
        <div class="loading-content">
          <div class="loading-spinner"></div>
          {#if mainFlow === 'baseline'}
            <h3>Creazione Baseline</h3>
            <p>Elaborazione dei 5 video e calcolo del modello...</p>
            <div class="loading-steps">
              <div class="loading-step">Estrazione keypoint 3D</div>
              <div class="loading-step">Calcolo angoli</div>
              <div class="loading-step">Addestramento AI</div>
            </div>
          {:else}
            <h3>Analisi in Corso</h3>
            <p>Confronto con la baseline...</p>
            <div class="loading-steps">
              <div class="loading-step">Tracking scheletrico</div>
              <div class="loading-step">Calcolo score</div>
            </div>
          {/if}
        </div>
      </div>
    {/if}
  </div>
  
  <div class="step-footer">
    {#if currentStep > 1}
      <button class="btn-restart" on:click={restartFlow}>
        Ricomincia da capo
      </button>
    {/if}
  </div>
</div>

<style>
  .step-holder {
    height: 100%;
    display: flex;
    flex-direction: column;
    /* Il background è gestito dal parent */
  }
  
  .step-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    /* AUMENTATO: Padding orizzontale allineato a step-container (2.5rem) */
    padding: 1.5rem 2.5rem; 
    border-bottom: 1px solid var(--border-color);
    background: rgba(15, 23, 42, 0.5); /* Leggermente più scuro */
    backdrop-filter: blur(10px);
  }
  
  .header-left h2 {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.1em; /* Spaziatura lettere più ampia */
    color: #64748b; /* Colore più spento per l'etichetta */
    margin-bottom: 0.4rem;
    font-weight: 700;
  }
  
  .step-subtitle {
    font-size: 1.1rem;
    color: var(--text-main);
    font-weight: 700;
    margin: 0;
  }
  
  .btn-back {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border-color);
    color: var(--text-muted);
    padding: 0.6rem 1rem;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    transition: all 0.2s;
    cursor: pointer;
  }
  
  .btn-back:hover {
    background: rgba(255,255,255,0.1);
    color: white;
    border-color: rgba(255,255,255,0.4);
    transform: translateX(-2px);
  }
  
  .step-content {
    flex: 1;
    overflow-y: auto;
    padding: 0; 
    position: relative;
    scrollbar-gutter: stable;
  }
  
  .step-footer {
    /* AUMENTATO: Padding allineato */
    padding: 1.5rem 2.5rem;
    border-top: 1px solid var(--border-color);
    background: rgba(15, 23, 42, 0.5);
  }
  
  .btn-restart {
    background: transparent;
    width: 100%;
    border: 1px dashed rgba(255,255,255,0.2);
    color: var(--text-muted);
    padding: 1rem;
    border-radius: 12px;
    font-size: 0.95rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-restart:hover {
    border-color: var(--text-muted);
    color: var(--text-main);
    background: rgba(255,255,255,0.05);
  }
  
  /* Loading Overlay */
  .loading-overlay {
    position: absolute;
    inset: 0;
    background: rgba(15, 23, 42, 0.9); /* Più scuro */
    backdrop-filter: blur(12px); /* Più sfocato */
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 50;
  }
  
  .loading-content {
    text-align: center;
    color: white;
    max-width: 400px;
    padding: 3rem;
  }
  
  /* ... resto delle animazioni loading identico a prima ... */
  .loading-spinner {
    width: 50px;
    height: 50px;
    border: 3px solid rgba(59, 130, 246, 0.3);
    border-top-color: #3b82f6;
    border-radius: 50%;
    margin: 0 auto 1.5rem;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin { to { transform: rotate(360deg); } }
  
  .loading-content h3 { font-size: 1.25rem; margin-bottom: 0.5rem; color: white; }
  .loading-content p { color: var(--text-muted); font-size: 0.95rem; margin-bottom: 1.5rem; }
  
  .loading-steps { display: flex; flex-direction: column; gap: 0.5rem; }
  .loading-step {
    font-size: 0.85rem;
    color: var(--text-muted);
    padding: 0.5rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    border-left: 2px solid #3b82f6;
    animation: pulse 2s infinite;
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 0.6; }
    50% { opacity: 1; }
  }
</style>