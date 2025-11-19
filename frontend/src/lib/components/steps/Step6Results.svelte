<script>
  import { analysisStore } from '../../stores/analysisStore.js';
  
  $: results = $analysisStore.results;
  $: mainFlow = $analysisStore.mainFlow;
  
  function restartAnalysis() {
    analysisStore.reset();
  }
</script>

<div class="step-container">
  <h3>Risultati</h3>
  
  {#if results}
    {#if mainFlow === 'baseline' || results.baselineCreated}
      <!-- Risultati baseline -->
      <div class="result-card success-card">
        <div class="success-header">
          <div class="success-icon">✅</div>
          <div>
            <h4>Baseline Creata</h4>
            <p class="compact-desc">Modello di riferimento biomeccanico creato</p>
          </div>
        </div>
        
        {#if results.baselineRanges || results.details?.feature_ranges}
          <div class="biomechanics-section">
            <h4>📊 Range Baseline</h4>
            
            <div class="metrics-grid">
              {#if results.baselineRanges || results.details?.biomechanics}
                {@const biomechRanges = results.baselineRanges || results.details?.biomechanics || {}}
                
                {#if biomechRanges.leftKneeAngle}
                <div class="metric-card compact">
                  <h5>🦵 Ginocchio SX</h5>
                  <div class="range-compact">
                    <span class="val">{biomechRanges.leftKneeAngle.min}</span>
                    <span class="sep">→</span>
                    <span class="val">{biomechRanges.leftKneeAngle.max}</span>
                    <span class="unit">{biomechRanges.leftKneeAngle.unit || '°'}</span>
                  </div>
                </div>
                {/if}
                
                {#if biomechRanges.rightKneeAngle}
                <div class="metric-card compact">
                  <h5>🦵 Ginocchio DX</h5>
                  <div class="range-compact">
                    <span class="val">{biomechRanges.rightKneeAngle.min}</span>
                    <span class="sep">→</span>
                    <span class="val">{biomechRanges.rightKneeAngle.max}</span>
                    <span class="unit">{biomechRanges.rightKneeAngle.unit || '°'}</span>
                  </div>
                </div>
                {/if}
                
                {#if biomechRanges.pelvicDrop}
                <div class="metric-card compact">
                  <h5>⚖️ Caduta Pelvica</h5>
                  <div class="range-compact">
                    <span class="val">{biomechRanges.pelvicDrop.min}</span>
                    <span class="sep">→</span>
                    <span class="val">{biomechRanges.pelvicDrop.max}</span>
                    <span class="unit">{biomechRanges.pelvicDrop.unit || '%'}</span>
                  </div>
                </div>
                {/if}
                
                {#if biomechRanges.trunkInclination}
                <div class="metric-card compact">
                  <h5>📐 Inclinazione</h5>
                  <div class="range-compact">
                    <span class="val">{biomechRanges.trunkInclination.min}</span>
                    <span class="sep">→</span>
                    <span class="val">{biomechRanges.trunkInclination.max}</span>
                    <span class="unit">{biomechRanges.trunkInclination.unit || '°'}</span>
                  </div>
                </div>
                {/if}
              {/if}
              
              {#if results.details?.feature_ranges || results.baselineRanges?.features}
                {@const ranges = results.details?.feature_ranges || results.baselineRanges?.features || {}}
                
                {#if ranges.cpd}
                <div class="metric-card compact">
                  <h5>⚖️ CPD</h5>
                  <div class="range-compact">
                    <span class="val">{ranges.cpd.min}</span>
                    <span class="sep">→</span>
                    <span class="val">{ranges.cpd.max}</span>
                    <span class="unit">{ranges.cpd.unit || '°'}</span>
                  </div>
                </div>
                {/if}
                
                {#if ranges.bos}
                <div class="metric-card compact">
                  <h5>👣 BoS</h5>
                  <div class="range-compact">
                    <span class="val">{ranges.bos.min}</span>
                    <span class="sep">→</span>
                    <span class="val">{ranges.bos.max}</span>
                    <span class="unit">{ranges.bos.unit || 'm'}</span>
                  </div>
                </div>
                {/if}
                
                {#if ranges.gct}
                <div class="metric-card compact">
                  <h5>🦶 GCT</h5>
                  <div class="range-compact">
                    <span class="val">{ranges.gct.min}</span>
                    <span class="sep">→</span>
                    <span class="val">{ranges.gct.max}</span>
                    <span class="unit">{ranges.gct.unit || 'ms'}</span>
                  </div>
                </div>
                {/if}
                
                {#if ranges.cadence}
                <div class="metric-card compact">
                  <h5>🏃 Cadenza</h5>
                  <div class="range-compact">
                    <span class="val">{ranges.cadence.min}</span>
                    <span class="sep">→</span>
                    <span class="val">{ranges.cadence.max}</span>
                    <span class="unit">{ranges.cadence.unit || 'spm'}</span>
                  </div>
                </div>
                {/if}
              {/if}
            </div>
          </div>
        {/if}
      </div>
      
    {:else}
      <!-- Risultati analisi -->
      <div class="result-card" style="border-left: 3px solid {results.anomaly_color}">
        <div class="score-compact">
          <div>
            <div class="score-label">Anomaly Score</div>
            <div class="score-value" style="color: {results.anomaly_color}">
              {results.anomaly_score?.toFixed(4)}
            </div>
          </div>
          <div class="level-badge" style="background: {results.anomaly_color}">
            {results.anomaly_level}
          </div>
        </div>
        
        <div class="interpretation compact">
          {#if results.anomaly_level === 'Ottimale'}
            <p>✓ Eccellente! Corsa simile alla baseline.</p>
          {:else if results.anomaly_level === 'Buono'}
            <p>✓ Buono! In linea con la baseline.</p>
          {:else if results.anomaly_level === 'Moderato'}
            <p>⚠ Alcune differenze dalla baseline.</p>
          {:else if results.anomaly_level === 'Attenzione'}
            <p>⚠ Deviazioni significative.</p>
          {:else if results.anomaly_level === 'Critico'}
            <p>🚨 Pattern molto diverso. Consulta professionista.</p>
          {:else}
            <p>📊 Livello: {results.anomaly_level || 'N/A'}</p>
          {/if}
        </div>
        
        {#if results.feature_metrics}
          <div class="metrics-grid">
            <!-- Spazio-Temporale -->
            <div class="metric-card">
              <h5>🦶 GCT</h5>
              <div class="stats-compact">
                <span class="stat"><b>μ:</b> {results.feature_metrics.gct?.mean || 'N/A'}</span>
                <span class="stat"><b>σ:</b> {results.feature_metrics.gct?.std || 'N/A'}</span>
              </div>
            </div>
            
            <div class="metric-card">
              <h5>🏃 Cadenza</h5>
              <div class="stats-compact">
                <span class="stat"><b>μ:</b> {results.feature_metrics.cadence?.mean || 'N/A'}</span>
                <span class="stat"><b>σ:</b> {results.feature_metrics.cadence?.std || 'N/A'}</span>
              </div>
            </div>
            
            <!-- Piano Frontale -->
            <div class="metric-card">
              <h5>⚖️ CPD</h5>
              <div class="stats-compact">
                <span class="stat"><b>μ:</b> {results.feature_metrics.cpd?.mean || 'N/A'}</span>
                <span class="stat"><b>σ:</b> {results.feature_metrics.cpd?.std || 'N/A'}</span>
              </div>
            </div>
            
            <div class="metric-card">
              <h5>👣 BoS</h5>
              <div class="stats-compact">
                <span class="stat"><b>μ:</b> {results.feature_metrics.bos?.mean || 'N/A'}</span>
                <span class="stat"><b>σ:</b> {results.feature_metrics.bos?.std || 'N/A'}</span>
              </div>
            </div>
            
            <div class="metric-card">
              <h5>🦶 Eversione</h5>
              <div class="stats-compact">
                <span class="stat"><b>μ:</b> {results.feature_metrics.rearfoot_eversion?.mean || 'N/A'}</span>
                <span class="stat"><b>σ:</b> {results.feature_metrics.rearfoot_eversion?.std || 'N/A'}</span>
              </div>
            </div>
            
            <div class="metric-card">
              <h5>📐 Tronco</h5>
              <div class="stats-compact">
                <span class="stat"><b>μ:</b> {results.feature_metrics.lateral_trunk_lean?.mean || 'N/A'}</span>
                <span class="stat"><b>σ:</b> {results.feature_metrics.lateral_trunk_lean?.std || 'N/A'}</span>
              </div>
            </div>
          </div>
        {/if}
        
        {#if results.metrics_stability}
          <div class="section-compact">
            <h4>📊 Stabilità (CV%)</h4>
            <div class="inline-stats">
              <span>GCT: <b>{results.metrics_stability.gct_cv}</b></span>
              <span>Stride: <b>{results.metrics_stability.stride_time_cv}</b></span>
            </div>
          </div>
        {/if}
        
        {#if results.metrics_asymmetry}
          <div class="section-compact">
            <h4>⚖️ Asimmetria</h4>
            <div class="inline-stats">
              <span>GCT SI: <b>{results.metrics_asymmetry.gct_si}%</b></span>
              <span>CPD SA: <b>{results.metrics_asymmetry.cpd_sa}%</b></span>
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
      <p>Nessun risultato</p>
    </div>
  {/if}
</div>

<style>
  .step-container {
    padding: 1rem;
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  
  h3 {
    font-size: 1.2rem;
    margin-bottom: 0.75rem;
    color: var(--text-light);
  }
  
  h4 {
    font-size: 0.95rem;
    margin-bottom: 0.5rem;
    color: var(--text-light);
  }
  
  h5 {
    font-size: 0.8rem;
    margin: 0 0 0.25rem 0;
    color: var(--text-muted);
    font-weight: 600;
  }
  
  .result-card {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 0.75rem;
  }
  
  .success-card {
    border-left: 3px solid var(--success-color);
  }
  
  .success-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }
  
  .success-icon {
    font-size: 2rem;
  }
  
  .compact-desc {
    font-size: 0.8rem;
    color: var(--text-muted);
    margin: 0;
  }
  
  .score-compact {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
    gap: 1rem;
  }
  
  .score-label {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 0.25rem;
  }
  
  .score-value {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1;
  }
  
  .level-badge {
    padding: 0.5rem 1rem;
    border-radius: 16px;
    font-weight: 600;
    color: white;
    font-size: 0.85rem;
    white-space: nowrap;
  }
  
  .interpretation {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 0.75rem;
    margin-bottom: 0.75rem;
  }
  
  .interpretation.compact p {
    font-size: 0.85rem;
    line-height: 1.4;
    margin: 0;
  }
  
  .biomechanics-section {
    margin-top: 1rem;
  }
  
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
  }
  
  .metric-card {
    background: rgba(0, 0, 0, 0.3);
    border-radius: 8px;
    padding: 0.6rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .metric-card.compact {
    padding: 0.5rem;
  }
  
  .range-compact {
    display: flex;
    align-items: baseline;
    gap: 0.4rem;
    font-size: 0.9rem;
  }
  
  .range-compact .val {
    color: var(--success-color);
    font-weight: 700;
  }
  
  .range-compact .sep {
    color: rgba(255, 255, 255, 0.3);
  }
  
  .range-compact .unit {
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.75rem;
  }
  
  .stats-compact {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
  }
  
  .stat {
    font-size: 0.8rem;
    color: var(--text-muted);
  }
  
  .stat b {
    color: var(--accent-primary);
    font-weight: 700;
  }
  
  .section-compact {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 0.6rem;
    margin-top: 0.75rem;
  }
  
  .section-compact h4 {
    font-size: 0.85rem;
    margin-bottom: 0.4rem;
  }
  
  .inline-stats {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    font-size: 0.8rem;
    color: var(--text-muted);
  }
  
  .inline-stats b {
    color: var(--accent-primary);
  }
  
  .btn-restart {
    width: 100%;
    background: var(--accent-primary);
    color: white;
    border: none;
    padding: 0.75rem;
    font-size: 0.9rem;
    font-weight: 600;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    margin-top: auto;
  }
  
  .btn-restart:hover {
    background: #2980b9;
    transform: translateY(-1px);
  }
  
  .no-results {
    text-align: center;
    padding: 1.5rem;
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.85rem;
  }
  
  /* RESPONSIVE */
  @media (max-width: 768px) {
    .metrics-grid {
      grid-template-columns: 1fr;
    }
    
    .score-compact {
      flex-direction: column;
      align-items: flex-start;
    }
    
    .inline-stats {
      flex-direction: column;
      gap: 0.5rem;
    }
  }
  
  @media (max-width: 576px) {
    .step-container {
      padding: 0.75rem;
    }
    
    h3 {
      font-size: 1.1rem;
    }
    
    .result-card {
      padding: 0.75rem;
    }
    
    .score-value {
      font-size: 1.75rem;
    }
    
    .metric-card {
      padding: 0.5rem;
    }
    
    .success-icon {
      font-size: 1.75rem;
    }
  }
</style>