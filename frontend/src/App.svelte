<script>
  import VideoHolder from './lib/components/VideoHolder.svelte';
  import StepHolder from './lib/components/StepHolder.svelte';
  import { analysisStore } from './lib/stores/analysisStore.js';
  import { onMount } from 'svelte';
  
  let videoHolder;
  
  $: error = $analysisStore.error;
  
  onMount(() => {
    // Event listeners per comunicazione con VideoHolder
    window.addEventListener('changecamera', (e) => {
      if (videoHolder?.changeCamera) {
        videoHolder.changeCamera(e.detail);
      }
    });
    
    window.addEventListener('startrecording', () => {
      if (videoHolder?.startRecording) {
        videoHolder.startRecording();
      }
    });
    
    window.addEventListener('stoprecording', () => {
      if (videoHolder?.stopRecording) {
        videoHolder.stopRecording();
      }
    });
  });
  
  function clearMessage() {
    analysisStore.clearMessages();
  }
</script>

<svelte:head>
  <title>Running Posture Analyzer</title>
</svelte:head>

<div class="app-container">
  <header class="app-header">
    <h1>Running Posture Analyzer</h1>
    <p class="subtitle">Analisi Biomeccanica Avanzata della Corsa con AI</p>
  </header>
  
  <main class="main-content">
    <!-- Messaggi globali -->
    {#if error}
      <div class="alert alert-error">
        <span>{error}</span>
        <button class="close-btn" on:click={clearMessage}>×</button>
      </div>
    {/if}
    
    <!-- Layout principale: Video a sinistra, Step a destra -->
    <div class="analysis-grid">
      <div class="video-section">
        <VideoHolder bind:this={videoHolder} />
      </div>
      
      <div class="step-section">
        <StepHolder />
      </div>
    </div>
  </main>
  
  <footer class="app-footer">
    <p>Powered by MediaPipe + TensorFlow LSTM Autoencoder</p>
  </footer>
</div>

<style>
  .app-container {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }
  
  .app-header {
    background: var(--primary-bg);
    padding: 1.25rem 2rem;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  }
  
  .app-header h1 {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.3rem;
  }
  
  .subtitle {
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.95rem;
  }
  
  .main-content {
    flex: 1;
    max-width: 1600px;
    width: 100%;
    margin: 0 auto;
    padding: 1rem;
  }
  
  .alert {
    padding: 0.75rem 2.5rem 0.75rem 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    position: relative;
    animation: slideIn 0.3s ease;
    font-size: 0.9rem;
  }
  
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .alert-error {
    background: var(--error-color);
    color: white;
  }
  
  .close-btn {
    position: absolute;
    right: 1rem;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: white;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: background 0.2s;
  }
  
  .close-btn:hover {
    background: rgba(0, 0, 0, 0.2);
  }
  
  .analysis-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 1rem;
    height: calc(100vh - 170px);
    min-height: 500px;
  }
  
  .video-section {
    height: 100%;
    width: 100%;
    overflow: hidden;
  }
  
  .step-section {
    height: 100%;
    width: 100%;
    overflow-y: auto;
  }
  
  @media (max-width: 1200px) {
    .analysis-grid {
      grid-template-columns: 1fr;
      height: auto;
    }
    
    .video-section {
      height: 500px;
    }
    
    .step-section {
      height: auto;
      max-height: 700px;
    }
  }
  
  .app-footer {
    background: var(--primary-bg);
    padding: 0.75rem;
    text-align: center;
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.85rem;
  }
</style>


