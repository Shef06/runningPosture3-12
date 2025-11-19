<script>
  let file = null;
  let loading = false;
  let result = null;
  let videoUrl = null;
  
  function handleFileSelect(event) {
    const selectedFile = event.target.files[0];
    
    if (selectedFile) {
      file = selectedFile;
      
      // Crea URL per preview video
      if (videoUrl) {
        URL.revokeObjectURL(videoUrl);
      }
      videoUrl = URL.createObjectURL(selectedFile);
      
      result = null;
    }
  }
  
  async function analyzeVideo() {
    if (!file) {
      result = {
        status: 'error',
        message: 'Seleziona un video da analizzare'
      };
      return;
    }
    
    loading = true;
    result = null;
    
    try {
      const formData = new FormData();
      formData.append('video', file);
      
      const response = await fetch('http://localhost:5000/api/detect_anomaly', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      result = data;
    } catch (error) {
      result = {
        status: 'error',
        message: `Errore di connessione: ${error.message}`
      };
    } finally {
      loading = false;
    }
  }
  
  function resetAnalysis() {
    file = null;
    result = null;
    if (videoUrl) {
      URL.revokeObjectURL(videoUrl);
      videoUrl = null;
    }
    document.getElementById('analysis-input').value = '';
  }
</script>

<div class="analysis-container">
  <div class="video-section">
    <h2>Analizza Corsa</h2>
    
    {#if !videoUrl}
      <div class="video-placeholder">
        <div class="placeholder-content">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
          <p>Video Placeholder</p>
        </div>
      </div>
    {:else}
      <video controls src={videoUrl} class="video-preview">
        <track kind="captions" />
      </video>
    {/if}
    
    <div class="upload-controls">
      <input 
        type="file" 
        id="analysis-input"
        accept="video/*" 
        on:change={handleFileSelect}
        disabled={loading}
      />
      <label for="analysis-input" class="upload-button">
        📹 Seleziona Video
      </label>
      
      {#if file}
        <button class="reset-button" on:click={resetAnalysis} disabled={loading}>
          🔄 Reset
        </button>
      {/if}
    </div>
    
    {#if file}
      <div class="file-info">
        <p><strong>File:</strong> {file.name}</p>
        <p><strong>Dimensione:</strong> {(file.size / 1024 / 1024).toFixed(2)} MB</p>
      </div>
    {/if}
    
    <button 
      on:click={analyzeVideo} 
      disabled={loading || !file}
      class="analyze-button"
    >
      {#if loading}
        <span class="loading"></span> Analisi in corso...
      {:else}
        🔍 Analizza Corsa
      {/if}
    </button>
  </div>
  
  <div class="results-section">
    <h2>Risultati Analisi</h2>
    
    {#if result}
      {#if result.status === 'success'}
        <div class="result-card success-card" style="border-left: 4px solid {result.anomaly_color}">
          <div class="score-display">
            <div class="score-label">Anomaly Score</div>
            <div class="score-value" style="color: {result.anomaly_color}">
              {result.anomaly_score.toFixed(4)}
            </div>
          </div>
          
          <div class="level-display">
            <div class="level-badge" style="background: {result.anomaly_color}">
              {result.anomaly_level}
            </div>
          </div>
          
          <div class="interpretation">
            <h3>Interpretazione</h3>
            {#if result.anomaly_score < 0.01}
              <p>✓ Eccellente! La tua corsa è molto simile alla baseline ottimale.</p>
            {:else if result.anomaly_score < 0.05}
              <p>✓ Buono! La tua corsa è in linea con la baseline, con piccole variazioni.</p>
            {:else if result.anomaly_score < 0.1}
              <p>⚠ Moderato. Ci sono alcune differenze rispetto alla baseline ottimale.</p>
            {:else if result.anomaly_score < 0.25}
              <p>⚠ Attenzione! Deviazioni significative dal pattern biomeccanico ottimale.</p>
            {:else}
              <p>🚨 Critico! Pattern molto diverso dalla baseline. Consulta un professionista.</p>
            {/if}
          </div>
          
          {#if result.details}
            <div class="details">
              <h4>Dettagli Tecnici</h4>
              <ul>
                <li>Frame analizzati: {result.details.n_frames}</li>
                <li>Feature estratte: {result.details.n_features}</li>
              </ul>
            </div>
          {/if}
        </div>
      {:else}
        <div class="result-card error-card">
          <h3>Errore</h3>
          <p>{result.message}</p>
        </div>
      {/if}
    {:else}
      <div class="step-holder">
        <div class="step-placeholder">
          <p>I risultati dell'analisi appariranno qui</p>
          <div class="step-icon">📊</div>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .analysis-container {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 2rem;
    margin-top: 2rem;
  }
  
  @media (max-width: 968px) {
    .analysis-container {
      grid-template-columns: 1fr;
    }
  }
  
  .video-section, .results-section {
    background: var(--secondary-bg);
    border-radius: var(--border-radius);
    padding: 2rem;
    box-shadow: var(--box-shadow);
  }
  
  h2 {
    color: var(--text-light);
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
  }
  
  .video-placeholder {
    width: 100%;
    aspect-ratio: 16/9;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1.5rem;
  }
  
  .placeholder-content {
    text-align: center;
    color: rgba(255, 255, 255, 0.5);
  }
  
  .placeholder-content svg {
    margin-bottom: 1rem;
    opacity: 0.5;
  }
  
  .video-preview {
    width: 100%;
    aspect-ratio: 16/9;
    border-radius: 8px;
    background: black;
    margin-bottom: 1.5rem;
  }
  
  .upload-controls {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
  }
  
  input[type="file"] {
    display: none;
  }
  
  .upload-button {
    flex: 1;
    padding: 0.75rem 1.5rem;
    background: var(--accent-color);
    color: white;
    border-radius: 8px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    font-weight: 500;
  }
  
  .upload-button:hover {
    background: #2980b9;
    transform: translateY(-2px);
  }
  
  .reset-button {
    padding: 0.75rem 1.5rem;
    background: var(--warning-color);
  }
  
  .reset-button:hover:not(:disabled) {
    background: #e67e22;
  }
  
  .file-info {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1.5rem;
    font-size: 0.9rem;
  }
  
  .file-info p {
    margin-bottom: 0.5rem;
  }
  
  .analyze-button {
    width: 100%;
    background: var(--success-color);
    font-size: 1.1rem;
    padding: 1rem;
  }
  
  .analyze-button:hover:not(:disabled) {
    background: #27ae60;
  }
  
  .step-holder {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .step-placeholder {
    text-align: center;
    color: rgba(255, 255, 255, 0.5);
  }
  
  .step-icon {
    font-size: 4rem;
    margin-top: 1rem;
    opacity: 0.3;
  }
  
  .result-card {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    padding: 1.5rem;
    animation: slideIn 0.3s ease;
  }
  
  .score-display {
    text-align: center;
    margin-bottom: 1.5rem;
  }
  
  .score-label {
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 0.5rem;
  }
  
  .score-value {
    font-size: 3rem;
    font-weight: 700;
  }
  
  .level-display {
    text-align: center;
    margin-bottom: 1.5rem;
  }
  
  .level-badge {
    display: inline-block;
    padding: 0.5rem 1.5rem;
    border-radius: 20px;
    font-weight: 600;
    color: white;
  }
  
  .interpretation {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
  }
  
  .interpretation h3 {
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
  }
  
  .interpretation p {
    line-height: 1.5;
  }
  
  .details {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 1rem;
  }
  
  .details h4 {
    font-size: 0.95rem;
    margin-bottom: 0.5rem;
  }
  
  .details ul {
    list-style: none;
    font-size: 0.9rem;
  }
  
  .details li {
    margin-bottom: 0.25rem;
  }
  
  .error-card {
    border-left: 4px solid var(--error-color);
  }
  
  .error-card h3 {
    color: var(--error-color);
    margin-bottom: 0.5rem;
  }
</style>

