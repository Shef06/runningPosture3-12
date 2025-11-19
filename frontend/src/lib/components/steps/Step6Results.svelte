<script>
  import { analysisStore } from '../../stores/analysisStore.js';
  
  $: results = $analysisStore.results;
  $: mainFlow = $analysisStore.mainFlow;
  
  function restartAnalysis() {
    analysisStore.reset();
  }
</script>

<div class="step-container">
  <h3>Risultati Analisi</h3>
  
  {#if results}
    {#if mainFlow === 'baseline' || results.baselineCreated}
      <!-- Risultati creazione baseline -->
      <div class="result-card success-card">
        <div class="success-icon">✅</div>
        <h4>Baseline Creata con Successo!</h4>
        <p>Il modello di riferimento biomeccanico è stato creato dai 5 video ottimali.</p>
        
        {#if results.baselineRanges || results.details?.feature_ranges}
          <div class="biomechanics-section baseline-section">
            <h4>📊 Range Baseline Biomeccanici (dal backend)</h4>
            <p class="baseline-description">
              Questi sono i range (min-max) di riferimento della corsa ottimale, calcolati dal backend dall'analisi dei 5 video.
            </p>
            
            {#if results.baselineRanges || results.details?.biomechanics}
              {@const biomechRanges = results.baselineRanges || results.details?.biomechanics || {}}
              
              {#if biomechRanges.leftKneeAngle}
              <div class="bio-metric">
                <h5>🦵 Angolo Ginocchio Sinistro</h5>
                <div class="range-display">
                  <div class="range-bar">
                    <span class="range-label">Min</span>
                    <div class="range-visual">
                      <div class="range-line"></div>
                    </div>
                    <span class="range-label">Max</span>
                  </div>
                  <div class="range-values">
                    <span class="range-value min">{biomechRanges.leftKneeAngle.min}{biomechRanges.leftKneeAngle.unit || '°'}</span>
                    <span class="range-separator">—</span>
                    <span class="range-value max">{biomechRanges.leftKneeAngle.max}{biomechRanges.leftKneeAngle.unit || '°'}</span>
                  </div>
                </div>
              </div>
            {/if}
            
            {#if biomechRanges.rightKneeAngle}
              <div class="bio-metric">
                <h5>🦵 Angolo Ginocchio Destro</h5>
                <div class="range-display">
                  <div class="range-bar">
                    <span class="range-label">Min</span>
                    <div class="range-visual">
                      <div class="range-line"></div>
                    </div>
                    <span class="range-label">Max</span>
                  </div>
                  <div class="range-values">
                    <span class="range-value min">{biomechRanges.rightKneeAngle.min}{biomechRanges.rightKneeAngle.unit || '°'}</span>
                    <span class="range-separator">—</span>
                    <span class="range-value max">{biomechRanges.rightKneeAngle.max}{biomechRanges.rightKneeAngle.unit || '°'}</span>
                  </div>
                </div>
              </div>
            {/if}
            
            {#if biomechRanges.pelvicDrop}
              <div class="bio-metric">
                <h5>⚖️ Caduta Pelvica</h5>
                <div class="range-display">
                  <div class="range-bar">
                    <span class="range-label">Min</span>
                    <div class="range-visual">
                      <div class="range-line"></div>
                    </div>
                    <span class="range-label">Max</span>
                  </div>
                  <div class="range-values">
                    <span class="range-value min">{biomechRanges.pelvicDrop.min}{biomechRanges.pelvicDrop.unit || '%'}</span>
                    <span class="range-separator">—</span>
                    <span class="range-value max">{biomechRanges.pelvicDrop.max}{biomechRanges.pelvicDrop.unit || '%'}</span>
                  </div>
                </div>
              </div>
            {/if}
            
            {#if biomechRanges.trunkInclination}
              <div class="bio-metric">
                <h5>📐 Inclinazione Tronco</h5>
                <div class="range-display">
                  <div class="range-bar">
                    <span class="range-label">Min</span>
                    <div class="range-visual">
                      <div class="range-line"></div>
                    </div>
                    <span class="range-label">Max</span>
                  </div>
                  <div class="range-values">
                    <span class="range-value min">{biomechRanges.trunkInclination.min}{biomechRanges.trunkInclination.unit || '°'}</span>
                    <span class="range-separator">—</span>
                    <span class="range-value max">{biomechRanges.trunkInclination.max}{biomechRanges.trunkInclination.unit || '°'}</span>
                  </div>
                </div>
              </div>
              {/if}
            {/if}
            
            {#if results.details?.feature_ranges || results.baselineRanges?.features}
              {@const ranges = results.details?.feature_ranges || results.baselineRanges?.features || {}}
              
              {#if ranges.cpd}
                <div class="bio-metric">
                  <h5>⚖️ CPD (Caduta Pelvica Controlaterale)</h5>
                  <div class="range-display">
                    <div class="range-values">
                      <span class="range-value min">{ranges.cpd.min}{ranges.cpd.unit || '°'}</span>
                      <span class="range-separator">—</span>
                      <span class="range-value max">{ranges.cpd.max}{ranges.cpd.unit || '°'}</span>
                    </div>
                  </div>
                </div>
              {/if}
              
              {#if ranges.bos}
                <div class="bio-metric">
                  <h5>👣 Base d'Appoggio (BoS)</h5>
                  <div class="range-display">
                    <div class="range-values">
                      <span class="range-value min">{ranges.bos.min}{ranges.bos.unit || 'm'}</span>
                      <span class="range-separator">—</span>
                      <span class="range-value max">{ranges.bos.max}{ranges.bos.unit || 'm'}</span>
                    </div>
                  </div>
                </div>
              {/if}
              
              {#if ranges.eversion}
                <div class="bio-metric">
                  <h5>🦶 Eversione Retropiede</h5>
                  <div class="range-display">
                    <div class="range-values">
                      <span class="range-value min">{ranges.eversion.min}{ranges.eversion.unit || '°'}</span>
                      <span class="range-separator">—</span>
                      <span class="range-value max">{ranges.eversion.max}{ranges.eversion.unit || '°'}</span>
                    </div>
                  </div>
                </div>
              {/if}
              
              {#if ranges.trunkLean}
                <div class="bio-metric">
                  <h5>📐 Inclinazione Tronco Laterale</h5>
                  <div class="range-display">
                    <div class="range-values">
                      <span class="range-value min">{ranges.trunkLean.min}{ranges.trunkLean.unit || '°'}</span>
                      <span class="range-separator">—</span>
                      <span class="range-value max">{ranges.trunkLean.max}{ranges.trunkLean.unit || '°'}</span>
                    </div>
                  </div>
                </div>
              {/if}
              
              {#if ranges.gct}
                <div class="bio-metric">
                  <h5>🦶 Ground Contact Time (GCT)</h5>
                  <div class="range-display">
                    <div class="range-values">
                      <span class="range-value min">{ranges.gct.min}{ranges.gct.unit || 'ms'}</span>
                      <span class="range-separator">—</span>
                      <span class="range-value max">{ranges.gct.max}{ranges.gct.unit || 'ms'}</span>
                    </div>
                  </div>
                </div>
              {/if}
              
              {#if ranges.cadence}
                <div class="bio-metric">
                  <h5>🏃 Cadenza</h5>
                  <div class="range-display">
                    <div class="range-values">
                      <span class="range-value min">{ranges.cadence.min}{ranges.cadence.unit || 'passi/min'}</span>
                      <span class="range-separator">—</span>
                      <span class="range-value max">{ranges.cadence.max}{ranges.cadence.unit || 'passi/min'}</span>
                    </div>
                  </div>
                </div>
              {/if}
            {/if}
          </div>
        {/if}
      </div>
      
    {:else}
      <!-- Risultati analisi anomalia -->
      <div class="result-card" style="border-left: 4px solid {results.anomaly_color}">
        <div class="score-display">
          <div class="score-label">Anomaly Score</div>
          <div class="score-value" style="color: {results.anomaly_color}">
            {results.anomaly_score?.toFixed(4)}
          </div>
        </div>
        
        <div class="level-display">
          <div class="level-badge" style="background: {results.anomaly_color}">
            {results.anomaly_level}
          </div>
        </div>
        
        <div class="interpretation">
          <h4>Interpretazione</h4>
          {#if results.anomaly_level === 'Ottimale'}
            <p>✓ Eccellente! La tua corsa è molto simile alla baseline ottimale.</p>
          {:else if results.anomaly_level === 'Buono'}
            <p>✓ Buono! La tua corsa è in linea con la baseline, con piccole variazioni.</p>
          {:else if results.anomaly_level === 'Moderato'}
            <p>⚠ Moderato. Ci sono alcune differenze rispetto alla baseline ottimale.</p>
          {:else if results.anomaly_level === 'Attenzione'}
            <p>⚠ Attenzione! Deviazioni significative dal pattern biomeccanico ottimale.</p>
          {:else if results.anomaly_level === 'Critico'}
            <p>🚨 Critico! Pattern molto diverso dalla baseline. Consulta un professionista.</p>
          {:else}
            <p>📊 Analisi completata. Livello: {results.anomaly_level || 'N/A'}</p>
          {/if}
        </div>
        
        {#if results.feature_metrics}
          <!-- Panoramica Spazio-Temporale (dati dal backend) -->
          <div class="biomechanics-section">
            <h4>⏱️ Panoramica Spazio-Temporale</h4>
            
            <div class="bio-metric">
              <h5>🦶 Ground Contact Time (GCT)</h5>
              <div class="metric-stats">
                <div class="stat-item">
                  <span class="stat-label">Media:</span>
                  <span class="stat-value">{results.feature_metrics.gct?.mean || results.metrics_avg?.gct_mean || 'N/A'}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Min:</span>
                  <span class="stat-value">{results.feature_metrics.gct?.min || 'N/A'}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Max:</span>
                  <span class="stat-value">{results.feature_metrics.gct?.max || 'N/A'}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Std:</span>
                  <span class="stat-value">{results.feature_metrics.gct?.std || 'N/A'}</span>
                </div>
              </div>
              <p class="metric-description">Tempo di contatto al suolo per ciclo di falcata (ms)</p>
            </div>
            
            <div class="bio-metric">
              <h5>🏃 Cadenza</h5>
              <div class="metric-stats">
                <div class="stat-item">
                  <span class="stat-label">Media:</span>
                  <span class="stat-value">{results.feature_metrics.cadence?.mean || results.metrics_avg?.cadence_mean || 'N/A'}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Min:</span>
                  <span class="stat-value">{results.feature_metrics.cadence?.min || 'N/A'}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Max:</span>
                  <span class="stat-value">{results.feature_metrics.cadence?.max || 'N/A'}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Std:</span>
                  <span class="stat-value">{results.feature_metrics.cadence?.std || 'N/A'}</span>
                </div>
              </div>
              <p class="metric-description">Numero di passi al minuto</p>
            </div>
          </div>
          
          <!-- Analisi Piano Frontale (dati dal backend) -->
          <div class="biomechanics-section">
            <h4>📐 Analisi Piano Frontale</h4>
            
            <div class="bio-metric">
              <h5>⚖️ Caduta Pelvica Controlaterale (CPD)</h5>
              <div class="metric-stats">
                <div class="stat-item">
                  <span class="stat-label">Media:</span>
                  <span class="stat-value">{results.feature_metrics.cpd?.mean || results.metrics_avg?.cpd_mean || 'N/A'}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Min:</span>
                  <span class="stat-value">{results.feature_metrics.cpd?.min || 'N/A'}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Max:</span>
                  <span class="stat-value">{results.feature_metrics.cpd?.max || 'N/A'}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Std:</span>
                  <span class="stat-value">{results.feature_metrics.cpd?.std || 'N/A'}</span>
                </div>
              </div>
              <p class="metric-description">Angolo della linea bi-iliaca rispetto all'orizzontale ({results.feature_metrics.cpd?.unit || '°'})</p>
            </div>
            
            <div class="bio-metric">
              <h5>👣 Base d'Appoggio (BoS)</h5>
              <div class="metric-stats">
                <div class="stat-item">
                  <span class="stat-label">Media:</span>
                  <span class="stat-value">{results.feature_metrics.bos?.mean || results.metrics_avg?.bos_mean || 'N/A'}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Min:</span>
                  <span class="stat-value">{results.feature_metrics.bos?.min || 'N/A'}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Max:</span>
                  <span class="stat-value">{results.feature_metrics.bos?.max || 'N/A'}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Std:</span>
                  <span class="stat-value">{results.feature_metrics.bos?.std || 'N/A'}</span>
                </div>
              </div>
              <p class="metric-description">Distanza mediolaterale tra le caviglie ({results.feature_metrics.bos?.unit || 'm'})</p>
            </div>
            
            <div class="bio-metric">
              <h5>🦶 Eversione Retropiede</h5>
              <div class="metric-stats">
                <div class="stat-item">
                  <span class="stat-label">Media:</span>
                  <span class="stat-value">{results.feature_metrics.rearfoot_eversion?.mean || results.metrics_avg?.rearfoot_eversion_mean || 'N/A'}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Min:</span>
                  <span class="stat-value">{results.feature_metrics.rearfoot_eversion?.min || 'N/A'}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Max:</span>
                  <span class="stat-value">{results.feature_metrics.rearfoot_eversion?.max || 'N/A'}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Std:</span>
                  <span class="stat-value">{results.feature_metrics.rearfoot_eversion?.std || 'N/A'}</span>
                </div>
              </div>
              <p class="metric-description">Angolo di eversione del retropiede ({results.feature_metrics.rearfoot_eversion?.unit || '°'})</p>
            </div>
            
            <div class="bio-metric">
              <h5>📐 Inclinazione Tronco Laterale</h5>
              <div class="metric-stats">
                <div class="stat-item">
                  <span class="stat-label">Media:</span>
                  <span class="stat-value">{results.feature_metrics.lateral_trunk_lean?.mean || results.metrics_avg?.lateral_trunk_lean_mean || 'N/A'}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Min:</span>
                  <span class="stat-value">{results.feature_metrics.lateral_trunk_lean?.min || 'N/A'}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Max:</span>
                  <span class="stat-value">{results.feature_metrics.lateral_trunk_lean?.max || 'N/A'}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Std:</span>
                  <span class="stat-value">{results.feature_metrics.lateral_trunk_lean?.std || 'N/A'}</span>
                </div>
              </div>
              <p class="metric-description">Inclinazione laterale del tronco ({results.feature_metrics.lateral_trunk_lean?.unit || '°'})</p>
            </div>
          </div>
        {:else if results.metrics_avg}
          <!-- Fallback: usa metrics_avg se feature_metrics non disponibile (compatibilità) -->
          <div class="biomechanics-section">
            <h4>⏱️ Panoramica Spazio-Temporale</h4>
            
            <div class="bio-metric">
              <h5>🦶 Ground Contact Time (GCT) Medio</h5>
              <div class="metric-value">
                <span class="value">{results.metrics_avg.gct_mean}</span>
                <span class="unit">ms</span>
              </div>
              <p class="metric-description">Tempo medio di contatto al suolo per ciclo di falcata</p>
            </div>
            
            <div class="bio-metric">
              <h5>🏃 Cadenza Media</h5>
              <div class="metric-value">
                <span class="value">{results.metrics_avg.cadence_mean}</span>
                <span class="unit">passi/min</span>
              </div>
              <p class="metric-description">Numero medio di passi al minuto</p>
            </div>
          </div>
          
          <div class="biomechanics-section">
            <h4>📐 Analisi Piano Frontale</h4>
            
            <div class="bio-metric">
              <h5>⚖️ Caduta Pelvica Media (CPD)</h5>
              <div class="metric-value">
                <span class="value">{results.metrics_avg.cpd_mean}</span>
                <span class="unit">°</span>
              </div>
              <p class="metric-description">Angolo della linea bi-iliaca rispetto all'orizzontale</p>
            </div>
            
            <div class="bio-metric">
              <h5>👣 Base d'Appoggio Media (BoS)</h5>
              <div class="metric-value">
                <span class="value">{results.metrics_avg.bos_mean}</span>
                <span class="unit">m</span>
              </div>
              <p class="metric-description">Distanza mediolaterale tra le caviglie durante l'appoggio</p>
            </div>
            
            <div class="bio-metric">
              <h5>🦶 Eversione Retropiede Media</h5>
              <div class="metric-value">
                <span class="value">{results.metrics_avg.rearfoot_eversion_mean}</span>
                <span class="unit">°</span>
              </div>
              <p class="metric-description">Angolo di eversione del retropiede (caviglia-tallone-punta piede)</p>
            </div>
            
            <div class="bio-metric">
              <h5>📐 Inclinazione Tronco Media</h5>
              <div class="metric-value">
                <span class="value">{results.metrics_avg.lateral_trunk_lean_mean}</span>
                <span class="unit">°</span>
              </div>
              <p class="metric-description">Inclinazione laterale del tronco rispetto alla verticale</p>
            </div>
          </div>
        {/if}
        
        {#if results.metrics_stability}
          <!-- Stabilità (Variabilità) -->
          <div class="biomechanics-section stability-section">
            <h4>📊 Stabilità (Variabilità)</h4>
            <p class="section-description">Coefficiente di Variazione (CV) - Indica la variabilità stride-to-stride. Valori elevati possono indicare affaticamento o instabilità.</p>
            
            <div class="bio-metric">
              <h5>🦶 Variabilità GCT</h5>
              <div class="metric-value">
                <span class="value">{results.metrics_stability.gct_cv}</span>
                <span class="unit">%</span>
              </div>
              <p class="metric-description">Coefficiente di variazione del Ground Contact Time</p>
            </div>
            
            <div class="bio-metric">
              <h5>⏱️ Variabilità Tempo Falcata</h5>
              <div class="metric-value">
                <span class="value">{results.metrics_stability.stride_time_cv}</span>
                <span class="unit">%</span>
              </div>
              <p class="metric-description">Coefficiente di variazione del tempo di falcata</p>
            </div>
          </div>
        {/if}
        
        {#if results.metrics_asymmetry}
          <!-- Simmetria (Asimmetria) -->
          <div class="biomechanics-section asymmetry-section">
            <h4>⚖️ Simmetria (Asimmetria)</h4>
            <p class="section-description">Indici di asimmetria bilaterale. Valori elevati indicano differenze significative tra lato sinistro e destro.</p>
            
            <div class="bio-metric">
              <h5>🦶 Asimmetria GCT</h5>
              <div class="metric-value">
                <span class="value">{results.metrics_asymmetry.gct_si}</span>
                <span class="unit">%</span>
              </div>
              <p class="metric-description">Symmetry Index del Ground Contact Time (differenza sinistra/destra)</p>
            </div>
            
            <div class="bio-metric">
              <h5>⚖️ Asimmetria CPD</h5>
              <div class="metric-value">
                <span class="value">{results.metrics_asymmetry.cpd_sa}</span>
                <span class="unit">%</span>
              </div>
              <p class="metric-description">Symmetry Angle della Caduta Pelvica Controlaterale</p>
            </div>
          </div>
        {/if}
      </div>
    {/if}
    
    <button class="btn-restart" on:click={restartAnalysis}>
      🔄 Nuova Analisi
    </button>
    
  {:else}
    <div class="no-results">
      <p>Nessun risultato disponibile</p>
    </div>
  {/if}
</div>

<style>
  .step-container {
    padding: 0.5rem 0;
  }
  
  h3 {
    font-size: 1.2rem;
    margin-bottom: 1rem;
    color: var(--text-light);
  }
  
  h4 {
    font-size: 1rem;
    margin-bottom: 0.5rem;
    color: var(--text-light);
  }
  
  h5 {
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
    color: var(--text-light);
  }
  
  .result-card {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    padding: 1.25rem;
    margin-bottom: 1rem;
  }
  
  .success-card {
    border-left: 4px solid var(--success-color);
  }
  
  .success-icon {
    font-size: 3rem;
    text-align: center;
    margin-bottom: 0.75rem;
  }
  
  .score-display {
    text-align: center;
    margin-bottom: 1.25rem;
  }
  
  .score-label {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 0.4rem;
  }
  
  .score-value {
    font-size: 2.75rem;
    font-weight: 700;
  }
  
  .level-display {
    text-align: center;
    margin-bottom: 1.25rem;
  }
  
  .level-badge {
    display: inline-block;
    padding: 0.6rem 1.5rem;
    border-radius: 20px;
    font-weight: 600;
    color: white;
    font-size: 1rem;
  }
  
  .interpretation {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
  }
  
  .interpretation p {
    line-height: 1.5;
    color: rgba(255, 255, 255, 0.9);
    font-size: 0.9rem;
    margin: 0;
  }
  
  .details-section {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 1rem;
  }
  
  .detail-item {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    font-size: 0.85rem;
  }
  
  .detail-item:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }
  
  .label {
    font-weight: 600;
    color: rgba(255, 255, 255, 0.7);
  }
  
  .value {
    color: var(--text-light);
    font-weight: 600;
  }
  
  .btn-restart {
    width: 100%;
    background: var(--accent-color);
    color: white;
    border: none;
    padding: 0.85rem;
    font-size: 1rem;
    font-weight: 600;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .btn-restart:hover {
    background: #2980b9;
    transform: translateY(-1px);
  }
  
  .no-results {
    text-align: center;
    padding: 2rem;
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.9rem;
  }
  
  .biomechanics-section {
    margin-top: 1.5rem;
    padding: 1rem;
    background: rgba(52, 152, 219, 0.05);
    border-radius: 8px;
    border: 1px solid rgba(52, 152, 219, 0.2);
  }
  
  .baseline-section {
    background: rgba(46, 204, 113, 0.05);
    border-color: rgba(46, 204, 113, 0.3);
  }
  
  .baseline-description {
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 1rem;
    font-style: italic;
  }
  
  .biomechanics-section h4 {
    margin: 0 0 1rem 0;
    color: var(--accent-color);
    font-size: 1.1rem;
  }
  
  .bio-metric {
    margin-bottom: 1rem;
    padding: 0.75rem;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 6px;
  }
  
  .bio-metric:last-child {
    margin-bottom: 0;
  }
  
  .bio-metric h5 {
    margin: 0 0 0.5rem 0;
    color: var(--text-light);
    font-size: 0.95rem;
    font-weight: 600;
  }
  
  .metric-stats {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
  }
  
  .stat-item {
    display: flex;
    justify-content: space-between;
    padding: 0.4rem 0.6rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }
  
  .stat-label {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.7);
  }
  
  .stat-value {
    font-weight: 600;
    color: var(--success-color);
    font-size: 0.85rem;
  }
  
  /* Range display per baseline */
  .range-display {
    padding: 0.75rem;
  }
  
  .range-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
  }
  
  .range-label {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.5);
    text-transform: uppercase;
    font-weight: 700;
  }
  
  .range-visual {
    flex: 1;
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
  }
  
  .range-line {
    height: 100%;
    background: linear-gradient(90deg, var(--success-color), var(--accent-color));
    border-radius: 4px;
  }
  
  .range-values {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    font-size: 1.1rem;
  }
  
  .range-value {
    font-weight: 700;
    color: var(--success-color);
  }
  
  .range-value.min {
    color: var(--success-color);
  }
  
  .range-value.max {
    color: var(--accent-color);
  }
  
  .range-separator {
    color: rgba(255, 255, 255, 0.3);
    font-weight: 300;
  }
  
  /* Stili per le nuove metriche biomeccaniche */
  .metric-value {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }
  
  .metric-value .value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--accent-color);
  }
  
  .metric-value .unit {
    font-size: 1rem;
    color: rgba(255, 255, 255, 0.6);
    font-weight: 500;
  }
  
  .metric-description {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.6);
    margin: 0;
    font-style: italic;
  }
  
  .section-description {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 1rem;
    padding: 0.5rem;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
    font-style: italic;
  }
  
  .stability-section {
    border-left: 3px solid #3498db;
  }
  
  .asymmetry-section {
    border-left: 3px solid #9b59b6;
  }
</style>

