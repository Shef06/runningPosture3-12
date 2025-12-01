<script>
  import { analysisStore } from '../stores/analysisStore.js';
  import { onDestroy } from 'svelte';

  // Usa i video dallo store invece di input file
  $: baselineVideos = $analysisStore.baselineVideos;
  $: speed = $analysisStore.speed;
  $: fps = $analysisStore.fps;
  $: viewType = $analysisStore.viewType;
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
    
    // Converti a numero per sicurezza
    const speedNum = typeof speed === 'string' ? parseFloat(speed) : speed;
    const fpsNum = typeof fps === 'string' ? parseFloat(fps) : fps;
    
    // Valida parametri obbligatori
    if (!speedNum || isNaN(speedNum) || speedNum <= 0 || speedNum > 50) {
      message = 'Velocità deve essere tra 0.1 e 50 km/h';
      messageType = 'error';
      analysisStore.setError(message);
      return;
    }
    
    if (!fpsNum || isNaN(fpsNum) || fpsNum <= 0 || fpsNum > 240) {
      message = 'FPS deve essere tra 15 e 240';
      messageType = 'error';
      analysisStore.setError(message);
      return;
    }
    
    if (!viewType) {
      message = 'Tipo di vista non selezionato';
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
      formData.append('view_type', viewType || 'posterior');
      formData.append('speed', speed.toString());
      formData.append('fps', fps.toString());
      if (height) formData.append('height', height.toString());
      if (mass) formData.append('mass', mass.toString());
      
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
          viewType: data.viewType || 'posterior',
          skeleton_video_url: data.skeleton_video_url || null, // Includi URL video con scheletro
          baselineRanges: data.baselineRanges || (data.details?.feature_ranges ? {
            features: {
              cpd: data.details.feature_ranges.cpd,
              bos: data.details.feature_ranges.bos,
              eversion: data.details.feature_ranges.rearfoot_eversion,
              trunkLean: data.details.feature_ranges.lateral_trunk_lean,
              gct: data.details.feature_ranges.gct,
              cadence: data.details.feature_ranges.cadence
            }
          } : null),
          feature_metrics: data.details?.feature_metrics,
          biomechanics: data.details?.biomechanics,
          details: data.details,
          timestamp: new Date().toISOString()
        };
        analysisStore.setResults(results);
        console.log('📹 Risultati baseline salvati, skeleton_video_url:', results.skeleton_video_url);
        
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

<div class="uploader-container">
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
          <span>Analisi: Video {Math.min(currentVideoProgress + 1, baselineVideos.length)} di {baselineVideos.length}</span>
        </div>
        
        <div class="progress-track">
          <div class="progress-line" style="width: {progressPercent}%"></div>
        </div>
        
        <div class="progress-text">
          {Math.round(progressPercent)}% completato
        </div>
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
  .uploader-container {
    /* Full size per riempire il VideoHolder */
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.95) 100%);
    padding: 2rem;
    position: absolute;
    top: 0;
    left: 0;
    z-index: 10;
  }
  
  .processing-display {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    max-width: 600px;
    width: 100%;
  }
  
  .processing-icon {
    font-size: 4rem;
    margin-bottom: 1.5rem;
    animation: rotate 4s linear infinite;
  }
  
  @keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  
  .processing-display h3 {
    margin: 0 0 1rem 0;
    color: var(--text-light);
    font-size: 1.75rem;
    font-weight: 700;
  }
  
  .processing-description {
    color: var(--text-muted);
    font-size: 1.1rem;
    line-height: 1.6;
    margin: 0 0 3rem 0;
  }
  
  .progress-section {
    width: 100%;
    max-width: 500px;
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
  }
  
  .progress-info {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.8rem;
    color: var(--success-color);
    font-weight: 600;
    font-size: 1rem;
  }
  
  .pulse-dot {
    width: 10px;
    height: 10px;
    background: var(--success-color);
    border-radius: 50%;
    animation: pulse 1.5s ease-in-out infinite;
    box-shadow: 0 0 10px var(--success-color);
  }
  
  @keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.5); opacity: 0.6; }
  }
  
  /* Nuova barra di progresso stile "linea" */
  .progress-track {
    width: 100%;
    height: 4px; /* Linea sottile */
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
    overflow: hidden;
    position: relative;
  }
  
  .progress-line {
    height: 100%;
    background: var(--success-color);
    border-radius: 2px;
    box-shadow: 0 0 15px var(--success-color); /* Effetto glow */
    transition: width 0.3s ease-out;
    /* Aggiungiamo un gradiente per renderla più dinamica */
    background: linear-gradient(90deg, #C5E8B7, #2EB62C);
  }
  
  .progress-text {
    text-align: right;
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.9rem;
    font-variant-numeric: tabular-nums;
  }
  
  .alert {
    margin-top: 2rem;
    padding: 1rem;
    border-radius: 8px;
    font-size: 0.95rem;
    max-width: 500px;
    width: 100%;
    text-align: center;
  }
  
  .alert.success {
    background: rgba(52, 211, 153, 0.1);
    border: 1px solid var(--success-color);
    color: var(--success-color);
  }
  
  .alert.error {
    background: rgba(248, 113, 113, 0.1);
    border: 1px solid var(--error-color);
    color: var(--error-color);
  }
</style>