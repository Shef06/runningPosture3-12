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
          <h1>Running Analyzer</h1>
          <p class="subtitle">AI Biomechanical Analysis</p>
        </div>
      </div>
      <div class="header-badges">
        <span class="badge">AI</span>
        <span class="badge">Real-time</span>
        <span class="badge">3D</span>
      </div>
    </div>
  </header>
  
  <main class="main-content">
    {#if error}
      <div class="alert alert-error">
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
    <p>MediaPipe + TensorFlow LSTM</p>
  </footer>
</div>

<style>
  .app-container {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }
  
  .app-header {
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 0.75rem 1.5rem;
    border-bottom: 1px solid rgba(148, 163, 184, 0.18);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
    position: sticky;
    top: 0;
    z-index: 100;
  }
  
  .header-content {
    max-width: 1600px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    /* FIX SOVRAPPOSIZIONE */
    gap: 1.5rem; 
  }
  
  .logo-section {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    min-width: 0; /* Permette al testo di restringersi se necessario */
  }
  
  .logo-icon {
    font-size: 2rem;
    width: 42px;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(96, 165, 250, 0.2) 0%, rgba(129, 140, 248, 0.2) 100%);
    backdrop-filter: blur(10px);
    border-radius: 10px;
    border: 1px solid rgba(148, 163, 184, 0.18);
    flex-shrink: 0;
  }
  
  .logo-text h1 {
    font-size: 1.25rem;
    font-weight: 700;
    background: linear-gradient(135deg, #f1f5f9 0%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    letter-spacing: -0.03em;
    white-space: nowrap; /* Mantiene il titolo su una riga */
  }
  
  .subtitle {
    color: rgba(148, 163, 184, 0.9);
    font-size: 0.7rem;
    margin: 0;
    font-weight: 500;
    white-space: nowrap;
  }
  
  .header-badges {
    display: flex;
    gap: 0.5rem;
    /* FIX SOVRAPPOSIZIONE: impedisce ai badge di schiacciarsi */
    flex-shrink: 0; 
  }
  
  .badge {
    padding: 0.25rem 0.6rem;
    background: rgba(96, 165, 250, 0.15);
    border: 1px solid rgba(96, 165, 250, 0.3);
    border-radius: 12px;
    font-size: 0.65rem;
    color: #93c5fd;
    font-weight: 600;
    letter-spacing: 0.03em;
    text-transform: uppercase;
  }
  
  .main-content {
    flex: 1;
    max-width: 1600px;
    width: 100%;
    margin: 0 auto;
    padding: 0.75rem;
    position: relative;
  }
  
  .alert {
    padding: 0.6rem 2.5rem 0.6rem 1rem;
    border-radius: 10px;
    margin-bottom: 0.75rem;
    position: relative;
    animation: slideIn 0.4s ease;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    backdrop-filter: blur(12px);
    border: 1px solid;
  }
  
  @keyframes slideIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  .alert-error {
    background: rgba(248, 113, 113, 0.15);
    border-color: rgba(248, 113, 113, 0.4);
    color: #fca5a5;
  }
  
  .alert-text {
    flex: 1;
  }
  
  .close-btn {
    position: absolute;
    right: 0.5rem;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(248, 113, 113, 0.2);
    border: 1px solid rgba(248, 113, 113, 0.3);
    color: #fca5a5;
    font-size: 1.2rem;
    cursor: pointer;
    padding: 0;
    width: 26px;
    height: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    transition: all 0.2s;
  }
  
  .close-btn:hover {
    background: rgba(248, 113, 113, 0.3);
    transform: translateY(-50%) rotate(90deg);
  }
  
  .analysis-grid {
    display: grid;
    grid-template-columns: 1.8fr 1fr;
    gap: 0.75rem;
    height: calc(100vh - 140px);
    min-height: 500px;
  }
  
  .video-section,
  .step-section {
    height: 100%;
    width: 100%;
    overflow: hidden;
  }
  
  .step-section {
    overflow-y: auto;
  }
  
  .app-footer {
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 0.5rem 1.5rem;
    border-top: 1px solid rgba(148, 163, 184, 0.18);
    text-align: center;
    font-size: 0.75rem;
    color: rgba(148, 163, 184, 0.8);
  }
  
  .app-footer p {
    margin: 0;
  }
  
  /* RESPONSIVE BREAKPOINTS */
  
  /* Laptop (992px - 1200px) */
  @media (max-width: 1200px) and (min-width: 992px) {
    .analysis-grid {
      grid-template-columns: 1.5fr 1fr;
      height: calc(100vh - 130px);
    }
    
    .logo-text h1 {
      font-size: 1.15rem;
    }
    
    .subtitle {
      font-size: 0.65rem;
    }
  }
  
  /* Tablet Horizontal (768px - 992px) */
  @media (max-width: 992px) {
    .analysis-grid {
      grid-template-columns: 1fr;
      height: auto;
      gap: 0.5rem;
    }
    
    .video-section {
      height: 60vh;
      min-height: 400px;
    }
    
    .step-section {
      height: auto;
      max-height: 50vh;
    }
    
    /* Nasconde i badge su tablet se lo spazio è poco, opzionale */
    .header-badges {
      display: none;
    }
    
    .main-content {
      padding: 0.5rem;
    }
  }
  
  /* Tablet Vertical (576px - 768px) */
  @media (max-width: 768px) {
    .app-header {
      padding: 0.5rem 1rem;
    }
    
    .logo-icon {
      width: 36px;
      height: 36px;
      font-size: 1.75rem;
    }
    
    .logo-text h1 {
      font-size: 1rem;
    }
    
    .subtitle {
      font-size: 0.6rem;
    }
    
    .video-section {
      height: 50vh;
      min-height: 350px;
    }
    
    .step-section {
      max-height: 45vh;
    }
  }
  
  /* Mobile (< 576px) */
  @media (max-width: 576px) {
    .app-header {
      padding: 0.4rem 0.75rem;
    }
    
    .logo-section {
      gap: 0.5rem;
    }
    
    .logo-icon {
      width: 32px;
      height: 32px;
      font-size: 1.5rem;
      border-radius: 8px;
    }
    
    .logo-text h1 {
      font-size: 0.9rem;
    }
    
    .subtitle {
      font-size: 0.55rem;
    }
    
    .main-content {
      padding: 0.4rem;
    }
    
    .analysis-grid {
      gap: 0.4rem;
    }
    
    .video-section {
      height: 45vh;
      min-height: 280px;
    }
    
    .step-section {
      max-height: 50vh;
    }
    
    .app-footer {
      padding: 0.4rem;
      font-size: 0.7rem;
    }
    
    .alert {
      font-size: 0.75rem;
      padding: 0.5rem 2rem 0.5rem 0.75rem;
    }
    
    .close-btn {
      width: 24px;
      height: 24px;
      font-size: 1.1rem;
    }
  }
</style>