<script>
  import { analysisStore } from '../stores/analysisStore.js';
  import MainChoiceStep from './steps/MainChoiceStep.svelte';
  import ViewSelectionStep from './steps/ViewSelectionStep.svelte';
  import VideoMethodStep from './steps/VideoMethodStep.svelte';
  import CameraSetupStep from './steps/CameraSetupStep.svelte';
  import VideoCalibrationStep from './steps/VideoCalibrationStep.svelte';
  import BaselineUploadStep from './steps/BaselineUploadStep.svelte';
  import RecordCalibrationStep from './steps/RecordCalibrationStep.svelte';
  import AnalysisSummaryStep from './steps/AnalysisSummaryStep.svelte';
  import RecordAnalysisStep from './steps/RecordAnalysisStep.svelte';
  import ResultsStep from './steps/ResultsStep.svelte';
  
  $: currentStep = $analysisStore.currentStep;
  $: mainFlow = $analysisStore.mainFlow;
  $: viewType = $analysisStore.viewType;
  $: videoMethod = $analysisStore.videoMethod;
  $: loading = $analysisStore.loading;
  
  $: stepInfo = calculateStepInfo(currentStep, mainFlow, videoMethod);
  
  $: showBaselineLoading = loading && mainFlow === 'baseline';
  $: showAnalysisLoading = loading && mainFlow === 'analyze';
  
  function calculateStepInfo(step, flow, method) {
    if (!flow) {
      return { current: step, total: 8 };
    }
    
    if (!method) {
      return { current: step, total: 8 };
    }
    
    if (method === 'upload') {
      // Upload: Step 1-6 + risultati (step 7)
      // Step 1: MainChoice
      // Step 2: ViewSelection (NUOVO)
      // Step 3: VideoMethod
      // Step 4: Upload
      // Step 5: Analysis
      // Step 6: (skip, va direttamente a 7)
      // Step 7: Results
      const stepMap = {
        1: { current: 1, total: 7 },
        2: { current: 2, total: 7 },
        3: { current: 3, total: 7 },
        4: { current: 4, total: 7 },
        5: { current: 5, total: 7 },
        6: { current: 6, total: 7 },
        7: { current: 7, total: 7 } // Risultati
      };
      return stepMap[step] || { current: step, total: 7 };
    }
    
    if (method === 'record') {
      // Record: tutti gli 8 step
      // Step 1: MainChoice
      // Step 2: ViewSelection (NUOVO)
      // Step 3: VideoMethod
      // Step 4: CameraSetup
      // Step 5: Calibration
      // Step 6: Analysis (record)
      // Step 7: (skip)
      // Step 8: Results
      return { current: step, total: 8 };
    }
    
    return { current: step, total: 8 };
  }
  
  function goBack() {
    // Se siamo ai risultati (step 7) con upload, torna a step 6
    if (videoMethod === 'upload' && currentStep === 7) {
      analysisStore.goToStep(6);
      return;
    }
    // Se siamo ai risultati (step 8) con record, torna a step 7
    if (videoMethod === 'record' && currentStep === 8) {
      analysisStore.goToStep(7);
      return;
    }
    analysisStore.prevStep();
  }
  
  function getStepComponent() {
    if (currentStep === 1) return MainChoiceStep;
    if (currentStep === 2) return ViewSelectionStep;
    if (currentStep === 3) return VideoMethodStep;
    if (currentStep === 4) {
      if (videoMethod === 'record') return CameraSetupStep;
      else {
        if (mainFlow === 'baseline') return BaselineUploadStep;
        else return VideoCalibrationStep;
      }
    }
    if (currentStep === 5) {
      if (videoMethod === 'record') {
        return RecordCalibrationStep;
      } else {
        // Upload method
        return AnalysisSummaryStep;
      }
    }
    if (currentStep === 6) {
      // Solo per recording
      if (videoMethod === 'record') return RecordAnalysisStep;
      // Per upload, vai direttamente ai risultati (skip questo step)
      else return ResultsStep;
    }
    if (currentStep === 7) return ResultsStep; // Upload results
    if (currentStep === 8) return ResultsStep; // Record results
    return MainChoiceStep;
  }
  
  function restartFlow() {
    analysisStore.reset();
  }
</script>

<div class="step-holder">
  <div class="step-header">
    <div class="header-left">
      <h2>Configurazione</h2>
      <p class="step-subtitle">Step {stepInfo.current} / {stepInfo.total}</p>
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
    <div class="step-wrapper">
      <svelte:component this={getStepComponent()} />
    </div>
    
    {#if showBaselineLoading || showAnalysisLoading}
      <div class="loading-overlay">
        <div class="loading-content">
          <div class="loading-spinner"></div>
          {#if mainFlow === 'baseline'}
            <h3>Creazione Baseline</h3>
            <p>Elaborazione dei 5 video in corso...</p>
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
    overflow: hidden;
  }
  
  .step-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid var(--border-color);
    background: rgba(15, 23, 42, 0.4);
    flex-shrink: 0;
  }
  
  .header-left h2 {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    margin-bottom: 0.2rem;
  }
  
  .step-subtitle {
    font-size: 1.1rem;
    color: var(--text-main);
    font-weight: 600;
    margin: 0;
  }
  
  .btn-back {
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-muted);
    padding: 0.4rem 0.8rem;
    border-radius: 6px;
    font-size: 0.8rem;
    transition: all 0.2s;
    cursor: pointer;
  }
  
  .btn-back:hover {
    background: rgba(255,255,255,0.05);
    color: white;
    border-color: rgba(255,255,255,0.3);
  }
  
  /* MODIFICA: Step Content diventa un contenitore Flex */
  .step-content {
    flex: 1;
    overflow-y: auto;
    padding: 0; 
    position: relative;
    /* Flex per centrare verticalmente il wrapper interno */
    display: flex;
    flex-direction: column;
  }
  
  /* NUOVO: Wrapper interno per gestire larghezza e margini automatici */
  .step-wrapper {
    flex: 1;
    width: 100%;
    display: flex;
    flex-direction: column;
    /* Questo centra verticalmente il contenuto se c'è spazio extra */
    justify-content: center; 
    /* Padding inferiore extra per evitare taglio ombre */
    padding-bottom: 2rem;
  }
  
  .step-content::-webkit-scrollbar {
    width: 6px;
  }
  .step-content::-webkit-scrollbar-track {
    background: transparent;
  }
  .step-content::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
  }
  .step-content::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.2);
  }
  
  .step-footer {
    padding: 1rem 1.5rem;
    border-top: 1px solid var(--border-color);
    background: rgba(15, 23, 42, 0.4);
    flex-shrink: 0;
  }
  
  .btn-restart {
    background: transparent;
    width: 100%;
    border: 1px dashed var(--border-color);
    color: var(--text-muted);
    padding: 0.75rem;
    border-radius: 8px;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
  }
  
  .btn-restart:hover {
    border-color: var(--text-muted);
    color: var(--text-main);
    background: rgba(255,255,255,0.02);
  }
  
  /* Loading Overlay */
  .loading-overlay {
    position: absolute;
    inset: 0;
    background: rgba(15, 23, 42, 0.9);
    backdrop-filter: blur(12px);
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