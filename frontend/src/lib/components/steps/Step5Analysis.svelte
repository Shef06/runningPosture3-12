<script>
  import { analysisStore } from '../../stores/analysisStore.js';
  
  $: mainFlow = $analysisStore.mainFlow;
  $: recordedBlob = $analysisStore.recordedBlob;
  $: speed = $analysisStore.speed;
  $: fps = $analysisStore.fps;
  $: height = $analysisStore.height;
  $: mass = $analysisStore.mass;
  $: loading = $analysisStore.loading;
  $: isRecording = $analysisStore.isRecording;
  
  function startRecording() {
    window.dispatchEvent(new CustomEvent('startrecording'));
  }
  
  function stopRecording() {
    window.dispatchEvent(new CustomEvent('stoprecording'));
  }
  
  async function startAnalysis() {
    if (!recordedBlob) return;
    
    analysisStore.setLoading(true);
    analysisStore.clearMessages();
    
    try {
      // Converti Blob in File
      const file = new File([recordedBlob], 'recorded-video.webm', { type: 'video/webm' });
      const formData = new FormData();
      
      if (mainFlow === 'baseline') {
        // Per baseline
        formData.append('videos', file);
        formData.append('videos', file); // Temp: duplica per test
        formData.append('videos', file);
        formData.append('videos', file);
        formData.append('videos', file);
        formData.append('speed', speed);
        formData.append('fps', fps);
        
        const response = await fetch('http://localhost:5000/api/create_baseline', {
          method: 'POST',
          body: formData
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
          analysisStore.setResults(data);
          // Salva E_max e thresholds se disponibili
          if (data.details && data.details.thresholds) {
            analysisStore.setBaselineThresholds(data.details.thresholds);
            console.log('💾 E_max salvato:', data.details.thresholds.e_max);
          }
          // Salva feature ranges se disponibili (dal backend)
          if (data.details && data.details.feature_ranges) {
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
        } else {
          analysisStore.setError(data.message || 'Errore nella creazione baseline');
        }
      } else {
        // Analisi video
        formData.append('video', file);
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
          // Salva feature ranges se disponibili (dal backend, per analisi future)
          if (data.feature_ranges) {
            const frontendRanges = {
              features: {
                cpd: data.feature_ranges.cpd,
                bos: data.feature_ranges.bos,
                eversion: data.feature_ranges.rearfoot_eversion,
                trunkLean: data.feature_ranges.lateral_trunk_lean,
                gct: data.feature_ranges.gct,
                cadence: data.feature_ranges.cadence
              }
            };
            analysisStore.setBaselineRanges(frontendRanges);
            console.log('💾 Feature ranges aggiornati dal backend:', frontendRanges);
          }
        } else {
          analysisStore.setError(data.message || 'Errore nell\'analisi');
        }
      }
    } catch (error) {
      analysisStore.setError('Errore di connessione al server: ' + error.message);
    } finally {
      analysisStore.setLoading(false);
    }
  }
</script>

<div class="step-container">
  <h3>Registrazione e Analisi</h3>
  <p class="step-description">
    Registra il video dalla webcam e avvia l'analisi biomeccanica.
  </p>
  
  {#if !recordedBlob}
    <!-- Controlli registrazione -->
    <div class="recording-controls">
      <h4>Registrazione Video</h4>
      <p class="hint">La registrazione apparirà nel video holder</p>
      
      {#if !isRecording}
        <button class="btn-record" on:click={startRecording}>
          🔴 Avvia Registrazione
        </button>
      {:else}
        <button class="btn-stop" on:click={stopRecording}>
          ⏹ Ferma Registrazione
        </button>
      {/if}
    </div>
  {:else}
    <!-- Video registrato - mostra riepilogo -->
    <div class="info-summary">
      <h4>Video Registrato ✅</h4>
      <div class="param-list">
        <div class="param-item">
          <span class="label">Dimensione:</span>
          <span class="value">{(recordedBlob.size / 1024 / 1024).toFixed(2)} MB</span>
        </div>
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
  {/if}
</div>

<style>
  @import './steps-common.css';
  
  .step-container {
    padding: 0.5rem 0;
  }
  
  h3 {
    font-size: 1.2rem;
    margin-bottom: 0.5rem;
    color: var(--text-light);
  }
  
  h4 {
    font-size: 1rem;
    margin-bottom: 0.75rem;
    color: var(--text-light);
  }
  
  .step-description {
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 1rem;
    line-height: 1.4;
    font-size: 0.9rem;
  }
  
  .recording-controls {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    padding: 1.5rem;
    text-align: center;
    margin-bottom: 1rem;
  }
  
  .hint {
    color: rgba(255, 255, 255, 0.6);
    margin-bottom: 1.5rem;
    font-size: 0.85rem;
  }
  
  .btn-record {
    width: 100%;
    background: var(--error-color);
    color: white;
    border: none;
    padding: 1.2rem;
    font-size: 1.1rem;
    font-weight: 600;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .btn-record:hover {
    background: #c0392b;
    transform: scale(1.01);
  }
  
  .btn-stop {
    width: 100%;
    background: var(--warning-color);
    color: white;
    border: none;
    padding: 1.2rem;
    font-size: 1.1rem;
    font-weight: 600;
    border-radius: 8px;
    cursor: pointer;
    animation: pulse 1.5s infinite;
  }
  
  @keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.01); }
  }
  
  .info-summary {
    background: rgba(46, 204, 113, 0.1);
    border: 1px solid var(--success-color);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
  }
  
  .btn-primary {
    background: var(--success-color);
  }
  
  .btn-primary:hover:not(:disabled) {
    background: #27ae60;
  }
</style>

