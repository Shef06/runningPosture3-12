<script>
  import { analysisStore } from '../../stores/analysisStore.js';
  
  $: mainFlow = $analysisStore.mainFlow;
  $: videoFile = $analysisStore.videoFile;
  $: baselineVideos = $analysisStore.baselineVideos;
  $: speed = $analysisStore.speed;
  $: fps = $analysisStore.fps;
  $: height = $analysisStore.height;
  $: mass = $analysisStore.mass;
  $: loading = $analysisStore.loading;
  
  async function startAnalysis() {
    // Verifica che ci siano video da analizzare
    if (mainFlow === 'baseline' && baselineVideos.length !== 5) {
      analysisStore.setError('Sono richiesti esattamente 5 video per la baseline');
      return;
    }
    if (mainFlow === 'analyze' && !videoFile) {
      analysisStore.setError('Seleziona un video da analizzare');
      return;
    }

    // Avvia l'analisi con MediaPipe nel VideoHolder
    analysisStore.setAnalyzing(true);
    analysisStore.clearMessages();
    
    // Vai al prossimo step per mostrare i risultati dopo
    // (Per ora l'analisi è solo visiva, i risultati verranno poi inviati al backend)
    return;
    
    /* 
    // TODO: Dopo l'analisi visiva, inviare i dati al backend
    analysisStore.setLoading(true);
    analysisStore.clearMessages();
    
    try {
      const formData = new FormData();
      
      if (mainFlow === 'baseline') {
        // Carica tutti e 5 i video della baseline
        baselineVideos.forEach(video => {
          formData.append('videos', video);
        });
        formData.append('speed', speed);
        formData.append('fps', fps);
        formData.append('height', height);
        formData.append('mass', mass);
        
        const response = await fetch('http://localhost:5000/api/create_baseline', {
          method: 'POST',
          body: formData
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
          analysisStore.setResults(data);
          analysisStore.setMessage('✅ Baseline creata con successo!');
        } else {
          analysisStore.setError(data.message || 'Errore nella creazione baseline');
        }
      } else {
        // Analisi video
        formData.append('video', videoFile);
        formData.append('speed', speed);
        formData.append('fps', fps);
        formData.append('height', height);
        formData.append('mass', mass);
        
        const response = await fetch('http://localhost:5000/api/detect_anomaly', {
          method: 'POST',
          body: formData
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
          analysisStore.setResults(data);
        } else {
          analysisStore.setError(data.message || 'Errore nell\'analisi');
        }
      }
    } catch (error) {
      analysisStore.setError('Errore di connessione al server: ' + error.message);
    } finally {
      analysisStore.setLoading(false);
    }
    */
  }
</script>

<div class="step-container">
  <h3>
    {#if mainFlow === 'baseline'}
      Creazione Baseline
    {:else}
      Analisi Video
    {/if}
  </h3>
  <p class="step-description">
    {#if mainFlow === 'baseline'}
      Il sistema analizzerà il video per creare il modello di riferimento della tua corsa ottimale.
    {:else}
      Il video verrà confrontato con la baseline per rilevare eventuali anomalie biomeccaniche.
    {/if}
  </p>
  
  <div class="info-summary">
    <h4>Riepilogo Parametri:</h4>
    <div class="param-list">
      {#if mainFlow === 'baseline'}
        <div class="param-item">
          <span class="label">Video Baseline:</span>
          <span class="value">{baselineVideos.length} video</span>
        </div>
        {#each baselineVideos as video, index}
          <div class="param-item sub-item">
            <span class="label">{index + 1}.</span>
            <span class="value">{video.name}</span>
          </div>
        {/each}
      {:else}
        <div class="param-item">
          <span class="label">Video:</span>
          <span class="value">{videoFile?.name || 'N/A'}</span>
        </div>
      {/if}
      <div class="param-item">
        <span class="label">FPS:</span>
        <span class="value">{fps} fps</span>
      </div>
      <div class="param-item">
        <span class="label">Altezza:</span>
        <span class="value">{height} cm</span>
      </div>
      <div class="param-item">
        <span class="label">Massa:</span>
        <span class="value">{mass} kg</span>
      </div>
    </div>
  </div>
  
  {#if loading}
    <div class="loading-state">
      <div class="loading-spinner"></div>
      <p>Elaborazione in corso...</p>
      <p class="loading-hint">Questo potrebbe richiedere alcuni minuti</p>
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

<style>
  @import './steps-common.css';
  
  .btn-primary {
    background: var(--success-color);
  }
  
  .btn-primary:hover:not(:disabled) {
    background: #27ae60;
  }
  
  .param-item.sub-item {
    padding-left: 1.5rem;
    font-size: 0.8rem;
    background: rgba(0, 0, 0, 0.1);
  }
  
  .param-item.sub-item .label {
    min-width: 20px;
  }
  
  .param-item.sub-item .value {
    font-size: 0.8rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  /* Rimuovi outline blu */
  .info-summary,
  .param-list,
  .param-item {
    outline: none;
    border: none;
  }
  
  .info-summary {
    background: rgba(52, 152, 219, 0.1);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
  }
</style>

