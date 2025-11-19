<script>
  import { analysisStore } from '../stores/analysisStore.js';
  import { onDestroy } from 'svelte';
  
  // Usa i video dallo store invece di input file
  $: baselineVideos = $analysisStore.baselineVideos;
  $: speed = $analysisStore.speed;
  $: fps = $analysisStore.fps;
  $: height = $analysisStore.height;
  $: mass = $analysisStore.mass;
  
  let loading = false;
  let message = null;
  let messageType = null;
  let currentVideoProgress = 0; // Video corrente in elaborazione (0-5)
  let progressPercent = 0; // Percentuale progress (0-100)
  
  // Auto-start quando i video sono pronti e isAnalyzing è true
  $: isAnalyzing = $analysisStore.isAnalyzing;
  $: if (isAnalyzing && baselineVideos.length === 5 && !loading && speed && fps) {
    // Usa setTimeout per evitare problemi di reattività
    setTimeout(() => {
      if (!loading) {
        createBaseline();
      }
    }, 100);
  }
  
  // Simula progress durante l'elaborazione
  let progressInterval = null;
  
  function startProgressSimulation() {
    currentVideoProgress = 0;
    progressPercent = 0;
    
    // Simula progress: ogni video rappresenta 20% (100% / 5 video)
    progressInterval = setInterval(() => {
      if (currentVideoProgress < 5) {
        // Incrementa progress gradualmente per ogni video
        const videoProgress = (currentVideoProgress + 1) * 20; // 20%, 40%, 60%, 80%, 100%
        const increment = 0.5; // Incremento graduale
        
        if (progressPercent < videoProgress - 1) {
          progressPercent = Math.min(progressPercent + increment, videoProgress);
        } else {
          // Passa al prossimo video
          currentVideoProgress++;
          if (currentVideoProgress >= 5) {
            progressPercent = 100;
            clearInterval(progressInterval);
          }
        }
      } else {
        clearInterval(progressInterval);
      }
    }, 200); // Aggiorna ogni 200ms
  }
  
  function stopProgressSimulation() {
    if (progressInterval) {
      clearInterval(progressInterval);
      progressInterval = null;
    }
  }
  
  // Cleanup quando il componente viene distrutto
  onDestroy(() => {
    stopProgressSimulation();
  });
  
  async function createBaseline() {
    if (baselineVideos.length !== 5) {
      message = 'Sono richiesti esattamente 5 video per creare la baseline';
      messageType = 'error';
      return;
    }
    
    // Valida parametri obbligatori
    if (!speed || speed <= 0) {
      message = 'Velocità del tapis roulant (speed) è obbligatoria';
      messageType = 'error';
      analysisStore.setError(message);
      return;
    }
    
    if (!fps || fps <= 0) {
      message = 'FPS del video è obbligatorio';
      messageType = 'error';
      analysisStore.setError(message);
      return;
    }
    
    loading = true;
    message = null;
    currentVideoProgress = 0;
    progressPercent = 0;
    // Imposta loading nello store per mostrare overlay in StepHolder
    analysisStore.setLoading(true);
    analysisStore.clearMessages();
    
    // Avvia simulazione progress
    startProgressSimulation();
    
    try {
      const formData = new FormData();
      baselineVideos.forEach(file => {
        formData.append('videos', file);
      });
      
      // Aggiungi parametri di calibrazione
      formData.append('speed', speed);
      formData.append('fps', fps);
      if (height) formData.append('height', height);
      if (mass) formData.append('mass', mass);
      
      const response = await fetch('http://localhost:5000/api/create_baseline', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        // Salva i risultati completi nello store
        const results = {
          status: 'success',
          baselineCreated: true,
          videosProcessed: 5,
          totalFrames: data.details?.n_frames_total || 0,
          baselineRanges: data.details?.feature_ranges ? {
            features: {
              cpd: data.details.feature_ranges.cpd,
              bos: data.details.feature_ranges.bos,
              eversion: data.details.feature_ranges.rearfoot_eversion,
              trunkLean: data.details.feature_ranges.lateral_trunk_lean,
              gct: data.details.feature_ranges.gct,
              cadence: data.details.feature_ranges.cadence
            }
          } : null,
          feature_metrics: data.details?.feature_metrics,
          biomechanics: data.details?.biomechanics,
          details: data.details,
          timestamp: new Date().toISOString()
        };
        
        analysisStore.setResults(results);
        
        // Salva E_max e thresholds se disponibili
        if (data.details?.thresholds) {
          analysisStore.setBaselineThresholds(data.details.thresholds);
          console.log('💾 E_max salvato:', data.details.thresholds.e_max);
        }
        
        // Salva feature ranges se disponibili (dal backend)
        if (data.details?.feature_ranges) {
          const frontendRanges = {
            features: {
              cpd: data.details.feature_ranges.cpd,
              bos: data.details.feature_ranges.bos,
              eversion: data.details.feature_ranges.rearfoot_eversion,
              trunkLean: data.details.feature_ranges.lateral_trunk_lean,
              gct: data.details.feature_ranges.gct,
              cadence: data.details.feature_ranges.cadence
            }
          };
          analysisStore.setBaselineRanges(frontendRanges);
          console.log('💾 Feature ranges salvati dal backend:', frontendRanges);
        }
        
        analysisStore.setMessage('✅ Baseline creata con successo!');
        console.log('✅ Baseline creata con successo:', results);
      } else {
        const errorMsg = data.message || 'Errore nella creazione baseline';
        analysisStore.setError(errorMsg);
        message = `✗ Errore: ${errorMsg}`;
        messageType = 'error';
      }
    } catch (error) {
      const errorMsg = `Errore di connessione: ${error.message}`;
      analysisStore.setError(errorMsg);
      message = `✗ ${errorMsg}`;
      messageType = 'error';
    } finally {
      stopProgressSimulation();
      // Completa il progress
      currentVideoProgress = 5;
      progressPercent = 100;
      loading = false;
      analysisStore.setAnalyzing(false);
      // Rimuovi loading dallo store
      analysisStore.setLoading(false);
    }
  }
</script>

<div class="uploader-card">
  <div class="processing-display">
    <div class="processing-icon">⚙️</div>
    <h3>Creazione Baseline in Corso</h3>
    <p class="processing-description">
      I 5 video vengono inviati al backend per calcolare la baseline biomeccanica.
    </p>
    
    {#if loading}
      <div class="progress-section">
        <div class="progress-info">
          <span class="pulse-dot"></span>
          <span>Analisi Baseline: Video {currentVideoProgress + 1} di {baselineVideos.length}</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" style="width: {progressPercent}%"></div>
        </div>
        <div class="progress-text">
          {Math.round(progressPercent)}% completato
        </div>
      </div>
    {/if}
    
    {#if baselineVideos.length > 0}
      <div class="video-list">
        <p class="video-list-title">Video caricati:</p>
        {#each baselineVideos as file, i}
          <div class="file-item">
            <span class="file-number">{i + 1}</span>
            <span class="file-name">{file.name}</span>
            <span class="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
          </div>
        {/each}
      </div>
    {/if}
  </div>
  
  {#if message}
    <div class="alert {messageType}">
      {message}
    </div>
  {/if}
</div>

<style>
  .uploader-card {
    background: var(--secondary-bg);
    border-radius: var(--border-radius);
    padding: 2rem;
    box-shadow: var(--box-shadow);
  }
  
  h2 {
    color: var(--text-light);
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
  }
  
  .description {
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.95rem;
    line-height: 1.5;
    margin-bottom: 1.5rem;
  }
  
  .upload-area {
    position: relative;
    margin-bottom: 1.5rem;
  }
  
  input[type="file"] {
    display: none;
  }
  
  .upload-label {
    display: block;
    padding: 3rem 2rem;
    background: rgba(52, 152, 219, 0.1);
    border: 2px dashed var(--accent-color);
    border-radius: 8px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    font-size: 1.1rem;
  }
  
  .upload-label:hover {
    background: rgba(52, 152, 219, 0.2);
    border-color: #5dade2;
  }
  
  .file-list {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1.5rem;
  }
  
  .file-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    margin-bottom: 0.5rem;
  }
  
  .file-item:last-child {
    margin-bottom: 0;
  }
  
  .file-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    background: var(--accent-color);
    border-radius: 50%;
    font-weight: 600;
    font-size: 0.9rem;
  }
  
  .file-name {
    flex: 1;
    font-size: 0.95rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .file-size {
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.85rem;
  }
  
  .processing-display {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(46, 204, 113, 0.1) 0%, rgba(52, 152, 219, 0.1) 100%);
    border-radius: 12px;
    padding: 3rem;
    text-align: center;
    min-height: 0;
  }
  
  .processing-icon {
    font-size: 4rem;
    margin-bottom: 1.5rem;
    animation: rotate 2s linear infinite;
  }
  
  @keyframes rotate {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
  
  .processing-display h3 {
    margin: 0 0 1rem 0;
    color: var(--text-light);
    font-size: 1.5rem;
    font-weight: 700;
  }
  
  .processing-description {
    color: rgba(255, 255, 255, 0.7);
    font-size: 1rem;
    max-width: 500px;
    line-height: 1.6;
    margin: 0 0 2rem 0;
  }
  
  .progress-section {
    padding: 1rem;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 8px;
    margin-top: 1rem;
    width: 100%;
    max-width: 400px;
  }
  
  .progress-info {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    color: var(--success-color);
    font-weight: 600;
    font-size: 0.95rem;
  }
  
  .pulse-dot {
    width: 10px;
    height: 10px;
    background: var(--success-color);
    border-radius: 50%;
    animation: pulse 1.5s ease-in-out infinite;
  }
  
  @keyframes pulse {
    0%, 100% {
      transform: scale(1);
      opacity: 1;
    }
    50% {
      transform: scale(1.3);
      opacity: 0.7;
    }
  }
  
  .progress-bar {
    width: 100%;
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 0.5rem;
  }
  
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--success-color), var(--accent-color));
    border-radius: 4px;
  }
  
  .progress-fill {
    transition: width 0.3s ease;
  }
  
  .progress-text {
    text-align: center;
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.85rem;
    margin-top: 0.5rem;
  }
  
  .video-list {
    margin-top: 2rem;
    width: 100%;
    max-width: 500px;
  }
  
  .video-list-title {
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.6);
    margin-bottom: 0.75rem;
    font-weight: 600;
  }
  
  .alert {
    margin-top: 1rem;
    padding: 1rem;
    border-radius: 8px;
    font-size: 0.95rem;
  }
  
  .alert.success {
    background: rgba(46, 204, 113, 0.2);
    border: 1px solid var(--success-color);
    color: var(--success-color);
  }
  
  .alert.error {
    background: rgba(231, 76, 60, 0.2);
    border: 1px solid var(--error-color);
    color: var(--error-color);
  }
</style>

