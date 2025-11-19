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
  
  // Calcola lo step visivo e il totale
  $: stepInfo = calculateStepInfo(currentStep, mainFlow, videoMethod);
  
  // Determina se mostrare il loading overlay per baseline o analisi
  $: showBaselineLoading = loading && mainFlow === 'baseline';
  $: showAnalysisLoading = loading && mainFlow === 'analyze';
  
  function calculateStepInfo(step, flow, method) {
    // Step mapping per flussi diversi
    if (!flow || !method) {
      return { current: step, total: 6 };
    }
    
    // Upload (salta step 5): 1 → 2 → 3 → 4 → 6
    // Mapping: 1→1, 2→2, 3→3, 4→4, 6→5
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
    
    // Record (tutti gli step): 1 → 2 → 3 → 4 → 5 → 6
    if (method === 'record') {
      return { current: step, total: 6 };
    }
    
    return { current: step, total: 6 };
  }
  
  function goBack() {
    analysisStore.prevStep();
  }
  
  // Calcola quale componente mostrare
  function getStepComponent() {
    if (currentStep === 1) {
      return Step1MainChoice;
    }
    
    if (currentStep === 2) {
      return Step2VideoMethod;
    }
    
    if (currentStep === 3) {
      if (videoMethod === 'record') {
        return Step3CameraSetup;
      } else {
        // Upload: usa componente diverso per baseline (5 video) vs analisi (1 video)
        if (mainFlow === 'baseline') {
          return Step3BaselineUpload;
        } else {
          return Step3Calibration;
        }
      }
    }
    
    if (currentStep === 4) {
      if (videoMethod === 'record') {
        return Step4Calibration;
      } else {
        return Step4Analysis;
      }
    }
    
    if (currentStep === 5) {
      return Step5Analysis;
    }
    
    if (currentStep === 6) {
      return Step6Results;
    }
    
    return Step1MainChoice;
  }
  
  function restartFlow() {
    analysisStore.reset();
  }
</script>

<div class="step-holder">
  <div class="step-header">
    <div class="header-left">
      <h2>Step</h2>
      <p class="step-subtitle">Step {stepInfo.current} di {stepInfo.total}</p>
    </div>
    <div class="header-right">
      {#if currentStep > 1}
        <button class="btn-back" on:click={goBack}>
          ← Indietro
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
            <h3>Creazione Baseline in Corso</h3>
            <p>Il backend sta elaborando i 5 video e calcolando la baseline biomeccanica...</p>
            <div class="loading-steps">
              <div class="loading-step">📹 Estrazione keypoint 3D</div>
              <div class="loading-step">🦶 Rilevamento eventi del passo</div>
              <div class="loading-step">📊 Calcolo features biomeccaniche</div>
              <div class="loading-step">🤖 Addestramento modello AI</div>
              <div class="loading-step">📈 Calcolo soglie dinamiche</div>
              <div class="loading-step">💾 Salvataggio risultati</div>
            </div>
          {:else}
            <h3>Analisi Video in Corso</h3>
            <p>Il backend sta analizzando il video e calcolando l'anomaly score...</p>
            <div class="loading-steps">
              <div class="loading-step">📹 Estrazione keypoint 3D</div>
              <div class="loading-step">🦶 Rilevamento eventi del passo</div>
              <div class="loading-step">📊 Calcolo features biomeccaniche</div>
              <div class="loading-step">🤖 Calcolo anomaly score</div>
              <div class="loading-step">📈 Classificazione livello anomalia</div>
              <div class="loading-step">💾 Salvataggio risultati</div>
            </div>
          {/if}
        </div>
      </div>
    {/if}
  </div>
  
  <div class="step-footer">
    {#if currentStep > 1}
      <button class="btn-restart" on:click={restartFlow}>
        🔄 Ricomincia
      </button>
    {/if}
  </div>
</div>

<style>
  .step-holder {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: var(--secondary-bg);
    border-radius: var(--border-radius);
    padding: 1rem;
    box-shadow: var(--box-shadow);
  }
  
  .step-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid rgba(255, 255, 255, 0.1);
  }
  
  .header-left {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .step-header h2 {
    font-size: 1.5rem;
    margin: 0;
    font-weight: 700;
  }
  
  .step-subtitle {
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.6);
    margin: 0;
    font-weight: 500;
  }
  
  .header-right {
    display: flex;
    align-items: center;
  }
  
  .btn-back {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .btn-back:hover {
    background: rgba(255, 255, 255, 0.2);
    border-color: rgba(255, 255, 255, 0.5);
    transform: translateX(-2px);
  }
  
  .step-content {
    flex: 1;
    overflow-y: auto;
    padding-right: 0.5rem;
    position: relative;
  }
  
  .step-content::-webkit-scrollbar {
    width: 6px;
  }
  
  .step-content::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 3px;
  }
  
  .step-content::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 3px;
  }
  
  .step-content::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.3);
  }
  
  .step-footer {
    margin-top: 1rem;
    padding-top: 0.75rem;
    border-top: 2px solid rgba(255, 255, 255, 0.1);
  }
  
  .btn-restart {
    background: var(--warning-color);
    width: 100%;
    border: none;
    color: white;
    padding: 0.75rem;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .btn-restart:hover {
    background: #e67e22;
    transform: translateY(-1px);
  }
  
  /* Loading overlay per baseline */
  .loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.85);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    border-radius: var(--border-radius);
    animation: fadeIn 0.3s ease;
  }
  
  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
  
  .loading-content {
    text-align: center;
    color: white;
    max-width: 500px;
    padding: 2rem;
  }
  
  .loading-spinner {
    width: 60px;
    height: 60px;
    border: 4px solid rgba(255, 255, 255, 0.2);
    border-top-color: var(--primary-color, #2ecc71);
    border-radius: 50%;
    margin: 0 auto 1.5rem;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
  
  .loading-content h3 {
    font-size: 1.5rem;
    margin: 0 0 0.5rem 0;
    font-weight: 700;
    color: var(--primary-color, #2ecc71);
  }
  
  .loading-content p {
    font-size: 1rem;
    margin: 0 0 2rem 0;
    color: rgba(255, 255, 255, 0.8);
    line-height: 1.6;
  }
  
  .loading-steps {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-top: 1.5rem;
  }
  
  .loading-step {
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.7);
    padding: 0.5rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    border-left: 3px solid var(--primary-color, #2ecc71);
    animation: pulse 2s ease-in-out infinite;
  }
  
  .loading-step:nth-child(1) { animation-delay: 0s; }
  .loading-step:nth-child(2) { animation-delay: 0.3s; }
  .loading-step:nth-child(3) { animation-delay: 0.6s; }
  .loading-step:nth-child(4) { animation-delay: 0.9s; }
  .loading-step:nth-child(5) { animation-delay: 1.2s; }
  .loading-step:nth-child(6) { animation-delay: 1.5s; }
  
  @keyframes pulse {
    0%, 100% {
      opacity: 0.7;
      transform: translateX(0);
    }
    50% {
      opacity: 1;
      transform: translateX(5px);
    }
  }
  
  .step-content {
    position: relative;
  }
</style>

