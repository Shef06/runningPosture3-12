<script>
  import { analysisStore } from '../../stores/analysisStore.js';
  
  $: mainFlow = $analysisStore.mainFlow;
  $: videoFile = $analysisStore.videoFile;
  $: baselineVideos = $analysisStore.baselineVideos;
  $: speed = $analysisStore.speed;
  $: fps = $analysisStore.fps;
  $: loading = $analysisStore.loading;

  async function startAnalysis() {
    if (mainFlow === 'baseline' && baselineVideos.length !== 5) {
      analysisStore.setError('Sono richiesti esattamente 5 video per la baseline');
      return;
    }
    if (mainFlow === 'analyze' && !videoFile) {
      analysisStore.setError('Seleziona un video da analizzare');
      return;
    }

    analysisStore.setAnalyzing(true);
    analysisStore.clearMessages();
  }
</script>

<div class="step-container">
  <div class="header-section">
    <h3>
      {#if mainFlow === 'baseline'}
        Riepilogo Baseline
      {:else}
        Riepilogo Analisi
      {/if}
    </h3>
    <p class="step-description">
      {#if mainFlow === 'baseline'}
        Conferma i dati prima di generare il modello.
      {:else}
        Conferma i parametri del video da analizzare.
      {/if}
    </p>
  </div>
  
  <div class="summary-card">
    <div class="split-layout">
      
      <div class="left-col">
        <h4 class="section-title">
          {#if mainFlow === 'baseline'}
            <span class="icon">📚</span> Dataset ({baselineVideos.length})
          {:else}
            <span class="icon">📹</span> Video Input
          {/if}
        </h4>
        
        {#if mainFlow === 'baseline'}
          <div class="video-playlist">
            <div class="playlist-scroll-area">
              {#each baselineVideos as video, index}
                <div class="playlist-item">
                  <span class="item-index">{index + 1}</span>
                  <div class="item-info">
                    <span class="item-name">{video.name}</span>
                    <span class="item-size">{(video.size / 1024 / 1024).toFixed(1)}MB</span>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {:else}
          <div class="single-video-item">
            <div class="file-icon">🎬</div>
            <div class="file-details">
              <span class="file-name">{videoFile?.name || 'N/A'}</span>
              <span class="file-meta">{(videoFile?.size / 1024 / 1024).toFixed(2)} MB</span>
            </div>
          </div>
        {/if}
      </div>

      <div class="right-col">
        <h4 class="section-title"><span class="icon">⚙️</span> Parametri</h4>
        <div class="params-stack">
          <div class="param-box">
            <span class="param-label">FPS</span>
            <span class="param-value">{fps}</span>
          </div>
          {#if speed}
            <div class="param-box">
              <span class="param-label">Velocità</span>
              <span class="param-value">{speed} <small>km/h</small></span>
            </div>
          {/if}
        </div>
      </div>
      
    </div>
  </div>
  
  <div class="action-area">
    {#if loading}
      <div class="loading-state">
        <div class="loading-spinner"></div>
        <p>Elaborazione...</p>
      </div>
    {:else}
      <button class="btn-primary" on:click={startAnalysis}>
        {#if mainFlow === 'baseline'}
          🚀 Crea Baseline
        {:else}
          🔍 Avvia Analisi
        {/if}
      </button>
    {/if}
  </div>
</div>

<style>
  @import './steps-common.css';
  
  .step-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    justify-content: flex-start;
  }

  .header-section {
    margin-bottom: 0.5rem;
    flex-shrink: 0;
  }

  .step-description { margin-bottom: 0; }

  .summary-card {
    background: rgba(30, 41, 59, 0.4);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    flex-shrink: 0;
    overflow: hidden;
  }

  /* Layout a due colonne con altezza esplicita per allineamento perfetto */
  .split-layout {
    display: grid;
    grid-template-columns: 1.5fr 1fr;
    gap: 1rem;
    height: 180px; /* ALTEZZA FISSA PER IL CONTENUTO */
  }

  /* Colonne interne */
  .left-col, .right-col {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0; /* Cruciale per lo scroll interno */
  }

  .section-title {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-weight: 700;
    flex-shrink: 0;
  }
  
  /* --- Colonna Sinistra: Video --- */
  .video-playlist {
    background: rgba(15, 23, 42, 0.5);
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    flex: 1; /* Occupa tutto lo spazio rimanente */
    display: flex;
    flex-direction: column;
    overflow: hidden; /* Nasconde scrollbar del container esterno */
  }

  .playlist-scroll-area {
    overflow-y: auto;
    height: 100%;
    /* Scrollbar sottile */
    scrollbar-width: thin;
    scrollbar-color: rgba(255,255,255,0.1) transparent;
  }

  .playlist-scroll-area::-webkit-scrollbar { width: 4px; }
  .playlist-scroll-area::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }

  .playlist-item {
    display: flex;
    align-items: center;
    padding: 0.6rem 0.8rem; /* Padding leggermente aumentato */
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    transition: background 0.2s;
  }
  
  .playlist-item:last-child { border-bottom: none; }
  .playlist-item:hover { background: rgba(255, 255, 255, 0.05); }

  .item-index {
    background: rgba(255,255,255,0.1);
    color: var(--text-muted);
    font-size: 0.65rem;
    font-weight: 700;
    width: 20px;
    height: 20px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 0.6rem;
    flex-shrink: 0;
  }

  .item-info {
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .item-name {
    font-size: 0.85rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: var(--text-main);
    font-weight: 500;
  }

  .item-size { color: var(--text-muted); font-size: 0.7rem; }

  /* Video Singolo */
  .single-video-item {
    background: rgba(59, 130, 246, 0.1);
    border: 1px solid var(--accent-primary);
    border-radius: 10px;
    padding: 1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    flex: 1;
  }
  .file-icon { font-size: 2rem; }
  .file-details { display: flex; flex-direction: column; overflow: hidden; }
  .file-name { font-weight: 600; color: var(--text-main); font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .file-meta { font-size: 0.75rem; color: var(--accent-primary); }

  /* --- Colonna Destra: Parametri --- */
  .params-stack {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    flex: 1; /* Riempie l'altezza */
  }

  .param-box {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 0.5rem;
    border-radius: 10px;
    display: flex;
    flex-direction: column; 
    align-items: center;
    justify-content: center;
    flex: 1; /* Si dividono lo spazio verticale equamente */
  }

  .param-label {
    font-size: 0.7rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.2rem;
  }

  .param-value {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--success-color);
    line-height: 1;
  }

  .param-value small {
    font-size: 0.75rem;
    font-weight: 400;
    color: var(--text-muted);
    margin-left: 2px;
  }
  
  .action-area { margin-top: auto; }

  .btn-primary {
    background: var(--success-color);
    padding: 1.1rem;
    font-size: 1.1rem;
  }
  
  .btn-primary:hover:not(:disabled) { background: #27ae60; }
  
  .loading-state {
    text-align: center;
    padding: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.8rem;
  }
  
  .loading-spinner {
    width: 24px;
    height: 24px;
    border-width: 3px;
    margin: 0;
  }
  
  @media (max-width: 650px) {
    .split-layout {
      grid-template-columns: 1fr;
      gap: 1rem;
      height: auto; /* Su mobile lascia crescere */
    }
    .video-playlist { height: 160px; }
    .params-stack { height: auto; flex-direction: row; }
    .param-box { padding: 1rem; }
  }
</style>