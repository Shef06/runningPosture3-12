<script>
  import { analysisStore } from '../../stores/analysisStore.js';
  
  let fileInput;
  let speed = null; // km/h - obbligatorio
  let fps = null; // obbligatorio
  let height = 180;
  let mass = 70;
  let dragOver = false;
  
  $: baselineVideos = $analysisStore.baselineVideos;
  $: baselineVideoUrls = $analysisStore.baselineVideoUrls;
  $: videosCount = baselineVideos.length;
  $: canContinue = videosCount === 5;
  
  function handleFileSelect(event) {
    const files = Array.from(event.target.files);
    addVideos(files);
  }
  
  function addVideos(files) {
    files.forEach(file => {
      if (baselineVideos.length < 5 && file.type.startsWith('video/')) {
        analysisStore.addBaselineVideo(file);
      }
    });
  }
  
  function removeVideo(index) {
    analysisStore.removeBaselineVideo(index);
  }
  
  function handleDragOver(event) {
    event.preventDefault();
    dragOver = true;
  }
  
  function handleDragLeave() {
    dragOver = false;
  }
  
  function handleDrop(event) {
    event.preventDefault();
    dragOver = false;
    
    const files = Array.from(event.dataTransfer.files);
    addVideos(files);
  }
  
  function continueToAnalysis() {
    if (!canContinue) return;
    
    // Valida parametri obbligatori
    if (!speed || speed <= 0) {
      alert('Inserisci la velocità del tapis roulant (km/h)');
      return;
    }
    
    if (!fps || fps <= 0) {
      alert('Inserisci gli FPS del video');
      return;
    }
    
    analysisStore.setCalibration(speed, fps, height, mass);
    analysisStore.nextStep();
  }
  
  function formatFileSize(bytes) {
    return (bytes / 1024 / 1024).toFixed(2);
  }
</script>

<div class="step-container">
  <h3>Carica 5 Video Baseline</h3>
  <p class="step-description">
    Seleziona 5 video della tua corsa ottimale registrati da <strong>vista posteriore</strong>. Questi video verranno utilizzati per creare il modello di riferimento.
  </p>
  
  <div class="instruction-box">
    <h4>📹 Istruzioni per la Registrazione</h4>
    <p><strong>IMPORTANTE:</strong> I video devono essere registrati esclusivamente da una <strong>vista posteriore</strong>.</p>
    <ul>
      <li>Posizionare la telecamera su un treppiede stabile</li>
      <li>Altezza della telecamera: all'altezza del bacino</li>
      <li>Posizione: direttamente dietro il tapis roulant</li>
      <li>Assicurarsi che tutto il corpo sia visibile nel frame</li>
    </ul>
  </div>
  
  <!-- Progress Indicator -->
  <div class="progress-indicator" class:complete={canContinue}>
    <div class="progress-bar">
      <div class="progress-fill" style="width: {(videosCount / 5) * 100}%"></div>
    </div>
    <span class="progress-text">{videosCount} / 5 video caricati</span>
  </div>
  
  <!-- Upload Area -->
  {#if videosCount < 5}
    <div 
      class="upload-area" 
      class:drag-over={dragOver}
      on:dragover={handleDragOver}
      on:dragleave={handleDragLeave}
      on:drop={handleDrop}
    >
      <input 
        type="file" 
        bind:this={fileInput}
        accept="video/*" 
        multiple
        on:change={handleFileSelect}
        id="video-upload"
        style="display: none;"
      />
      <label for="video-upload" class="upload-label">
        <div class="upload-icon">📹</div>
        <div class="upload-text">
          <strong>Clicca per selezionare</strong> o trascina i video qui
        </div>
        <div class="upload-hint">
          Ancora {5 - videosCount} video richiesti
        </div>
      </label>
    </div>
  {/if}
  
  <!-- Video List -->
  {#if videosCount > 0}
    <div class="video-list">
      {#each baselineVideos as video, index}
        <div class="video-card">
          <div class="video-number">{index + 1}</div>
          <div class="video-preview">
            <video src={baselineVideoUrls[index]} class="thumbnail">
              <track kind="captions" />
            </video>
          </div>
          <div class="video-info">
            <div class="video-name">{video.name}</div>
            <div class="video-size">{formatFileSize(video.size)} MB</div>
          </div>
          <button 
            class="remove-btn" 
            on:click={() => removeVideo(index)}
            title="Rimuovi video"
          >
            ×
          </button>
        </div>
      {/each}
    </div>
  {/if}
  
  <!-- Calibration Form (solo quando 5 video sono caricati) -->
  {#if canContinue}
    <div class="calibration-section">
      <h4>Parametri Calibrazione</h4>
      
      <div class="calibration-form">
        <div class="form-group">
          <label for="speed">Velocità Tapis Roulant: <span class="required">*</span></label>
          <input 
            type="number" 
            id="speed" 
            bind:value={speed} 
            min="1" 
            max="50" 
            step="0.1"
            required
            placeholder="es. 12"
          />
          <span class="unit">km/h</span>
        </div>
        
        <div class="form-group">
          <label for="fps">FPS Video: <span class="required">*</span></label>
          <input 
            type="number" 
            id="fps" 
            bind:value={fps} 
            min="15" 
            max="240" 
            step="1"
            required
            placeholder="es. 60"
          />
          <span class="unit">fps</span>
        </div>
        
        <div class="form-group">
          <label for="height">Altezza:</label>
          <input 
            type="number" 
            id="height" 
            bind:value={height} 
            min="100" 
            max="250" 
            step="1"
          />
          <span class="unit">cm</span>
        </div>
        
        <div class="form-group">
          <label for="mass">Massa:</label>
          <input 
            type="number" 
            id="mass" 
            bind:value={mass} 
            min="30" 
            max="200" 
            step="1"
          />
          <span class="unit">kg</span>
        </div>
      </div>
    </div>
  {/if}
  
  <button 
    class="btn-primary" 
    on:click={continueToAnalysis}
    disabled={!canContinue || !speed || !fps}
  >
    {#if canContinue}
      Continua →
    {:else}
      Carica {5 - videosCount} video rimanenti
    {/if}
  </button>
</div>

<style>
  @import './steps-common.css';
  
  .progress-indicator {
    margin-bottom: 1.5rem;
  }
  
  .progress-bar {
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 0.5rem;
  }
  
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent-color), var(--success-color));
    transition: width 0.3s ease;
  }
  
  .progress-indicator.complete .progress-fill {
    background: var(--success-color);
  }
  
  .progress-text {
    display: block;
    text-align: center;
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.7);
    font-weight: 600;
  }
  
  .upload-area {
    margin-bottom: 1rem;
    border: 2px dashed rgba(255, 255, 255, 0.3);
    border-radius: 8px;
    background: rgba(52, 152, 219, 0.05);
    transition: all 0.3s ease;
  }
  
  .upload-area.drag-over {
    border-color: var(--success-color);
    background: rgba(46, 204, 113, 0.1);
    transform: scale(1.02);
  }
  
  .upload-label {
    display: block;
    padding: 2rem;
    text-align: center;
    cursor: pointer;
  }
  
  .upload-icon {
    font-size: 3rem;
    margin-bottom: 0.75rem;
    opacity: 0.7;
  }
  
  .upload-text {
    font-size: 1rem;
    margin-bottom: 0.5rem;
    color: var(--text-light);
  }
  
  .upload-hint {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.5);
  }
  
  .video-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-bottom: 1rem;
    max-height: 350px;
    overflow-y: auto;
    padding-right: 0.5rem;
  }
  
  .video-list::-webkit-scrollbar {
    width: 6px;
  }
  
  .video-list::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 3px;
  }
  
  .video-list::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 3px;
  }
  
  .video-card {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
    animation: slideIn 0.3s ease;
  }
  
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(-10px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }
  
  .video-card:hover {
    background: rgba(0, 0, 0, 0.4);
    border-color: var(--accent-color);
  }
  
  .video-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: var(--accent-color);
    border-radius: 50%;
    font-weight: 700;
    font-size: 0.95rem;
    flex-shrink: 0;
  }
  
  .video-preview {
    width: 80px;
    height: 60px;
    border-radius: 4px;
    overflow: hidden;
    background: rgba(0, 0, 0, 0.5);
    flex-shrink: 0;
  }
  
  .thumbnail {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .video-info {
    flex: 1;
    min-width: 0;
  }
  
  .video-name {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-light);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-bottom: 0.25rem;
  }
  
  .video-size {
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.5);
  }
  
  .remove-btn {
    width: 32px;
    height: 32px;
    background: var(--error-color);
    border: none;
    border-radius: 50%;
    color: white;
    font-size: 1.5rem;
    line-height: 1;
    cursor: pointer;
    transition: all 0.3s ease;
    flex-shrink: 0;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .remove-btn:hover {
    background: #c0392b;
    transform: rotate(90deg);
  }
  
  .required {
    color: #e74c3c;
  }
  
  input[type="number"]:invalid {
    border-color: #e74c3c;
  }
  
  .calibration-section {
    background: rgba(46, 204, 113, 0.1);
    border: 1px solid var(--success-color);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    animation: slideIn 0.3s ease;
  }
  
  .calibration-section h4 {
    color: var(--success-color);
    margin-bottom: 0.75rem;
  }
  
  .btn-primary {
    background: var(--success-color);
  }
  
  .btn-primary:hover:not(:disabled) {
    background: #27ae60;
  }
  
  .btn-primary:disabled {
    background: rgba(255, 255, 255, 0.2);
  }
</style>

