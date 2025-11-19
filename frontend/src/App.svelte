<script>
  import VideoHolder from './lib/components/VideoHolder.svelte';
  import StepHolder from './lib/components/StepHolder.svelte';
  import { analysisStore } from './lib/stores/analysisStore.js';
  import { onMount } from 'svelte';
  
  let videoHolder;
  
  $: error = $analysisStore.error;
  
  onMount(() => {
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
    <div class="header-content">
      <div class="logo-section">
        <div class="logo-icon">🏃</div>
        <div class="logo-text">
          <h1>Running Posture Analyzer</h1>
          <p class="subtitle">Analisi Biomeccanica Avanzata con AI</p>
        </div>
      </div>
      <div class="header-decoration"></div>
    </div>
  </header>
  
  <main class="main-content">
    {#if error}
      <div class="alert alert-error">
        <div class="alert-icon">⚠️</div>
        <span class="alert-text">{error}</span>
        <button class="close-btn" on:click={clearMessage}>×</button>
      </div>
    {/if}
    
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
    <div class="footer-content">
      <div class="footer-text">
        <p>Powered by MediaPipe + TensorFlow LSTM</p>
        <div class="footer-badges">
          <span class="badge">AI-Powered</span>
          <span class="badge">Real-time</span>
          <span class="badge">3D Analysis</span>
        </div>
      </div>
    </div>
  </footer>
</div>

<style>
  .app-container {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }
  
  .app-header {
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 1.5rem 2rem;
    border-bottom: 1px solid rgba(148, 163, 184, 0.18);
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
    position: relative;
    z-index: 10;
  }
  
  .header-content {
    max-width: 1600px;
    margin: 0 auto;
    position: relative;
  }
  
  .logo-section {
    display: flex;
    align-items: center;
    gap: 1.25rem;
  }
  
  .logo-icon {
    font-size: 3rem;
    width: 70px;
    height: 70px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(96, 165, 250, 0.2) 0%, rgba(129, 140, 248, 0.2) 100%);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    border: 1px solid rgba(148, 163, 184, 0.18);
    box-shadow: 0 8px 32px rgba(96, 165, 250, 0.2);
  }
  
  .logo-text h1 {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #f1f5f9 0%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.25rem;
    letter-spacing: -0.03em;
  }
  
  .subtitle {
    color: rgba(148, 163, 184, 0.9);
    font-size: 0.9rem;
    margin: 0;
    font-weight: 500;
    letter-spacing: 0.02em;
  }
  
  .header-decoration {
    position: absolute;
    bottom: -1px;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #60a5fa, #818cf8, transparent);
    opacity: 0.6;
  }
  
  .main-content {
    flex: 1;
    max-width: 1600px;
    width: 100%;
    margin: 0 auto;
    padding: 1.5rem;
    position: relative;
  }
  
  .alert {
    padding: 1rem 3rem 1rem 1.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    position: relative;
    animation: slideIn 0.4s ease;
    font-size: 0.95rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    backdrop-filter: blur(12px);
    border: 1px solid;
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
    background: rgba(248, 113, 113, 0.15);
    border-color: rgba(248, 113, 113, 0.4);
    color: #fca5a5;
  }
  
  .alert-icon {
    font-size: 1.5rem;
    flex-shrink: 0;
  }
  
  .alert-text {
    flex: 1;
  }
  
  .close-btn {
    position: absolute;
    right: 1rem;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(248, 113, 113, 0.2);
    border: 1px solid rgba(248, 113, 113, 0.3);
    color: #fca5a5;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    transition: all 0.2s;
  }
  
  .close-btn:hover {
    background: rgba(248, 113, 113, 0.3);
    transform: translateY(-50%) rotate(90deg);
  }
  
  .analysis-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 1.5rem;
    height: calc(100vh - 200px);
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
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 1.5rem 2rem;
    border-top: 1px solid rgba(148, 163, 184, 0.18);
    box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.3);
    position: relative;
    z-index: 10;
  }
  
  .footer-content {
    max-width: 1600px;
    margin: 0 auto;
  }
  
  .footer-text {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 1rem;
  }
  
  .footer-text p {
    color: rgba(148, 163, 184, 0.8);
    font-size: 0.9rem;
    margin: 0;
  }
  
  .footer-badges {
    display: flex;
    gap: 0.75rem;
  }
  
  .badge {
    padding: 0.35rem 0.85rem;
    background: rgba(96, 165, 250, 0.15);
    border: 1px solid rgba(96, 165, 250, 0.3);
    border-radius: 20px;
    font-size: 0.75rem;
    color: #93c5fd;
    font-weight: 600;
    letter-spacing: 0.03em;
    text-transform: uppercase;
  }
  
  @media (max-width: 768px) {
    .logo-icon {
      width: 55px;
      height: 55px;
      font-size: 2.5rem;
    }
    
    .logo-text h1 {
      font-size: 1.5rem;
    }
    
    .subtitle {
      font-size: 0.8rem;
    }
    
    .footer-text {
      justify-content: center;
      text-align: center;
    }
  }
</style>