<script>
  import { analysisStore } from '../../stores/analysisStore.js';
  import AnalysisChart from '../AnalysisChart.svelte';
  import { onMount } from 'svelte';
  
  $: results = $analysisStore.results;
  $: mainFlow = $analysisStore.mainFlow;
  $: viewType = results?.viewType || 'posterior';

  // Stato per il modal del grafico
  let expandedChart = null;  // { title, data, labels, color, baselineMean, baselineStd }
  
  // Stato per Ghost Vision - USA LO STORE invece di variabile locale
  $: ghostVisionEnabled = $analysisStore.ghostVisionEnabled;
  $: ghostVisionAvailable = results?.ghost_vision_available || false;
  
  // Debug: log sempre per vedere lo stato
  $: if (results) {
    console.log('🔍 ResultsStep - Stato Ghost Vision:', {
      hasResults: !!results,
      ghost_vision_available: results?.ghost_vision_available,
      ghost_frames_count: results?.ghost_frames_count,
      skeleton_video_url: results?.skeleton_video_url,
      calculatedAvailable: ghostVisionAvailable
    });
  }
  
  // Log quando Ghost Vision diventa disponibile
  $: if (ghostVisionAvailable && results) {
    console.log('='.repeat(60));
    console.log('👻 GHOST VISION DISPONIBILE NEI RISULTATI');
    console.log('='.repeat(60));
    console.log('📊 Frame ghost disponibili:', results.ghost_frames_count || 'N/A');
    console.log('🎬 Video skeleton:', results.skeleton_video_url ? 'Disponibile' : 'Non disponibile');
    console.log('✅ Toggle Ghost Vision visibile nell\'interfaccia');
    console.log('💡 Attiva il toggle per vedere la silhouette baseline');
    console.log('='.repeat(60));
  } else if (results && !ghostVisionAvailable) {
    console.log('⚠️ ResultsStep - Ghost Vision NON disponibile:', {
      ghost_vision_available: results?.ghost_vision_available,
      ghost_frames_count: results?.ghost_frames_count
    });
  }

  function restartAnalysis() {
    analysisStore.reset();
  }

  // Funzione helper per formattare i numeri
  function formatVal(val, decimals = 2) {
    if (val === null || val === undefined) return 'N/A';
    if (typeof val !== 'number') return val;
    return Number(val.toFixed(decimals));
  }

  // Funzione per ottenere emoji basata sul livello
  function getLevelEmoji(level) {
    if (level === 'Ottimale') return '✅';
    if (level === 'Attenzione') return '⚠️';
    if (level === 'Critico') return '🚨';
    return '📊';
  }

  // Apri modal grafico
  function openChartModal(title, data, labels, color, baselineMean, baselineStd, yAxisMin = null, yAxisMax = null, beginAtZero = true, unit = "") {
    expandedChart = { title, data, labels, color, baselineMean, baselineStd, yAxisMin, yAxisMax, beginAtZero, unit };
  }

  // Chiudi modal
  function closeChartModal() {
    expandedChart = null;
  }

  // Gestione ESC per chiudere modal
  onMount(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape' && expandedChart) {
        closeChartModal();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  });

  // Stato per salvataggio (non utilizzato al momento)
  let isSaving = false;

  // Funzione per salvare baseline (non funzionante al momento)
  function saveBaseline() {
    // Funzionalità disabilitata - da implementare in futuro
    console.log('Salvataggio baseline - funzionalità non ancora implementata');
  }

  // Funzione per salvare analisi (non funzionante al momento)
  function saveAnalysis() {
    // Funzionalità disabilitata - da implementare in futuro
    console.log('Salvataggio analisi - funzionalità non ancora implementata');
  }
  
  // Funzione per toggle Ghost Vision
  function toggleGhostVision() {
    const newState = !$analysisStore.ghostVisionEnabled;
    analysisStore.setGhostVision(newState);
    
    if (newState) {
      console.log('='.repeat(60));
      console.log('👻 GHOST VISION ATTIVATA');
      console.log('='.repeat(60));
      console.log('📹 Video: Skeleton video con overlay ghost');
      console.log('🎨 Silhouette: Ciano semitrasparente (50% opacità)');
      console.log('🔄 Sincronizzazione: Basata su timestamp video');
      console.log('📊 Frame disponibili:', results?.ghost_frames_count || 'N/A');
      console.log('✅ Overlay attivo - Confronto visivo disponibile');
      console.log('='.repeat(60));
    } else {
      console.log('👻 Ghost Vision DISATTIVATA');
      console.log('⏸️ Overlay rimosso dal video');
    }
  }
</script>

<div class="step-container">
  <h3>Risultati</h3>
  
  {#if results}
    {#if mainFlow === 'baseline' || results.baselineCreated}
      <!-- BASELINE CREATA -->
      <div class="result-card success-card">
        <div class="success-header">
          <div class="success-icon">✅</div>
          <div>
            <h4>Baseline Creata</h4>
            <p class="compact-desc">Statistiche di riferimento calcolate da 5 video</p>
          </div>
        </div>
        
        {#if results.baselineRanges}
          <div class="biomechanics-section">
            <h4>📊 Statistiche Baseline ({viewType === 'posterior' ? 'Vista Posteriore' : 'Vista Laterale'})</h4>
            
            <div class="metrics-grid">
              {#if viewType === 'posterior'}
                {#if results.baselineRanges.leftKneeValgus}
                <div class="metric-card compact">
                  <h5>🦵 Valgismo Ginocchio SX</h5>
                <div class="baseline-stats">
                  <div class="stat-row">
                    <span class="label">Media:</span>
                    <span class="value">{formatVal(results.baselineRanges.leftKneeValgus.mean)}°</span>
                  </div>
                  <div class="stat-row">
                    <span class="label">± StdDev:</span>
                    <span class="value">{formatVal(results.baselineRanges.leftKneeValgus.std)}°</span>
                  </div>
                  <div class="stat-row muted">
                    <span class="label">Range:</span>
                    <span class="value">{formatVal(results.baselineRanges.leftKneeValgus.min)} - {formatVal(results.baselineRanges.leftKneeValgus.max)}°</span>
                  </div>
                </div>
              </div>
              {/if}
              
              {#if results.baselineRanges.rightKneeValgus}
              <div class="metric-card compact">
                <h5>🦵 Valgismo Ginocchio DX</h5>
                <div class="baseline-stats">
                  <div class="stat-row">
                    <span class="label">Media:</span>
                    <span class="value">{formatVal(results.baselineRanges.rightKneeValgus.mean)}°</span>
                  </div>
                  <div class="stat-row">
                    <span class="label">± StdDev:</span>
                    <span class="value">{formatVal(results.baselineRanges.rightKneeValgus.std)}°</span>
                  </div>
                  <div class="stat-row muted">
                    <span class="label">Range:</span>
                    <span class="value">{formatVal(results.baselineRanges.rightKneeValgus.min)} - {formatVal(results.baselineRanges.rightKneeValgus.max)}°</span>
                  </div>
                </div>
              </div>
              {/if}
              
              {#if results.baselineRanges.kneeValgusSymmetry}
              <div class="metric-card compact symmetry-card">
                <h5>⚖️ Simmetria Knee Valgus</h5>
                <div class="baseline-stats">
                  <div class="stat-row">
                    <span class="label">Media:</span>
                    <span class="value">{formatVal(results.baselineRanges.kneeValgusSymmetry.mean, 1)}%</span>
                  </div>
                  <div class="stat-row">
                    <span class="label">± StdDev:</span>
                    <span class="value">{formatVal(results.baselineRanges.kneeValgusSymmetry.std, 1)}%</span>
                  </div>
                  <div class="stat-row muted">
                    <span class="label">Range:</span>
                    <span class="value">{formatVal(results.baselineRanges.kneeValgusSymmetry.min, 1)} - {formatVal(results.baselineRanges.kneeValgusSymmetry.max, 1)}%</span>
                  </div>
                </div>
              </div>
              {/if}
              
              {#if results.baselineRanges.pelvicDrop}
              <div class="metric-card compact">
                <h5>⚖️ Caduta Pelvica</h5>
                <div class="baseline-stats">
                  <div class="stat-row">
                    <span class="label">Media:</span>
                    <span class="value">{formatVal(results.baselineRanges.pelvicDrop.mean)}°</span>
                  </div>
                  <div class="stat-row">
                    <span class="label">± StdDev:</span>
                    <span class="value">{formatVal(results.baselineRanges.pelvicDrop.std)}°</span>
                  </div>
                  <div class="stat-row muted">
                    <span class="label">Range:</span>
                    <span class="value">{formatVal(results.baselineRanges.pelvicDrop.min)} - {formatVal(results.baselineRanges.pelvicDrop.max)}°</span>
                  </div>
                </div>
              </div>
              {/if}
              
                {#if results.baselineRanges.cadence}
                <div class="metric-card compact">
                  <h5>🏃 Cadenza</h5>
                  <div class="baseline-stats">
                    <div class="stat-row">
                      <span class="label">Media:</span>
                      <span class="value">{formatVal(results.baselineRanges.cadence.mean, 0)} spm</span>
                    </div>
                    <div class="stat-row">
                      <span class="label">± StdDev:</span>
                      <span class="value">{formatVal(results.baselineRanges.cadence.std, 1)} spm</span>
                    </div>
                    <div class="stat-row muted">
                      <span class="label">Range:</span>
                      <span class="value">{formatVal(results.baselineRanges.cadence.min, 0)} - {formatVal(results.baselineRanges.cadence.max, 0)} spm</span>
                    </div>
                  </div>
                </div>
                {/if}
              {:else}
                <!-- Vista Laterale -->
                {#if results.baselineRanges.overstriding}
                <div class="metric-card compact">
                  <h5>👣 Overstriding</h5>
                  <div class="baseline-stats">
                    <div class="stat-row">
                      <span class="label">Media:</span>
                      <span class="value">{formatVal(results.baselineRanges.overstriding.mean, 3)} {results.baselineRanges.overstriding.unit}</span>
                    </div>
                    <div class="stat-row">
                      <span class="label">± StdDev:</span>
                      <span class="value">{formatVal(results.baselineRanges.overstriding.std, 3)} {results.baselineRanges.overstriding.unit}</span>
                    </div>
                    <div class="stat-row muted">
                      <span class="label">Range:</span>
                      <span class="value">{formatVal(results.baselineRanges.overstriding.min, 3)} - {formatVal(results.baselineRanges.overstriding.max, 3)} {results.baselineRanges.overstriding.unit}</span>
                    </div>
                  </div>
                </div>
                {/if}
                
                {#if results.baselineRanges.kneeFlexionIC}
                <div class="metric-card compact">
                  <h5>🦵 Flessione Ginocchio @ IC</h5>
                  <div class="baseline-stats">
                    <div class="stat-row">
                      <span class="label">Media:</span>
                      <span class="value">{formatVal(results.baselineRanges.kneeFlexionIC.mean)}°</span>
                    </div>
                    <div class="stat-row">
                      <span class="label">± StdDev:</span>
                      <span class="value">{formatVal(results.baselineRanges.kneeFlexionIC.std)}°</span>
                    </div>
                    <div class="stat-row muted">
                      <span class="label">Range:</span>
                      <span class="value">{formatVal(results.baselineRanges.kneeFlexionIC.min)} - {formatVal(results.baselineRanges.kneeFlexionIC.max)}°</span>
                    </div>
                  </div>
                </div>
                {/if}
                
                {#if results.baselineRanges.trunkLean}
                <div class="metric-card compact">
                  <h5>🧍 Trunk Lean</h5>
                  <div class="baseline-stats">
                    <div class="stat-row">
                      <span class="label">Media:</span>
                      <span class="value">{formatVal(results.baselineRanges.trunkLean.mean)}°</span>
                    </div>
                    <div class="stat-row">
                      <span class="label">± StdDev:</span>
                      <span class="value">{formatVal(results.baselineRanges.trunkLean.std)}°</span>
                    </div>
                    <div class="stat-row muted">
                      <span class="label">Range:</span>
                      <span class="value">{formatVal(results.baselineRanges.trunkLean.min)} - {formatVal(results.baselineRanges.trunkLean.max)}°</span>
                    </div>
                  </div>
                </div>
                {/if}
                
                {#if results.baselineRanges.groundContactTime}
                <div class="metric-card compact">
                  <h5>⏱️ Ground Contact Time</h5>
                  <div class="baseline-stats">
                    <div class="stat-row">
                      <span class="label">Media:</span>
                      <span class="value">{formatVal(results.baselineRanges.groundContactTime.mean, 3)} {results.baselineRanges.groundContactTime.unit}</span>
                    </div>
                    <div class="stat-row">
                      <span class="label">± StdDev:</span>
                      <span class="value">{formatVal(results.baselineRanges.groundContactTime.std, 3)} {results.baselineRanges.groundContactTime.unit}</span>
                    </div>
                    <div class="stat-row muted">
                      <span class="label">Range:</span>
                      <span class="value">{formatVal(results.baselineRanges.groundContactTime.min, 3)} - {formatVal(results.baselineRanges.groundContactTime.max, 3)} {results.baselineRanges.groundContactTime.unit}</span>
                    </div>
                  </div>
                </div>
                {/if}
              {/if}
            </div>
          </div>
        {/if}
      </div>
      
    {:else}
      <!-- ANALISI VIDEO -->
      <div class="result-card" style="border-left: 3px solid {results.anomaly_color}">
        <div class="score-compact">
          <div>
            <div class="score-label">Stato Generale</div>
            <div class="score-value" style="color: {results.anomaly_color}">
              {results.anomaly_level}
            </div>
            <div class="z-score-label">Max Z-Score: {formatVal(results.anomaly_score, 2)}</div>
          </div>
          <div class="level-badge" style="background: {results.anomaly_color}">
            {getLevelEmoji(results.anomaly_level)} {results.anomaly_level}
          </div>
        </div>
        
        <div class="interpretation compact">
          {#if results.anomaly_level === 'Ottimale'}
            <p>✓ Eccellente! Parametri biomeccanici in linea con la tua baseline.</p>
          {:else if results.anomaly_level === 'Attenzione'}
            <p>⚠ Alcune metriche mostrano deviazioni moderate dalla baseline.</p>
          {:else if results.anomaly_level === 'Critico'}
            <p>🚨 Deviazioni significative rilevate. Consulta un professionista.</p>
          {:else}
            <p>📊 Livello: {results.anomaly_level || 'N/A'}</p>
          {/if}
        </div>
        
        <!-- Ghost Vision Toggle -->
        {#if ghostVisionAvailable}
        <div class="ghost-vision-section">
          <div class="ghost-vision-header">
            <div class="ghost-vision-info">
              <h5>👻 Ghost Vision</h5>
              <p>Sovrapponi la silhouette della baseline perfetta al tuo video</p>
            </div>
            <label class="toggle-switch">
              <input 
                type="checkbox" 
                checked={ghostVisionEnabled}
                on:change={toggleGhostVision}
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
          {#if ghostVisionEnabled}
          <div class="ghost-vision-active">
            <span class="ghost-indicator">👻 Overlay attivo</span>
          </div>
          {/if}
        </div>
        {/if}
        
        {#if results.metrics}
          <div class="metrics-section">
            <h4>📊 Confronto con Baseline ({viewType === 'posterior' ? 'Vista Posteriore' : 'Vista Laterale'})</h4>
            
            <div class="metrics-grid">
              {#if viewType === 'posterior'}
                <!-- Vista Posteriore Metrics -->
                <!-- Valgismo Ginocchio SX -->
                {#if results.metrics.left_knee_valgus}
              <div class="metric-card analysis" style="border-left: 3px solid {results.metrics.left_knee_valgus.color}">
                <div class="metric-header">
                  <h5>🦵 Valgismo Ginocchio SX</h5>
                  <span class="level-badge-small" style="background: {results.metrics.left_knee_valgus.color}">
                    {results.metrics.left_knee_valgus.level}
                  </span>
                </div>
                <div class="metric-comparison">
                  <div class="comp-row">
                    <span class="label">Tuo valore:</span>
                    <span class="value current">{formatVal(results.metrics.left_knee_valgus.value)}°</span>
                  </div>
                  <div class="comp-row">
                    <span class="label">Baseline:</span>
                    <span class="value baseline">{formatVal(results.metrics.left_knee_valgus.baseline_mean)} ± {formatVal(results.metrics.left_knee_valgus.baseline_std)}°</span>
                  </div>
                  <div class="comp-row">
                    <span class="label">Z-Score:</span>
                    <span class="value z-score" style="color: {results.metrics.left_knee_valgus.color}">{formatVal(results.metrics.left_knee_valgus.z_score, 2)}</span>
                  </div>
                </div>
              </div>
              {/if}
              
              <!-- Valgismo Ginocchio DX -->
              {#if results.metrics.right_knee_valgus}
              <div class="metric-card analysis" style="border-left: 3px solid {results.metrics.right_knee_valgus.color}">
                <div class="metric-header">
                  <h5>🦵 Valgismo Ginocchio DX</h5>
                  <span class="level-badge-small" style="background: {results.metrics.right_knee_valgus.color}">
                    {results.metrics.right_knee_valgus.level}
                  </span>
                </div>
                <div class="metric-comparison">
                  <div class="comp-row">
                    <span class="label">Tuo valore:</span>
                    <span class="value current">{formatVal(results.metrics.right_knee_valgus.value)}°</span>
                  </div>
                  <div class="comp-row">
                    <span class="label">Baseline:</span>
                    <span class="value baseline">{formatVal(results.metrics.right_knee_valgus.baseline_mean)} ± {formatVal(results.metrics.right_knee_valgus.baseline_std)}°</span>
                  </div>
                  <div class="comp-row">
                    <span class="label">Z-Score:</span>
                    <span class="value z-score" style="color: {results.metrics.right_knee_valgus.color}">{formatVal(results.metrics.right_knee_valgus.z_score, 2)}</span>
                  </div>
                </div>
              </div>
              {/if}
              
              <!-- Simmetria Knee Valgus -->
              {#if results.metrics.knee_valgus_symmetry}
              <div class="metric-card analysis symmetry-card" style="border-left: 3px solid {results.metrics.knee_valgus_symmetry.color}">
                <div class="metric-header">
                  <h5>⚖️ Simmetria Knee Valgus</h5>
                  <span class="level-badge-small" style="background: {results.metrics.knee_valgus_symmetry.color}">
                    {results.metrics.knee_valgus_symmetry.level}
                  </span>
                </div>
                <div class="symmetry-content">
                  <div class="symmetry-value">
                    <span class="symmetry-percentage">{formatVal(results.metrics.knee_valgus_symmetry.value, 1)}%</span>
                    <span class="symmetry-label">Indice di Simmetria (LSI)</span>
                  </div>
                  <div class="symmetry-progress-bar">
                    <div 
                      class="symmetry-progress-fill" 
                      style="width: {Math.min(100, Math.max(0, results.metrics.knee_valgus_symmetry.value))}%; background: {results.metrics.knee_valgus_symmetry.color}"
                    ></div>
                  </div>
                  <div class="metric-comparison">
                    <div class="comp-row">
                      <span class="label">Baseline:</span>
                      <span class="value baseline">{formatVal(results.metrics.knee_valgus_symmetry.baseline_mean, 1)} ± {formatVal(results.metrics.knee_valgus_symmetry.baseline_std, 1)}%</span>
                    </div>
                    <div class="comp-row">
                      <span class="label">Z-Score:</span>
                      <span class="value z-score" style="color: {results.metrics.knee_valgus_symmetry.color}">{formatVal(results.metrics.knee_valgus_symmetry.z_score, 2)}</span>
                    </div>
                  </div>
                </div>
              </div>
              {/if}
              
              <!-- Caduta Pelvica -->
              {#if results.metrics.pelvic_drop}
              <div class="metric-card analysis" style="border-left: 3px solid {results.metrics.pelvic_drop.color}">
                <div class="metric-header">
                  <h5>⚖️ Caduta Pelvica</h5>
                  <span class="level-badge-small" style="background: {results.metrics.pelvic_drop.color}">
                    {results.metrics.pelvic_drop.level}
                  </span>
                </div>
                <div class="metric-comparison">
                  <div class="comp-row">
                    <span class="label">Tuo valore:</span>
                    <span class="value current">{formatVal(results.metrics.pelvic_drop.value)}°</span>
                  </div>
                  <div class="comp-row">
                    <span class="label">Baseline:</span>
                    <span class="value baseline">{formatVal(results.metrics.pelvic_drop.baseline_mean)} ± {formatVal(results.metrics.pelvic_drop.baseline_std)}°</span>
                  </div>
                  <div class="comp-row">
                    <span class="label">Z-Score:</span>
                    <span class="value z-score" style="color: {results.metrics.pelvic_drop.color}">{formatVal(results.metrics.pelvic_drop.z_score, 2)}</span>
                  </div>
                </div>
              </div>
              {/if}
              
                <!-- Cadenza -->
                {#if results.metrics.cadence}
                <div class="metric-card analysis" style="border-left: 3px solid {results.metrics.cadence.color}">
                  <div class="metric-header">
                    <h5>🏃 Cadenza</h5>
                    <span class="level-badge-small" style="background: {results.metrics.cadence.color}">
                      {results.metrics.cadence.level}
                    </span>
                  </div>
                  <div class="metric-comparison">
                    <div class="comp-row">
                      <span class="label">Tuo valore:</span>
                      <span class="value current">{formatVal(results.metrics.cadence.value, 0)} spm</span>
                    </div>
                    <div class="comp-row">
                      <span class="label">Baseline:</span>
                      <span class="value baseline">{formatVal(results.metrics.cadence.baseline_mean, 0)} ± {formatVal(results.metrics.cadence.baseline_std, 1)} spm</span>
                    </div>
                    <div class="comp-row">
                      <span class="label">Z-Score:</span>
                      <span class="value z-score" style="color: {results.metrics.cadence.color}">{formatVal(results.metrics.cadence.z_score, 2)}</span>
                    </div>
                  </div>
                </div>
                {/if}
              {:else}
                <!-- Vista Laterale Metrics -->
                <!-- Overstriding -->
                {#if results.metrics.overstriding}
                <div class="metric-card analysis" style="border-left: 3px solid {results.metrics.overstriding.color}">
                  <div class="metric-header">
                    <h5>👣 Overstriding</h5>
                    <span class="level-badge-small" style="background: {results.metrics.overstriding.color}">
                      {results.metrics.overstriding.level}
                    </span>
                  </div>
                  <div class="metric-comparison">
                    <div class="comp-row">
                      <span class="label">Tuo valore:</span>
                      <span class="value current">{formatVal(results.metrics.overstriding.value, 3)} {results.metrics.overstriding.unit}</span>
                    </div>
                    <div class="comp-row">
                      <span class="label">Baseline:</span>
                      <span class="value baseline">{formatVal(results.metrics.overstriding.baseline_mean, 3)} ± {formatVal(results.metrics.overstriding.baseline_std, 3)} {results.metrics.overstriding.unit}</span>
                    </div>
                    <div class="comp-row">
                      <span class="label">Z-Score:</span>
                      <span class="value z-score" style="color: {results.metrics.overstriding.color}">{formatVal(results.metrics.overstriding.z_score, 2)}</span>
                    </div>
                  </div>
                </div>
                {/if}
                
                <!-- Knee Flexion IC -->
                {#if results.metrics.knee_flexion_ic}
                <div class="metric-card analysis" style="border-left: 3px solid {results.metrics.knee_flexion_ic.color}">
                  <div class="metric-header">
                    <h5>🦵 Flessione Ginocchio @ IC</h5>
                    <span class="level-badge-small" style="background: {results.metrics.knee_flexion_ic.color}">
                      {results.metrics.knee_flexion_ic.level}
                    </span>
                  </div>
                  <div class="metric-comparison">
                    <div class="comp-row">
                      <span class="label">Tuo valore:</span>
                      <span class="value current">{formatVal(results.metrics.knee_flexion_ic.value)}°</span>
                    </div>
                    <div class="comp-row">
                      <span class="label">Baseline:</span>
                      <span class="value baseline">{formatVal(results.metrics.knee_flexion_ic.baseline_mean)} ± {formatVal(results.metrics.knee_flexion_ic.baseline_std)}°</span>
                    </div>
                    <div class="comp-row">
                      <span class="label">Z-Score:</span>
                      <span class="value z-score" style="color: {results.metrics.knee_flexion_ic.color}">{formatVal(results.metrics.knee_flexion_ic.z_score, 2)}</span>
                    </div>
                  </div>
                </div>
                {/if}
                
                <!-- Trunk Lean -->
                {#if results.metrics.trunk_lean}
                <div class="metric-card analysis" style="border-left: 3px solid {results.metrics.trunk_lean.color}">
                  <div class="metric-header">
                    <h5>🧍 Trunk Lean</h5>
                    <span class="level-badge-small" style="background: {results.metrics.trunk_lean.color}">
                      {results.metrics.trunk_lean.level}
                    </span>
                  </div>
                  <div class="metric-comparison">
                    <div class="comp-row">
                      <span class="label">Tuo valore:</span>
                      <span class="value current">{formatVal(results.metrics.trunk_lean.value)}°</span>
                    </div>
                    <div class="comp-row">
                      <span class="label">Baseline:</span>
                      <span class="value baseline">{formatVal(results.metrics.trunk_lean.baseline_mean)} ± {formatVal(results.metrics.trunk_lean.baseline_std)}°</span>
                    </div>
                    <div class="comp-row">
                      <span class="label">Z-Score:</span>
                      <span class="value z-score" style="color: {results.metrics.trunk_lean.color}">{formatVal(results.metrics.trunk_lean.z_score, 2)}</span>
                    </div>
                  </div>
                </div>
                {/if}
                
                <!-- Ground Contact Time -->
                {#if results.metrics.ground_contact_time}
                <div class="metric-card analysis" style="border-left: 3px solid {results.metrics.ground_contact_time.color}">
                  <div class="metric-header">
                    <h5>⏱️ Ground Contact Time</h5>
                    <span class="level-badge-small" style="background: {results.metrics.ground_contact_time.color}">
                      {results.metrics.ground_contact_time.level}
                    </span>
                  </div>
                  <div class="metric-comparison">
                    <div class="comp-row">
                      <span class="label">Tuo valore:</span>
                      <span class="value current">{formatVal(results.metrics.ground_contact_time.value, 3)} {results.metrics.ground_contact_time.unit}</span>
                    </div>
                    <div class="comp-row">
                      <span class="label">Baseline:</span>
                      <span class="value baseline">{formatVal(results.metrics.ground_contact_time.baseline_mean, 3)} ± {formatVal(results.metrics.ground_contact_time.baseline_std, 3)} {results.metrics.ground_contact_time.unit}</span>
                    </div>
                    <div class="comp-row">
                      <span class="label">Z-Score:</span>
                      <span class="value z-score" style="color: {results.metrics.ground_contact_time.color}">{formatVal(results.metrics.ground_contact_time.z_score, 2)}</span>
                    </div>
                  </div>
                </div>
                {/if}
              {/if}
            </div>
          </div>
        {/if}
        
        {#if results.charts}
          <div class="charts-section">
            <h4>📈 Analisi Temporale</h4>
            <p class="chart-desc">Variazione delle metriche nel tempo durante la corsa</p>
            
            {#if viewType === 'posterior'}
              <!-- Charts Vista Posteriore -->
              {#if results.charts.left_knee_valgus}
            <div class="chart-wrapper">
              <h5>Valgismo Ginocchio Sinistro</h5>
              <AnalysisChart 
                data={results.charts.left_knee_valgus} 
                labels={results.charts.timeline} 
                title="Knee Valgus Left"
                color="#3b82f6"
                baselineMean={results.metrics?.left_knee_valgus?.baseline_mean}
                baselineStd={results.metrics?.left_knee_valgus?.baseline_std}
                onClick={() => openChartModal(
                  "Valgismo Ginocchio Sinistro",
                  results.charts.left_knee_valgus,
                  results.charts.timeline,
                  "#3b82f6",
                  results.metrics?.left_knee_valgus?.baseline_mean,
                  results.metrics?.left_knee_valgus?.baseline_std
                )}
              />
            </div>
            {/if}
            
            {#if results.charts.right_knee_valgus}
            <div class="chart-wrapper">
              <h5>Valgismo Ginocchio Destro</h5>
              <AnalysisChart 
                data={results.charts.right_knee_valgus} 
                labels={results.charts.timeline} 
                title="Knee Valgus Right"
                color="#10b981"
                baselineMean={results.metrics?.right_knee_valgus?.baseline_mean}
                baselineStd={results.metrics?.right_knee_valgus?.baseline_std}
                onClick={() => openChartModal(
                  "Valgismo Ginocchio Destro",
                  results.charts.right_knee_valgus,
                  results.charts.timeline,
                  "#10b981",
                  results.metrics?.right_knee_valgus?.baseline_mean,
                  results.metrics?.right_knee_valgus?.baseline_std
                )}
              />
            </div>
            {/if}
            
            {#if results.charts.knee_valgus_symmetry}
            <div class="chart-wrapper">
              <h5>Simmetria Knee Valgus</h5>
              <AnalysisChart 
                data={results.charts.knee_valgus_symmetry} 
                labels={results.charts.timeline} 
                title="Knee Valgus Symmetry"
                color="#8b5cf6"
                baselineMean={results.metrics?.knee_valgus_symmetry?.baseline_mean}
                baselineStd={results.metrics?.knee_valgus_symmetry?.baseline_std}
                yAxisMin={0}
                yAxisMax={100}
                beginAtZero={true}
                unit="%"
                onClick={() => openChartModal(
                  "Simmetria Knee Valgus",
                  results.charts.knee_valgus_symmetry,
                  results.charts.timeline,
                  "#8b5cf6",
                  results.metrics?.knee_valgus_symmetry?.baseline_mean,
                  results.metrics?.knee_valgus_symmetry?.baseline_std,
                  0,
                  100,
                  true,
                  "%"
                )}
              />
            </div>
            {/if}
            
            {#if results.charts.pelvic_drop}
            <div class="chart-wrapper">
              <h5>Caduta Pelvica</h5>
              <AnalysisChart 
                data={results.charts.pelvic_drop} 
                labels={results.charts.timeline} 
                title="Pelvic Drop"
                color="#f59e0b"
                baselineMean={results.metrics?.pelvic_drop?.baseline_mean}
                baselineStd={results.metrics?.pelvic_drop?.baseline_std}
                onClick={() => openChartModal(
                  "Caduta Pelvica",
                  results.charts.pelvic_drop,
                  results.charts.timeline,
                  "#f59e0b",
                  results.metrics?.pelvic_drop?.baseline_mean,
                  results.metrics?.pelvic_drop?.baseline_std
                )}
              />
            </div>
            {/if}
            
              {#if results.charts.cadence}
              <div class="chart-wrapper">
                <h5>Cadenza</h5>
                <AnalysisChart 
                  data={results.charts.cadence} 
                  labels={results.charts.timeline} 
                  title="Cadence"
                  color="#8b5cf6"
                  baselineMean={results.metrics?.cadence?.baseline_mean}
                  baselineStd={results.metrics?.cadence?.baseline_std}
                  onClick={() => openChartModal(
                    "Cadenza",
                    results.charts.cadence,
                    results.charts.timeline,
                    "#8b5cf6",
                    results.metrics?.cadence?.baseline_mean,
                    results.metrics?.cadence?.baseline_std
                  )}
                />
              </div>
              {/if}
            {:else}
              <!-- Charts Vista Laterale -->
              {#if results.charts.overstriding}
              <div class="chart-wrapper">
                <h5>Overstriding</h5>
                <AnalysisChart 
                  data={results.charts.overstriding} 
                  labels={results.charts.timeline} 
                  title="Overstriding"
                  color="#3b82f6"
                  baselineMean={results.metrics?.overstriding?.baseline_mean}
                  baselineStd={results.metrics?.overstriding?.baseline_std}
                  onClick={() => openChartModal(
                    "Overstriding",
                    results.charts.overstriding,
                    results.charts.timeline,
                    "#3b82f6",
                    results.metrics?.overstriding?.baseline_mean,
                    results.metrics?.overstriding?.baseline_std
                  )}
                />
              </div>
              {/if}
              
              {#if results.charts.knee_flexion_ic}
              <div class="chart-wrapper">
                <h5>Flessione Ginocchio @ IC</h5>
                <AnalysisChart 
                  data={results.charts.knee_flexion_ic} 
                  labels={results.charts.timeline} 
                  title="Knee Flexion IC"
                  color="#10b981"
                  baselineMean={results.metrics?.knee_flexion_ic?.baseline_mean}
                  baselineStd={results.metrics?.knee_flexion_ic?.baseline_std}
                  beginAtZero={false}
                  unit="°"
                  onClick={() => openChartModal(
                    "Flessione Ginocchio @ IC",
                    results.charts.knee_flexion_ic,
                    results.charts.timeline,
                    "#10b981",
                    results.metrics?.knee_flexion_ic?.baseline_mean,
                    results.metrics?.knee_flexion_ic?.baseline_std,
                    null,
                    null,
                    false,
                    "°"
                  )}
                />
              </div>
              {/if}
              
              {#if results.charts.trunk_lean}
              <div class="chart-wrapper">
                <h5>Trunk Lean</h5>
                <AnalysisChart 
                  data={results.charts.trunk_lean} 
                  labels={results.charts.timeline} 
                  title="Trunk Lean"
                  color="#f59e0b"
                  baselineMean={results.metrics?.trunk_lean?.baseline_mean}
                  baselineStd={results.metrics?.trunk_lean?.baseline_std}
                  beginAtZero={false}
                  yAxisMin={-90}
                  yAxisMax={90}
                  unit="°"
                  onClick={() => openChartModal(
                    "Trunk Lean",
                    results.charts.trunk_lean,
                    results.charts.timeline,
                    "#f59e0b",
                    results.metrics?.trunk_lean?.baseline_mean,
                    results.metrics?.trunk_lean?.baseline_std,
                    -90,
                    90,
                    false,
                    "°"
                  )}
                />
              </div>
              {/if}
              
              {#if results.charts.ground_contact_time}
              <div class="chart-wrapper">
                <h5>Ground Contact Time</h5>
                <AnalysisChart 
                  data={results.charts.ground_contact_time} 
                  labels={results.charts.timeline} 
                  title="Ground Contact Time"
                  color="#8b5cf6"
                  baselineMean={results.metrics?.ground_contact_time?.baseline_mean}
                  baselineStd={results.metrics?.ground_contact_time?.baseline_std}
                  beginAtZero={true}
                  yAxisMin={0}
                  yAxisMax={null}
                  unit="s"
                  onClick={() => openChartModal(
                    "Ground Contact Time",
                    results.charts.ground_contact_time,
                    results.charts.timeline,
                    "#8b5cf6",
                    results.metrics?.ground_contact_time?.baseline_mean,
                    results.metrics?.ground_contact_time?.baseline_std,
                    0,
                    null,
                    true,
                    "s"
                  )}
                />
              </div>
              {/if}
            {/if}
          </div>
        {/if}
      </div>
    {/if}
    
    <!-- Bottoni azioni -->
    <div class="action-buttons">
      {#if mainFlow === 'baseline' || results.baselineCreated}
        <button 
          class="btn-save" 
          on:click={saveBaseline}
          disabled={true}
          title="Funzionalità non ancora disponibile"
        >
          💾 Salva Baseline
        </button>
      {:else}
        <button 
          class="btn-save" 
          on:click={saveAnalysis}
          disabled={true}
          title="Funzionalità non ancora disponibile"
        >
          💾 Salva Analisi
        </button>
      {/if}
      
      <button class="btn-restart" on:click={restartAnalysis}>
        🔄 Nuova Analisi
      </button>
    </div>
    
  {:else}
    <div class="no-results">
      <p>Nessun risultato</p>
    </div>
  {/if}

  <!-- Modal per grafico ingrandito -->
  {#if expandedChart}
    <div 
      class="chart-modal-overlay" 
      role="dialog"
      aria-modal="true"
      aria-labelledby="chart-modal-title"
      on:click={closeChartModal} 
      on:keydown={(e) => e.key === 'Escape' && closeChartModal()}
    >
      <div class="chart-modal-content" role="none" on:click|stopPropagation>
        <div class="chart-modal-header">
          <h3 id="chart-modal-title">{expandedChart.title}</h3>
          <button class="chart-modal-close" on:click={closeChartModal} aria-label="Chiudi modal">
            ✕
          </button>
        </div>
        <div class="chart-modal-body">
          <AnalysisChart 
            data={expandedChart.data} 
            labels={expandedChart.labels} 
            title={expandedChart.title}
            color={expandedChart.color}
            baselineMean={expandedChart.baselineMean}
            baselineStd={expandedChart.baselineStd}
          />
        </div>
      </div>
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
    max-width: 100%;
    overflow-wrap: break-word;
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
    flex-wrap: wrap;
  }
  
  .score-label {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 0.25rem;
  }
  
  .score-value {
    font-size: 1.8rem;
    font-weight: 700;
    line-height: 1;
  }
  
  .z-score-label {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.6);
    margin-top: 0.25rem;
  }
  
  .level-badge {
    padding: 0.5rem 1rem;
    border-radius: 16px;
    font-weight: 600;
    color: white;
    font-size: 0.85rem;
    white-space: nowrap;
  }
  
  .level-badge-small {
    padding: 0.25rem 0.5rem;
    border-radius: 8px;
    font-weight: 600;
    color: white;
    font-size: 0.7rem;
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
  
  .biomechanics-section, .metrics-section {
    margin-top: 1rem;
  }
  
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  
  .metric-card {
    background: rgba(0, 0, 0, 0.3);
    border-radius: 8px;
    padding: 0.6rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    min-width: 0;
  }
  
  .metric-card.compact {
    padding: 0.5rem;
  }
  
  .metric-card.analysis {
    padding: 0.75rem;
  }
  
  .metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }
  
  .baseline-stats {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }
  
  .stat-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 0.8rem;
  }
  
  .stat-row.muted {
    opacity: 0.7;
    font-size: 0.75rem;
  }
  
  .stat-row .label {
    color: rgba(255, 255, 255, 0.7);
  }
  
  .stat-row .value {
    color: var(--accent-primary);
    font-weight: 600;
  }
  
  .metric-comparison {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }
  
  .comp-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 0.8rem;
  }
  
  .comp-row .label {
    color: rgba(255, 255, 255, 0.7);
  }
  
  .comp-row .value {
    font-weight: 600;
  }
  
  .comp-row .value.current {
    color: #3b82f6;
  }
  
  .comp-row .value.baseline {
    color: rgba(255, 255, 255, 0.8);
  }
  
  .comp-row .value.z-score {
    font-weight: 700;
  }
  
  .symmetry-card {
    grid-column: 1 / -1; /* Occupa tutta la larghezza della griglia */
  }
  
  .symmetry-content {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .symmetry-value {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
  }
  
  .symmetry-percentage {
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent-primary);
    line-height: 1;
  }
  
  .symmetry-label {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.7);
  }
  
  .symmetry-progress-bar {
    width: 100%;
    height: 12px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    overflow: hidden;
    position: relative;
  }
  
  .symmetry-progress-fill {
    height: 100%;
    border-radius: 6px;
    transition: width 0.3s ease;
    box-shadow: 0 0 8px rgba(0, 0, 0, 0.3);
  }
  
  .action-buttons {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-top: auto;
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
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0.5rem;
  }
  
  .btn-restart:hover {
    background: #2980b9;
    transform: translateY(-1px);
  }
  
  .btn-save {
    width: 100%;
    background: #10b981;
    color: white;
    border: none;
    padding: 0.75rem;
    font-size: 0.9rem;
    font-weight: 600;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0.5rem;
  }
  
  .btn-save:hover:not(:disabled) {
    background: #059669;
    transform: translateY(-1px);
  }
  
  .btn-save:disabled {
    background: #6b7280;
    cursor: not-allowed;
    opacity: 0.6;
  }
  
  .no-results {
    text-align: center;
    padding: 1.5rem;
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.85rem;
  }
  
  .charts-section {
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .chart-wrapper {
    margin-bottom: 2rem;
  }
  
  .chart-wrapper h5 {
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
    color: var(--text-light);
  }
  
  .chart-desc {
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-bottom: 1rem;
    line-height: 1.4;
  }
  
  @media (max-width: 360px) {
    .metrics-grid {
      grid-template-columns: 1fr;
    }
  }
  
  /* Ghost Vision Toggle Styles */
  .ghost-vision-section {
    margin: 1rem 0;
    padding: 1rem;
    background: rgba(0, 255, 255, 0.05);
    border: 1px solid rgba(0, 255, 255, 0.2);
    border-radius: 8px;
  }
  
  .ghost-vision-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
  }
  
  .ghost-vision-info h5 {
    font-size: 0.95rem;
    margin: 0 0 0.25rem 0;
    color: var(--text-light);
    font-weight: 600;
  }
  
  .ghost-vision-info p {
    font-size: 0.8rem;
    color: var(--text-muted);
    margin: 0;
    line-height: 1.4;
  }
  
  /* Toggle Switch Styles */
  .toggle-switch {
    position: relative;
    display: inline-block;
    width: 52px;
    height: 28px;
    flex-shrink: 0;
  }
  
  .toggle-switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  
  .toggle-slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(255, 255, 255, 0.2);
    transition: 0.3s;
    border-radius: 28px;
  }
  
  .toggle-slider:before {
    position: absolute;
    content: "";
    height: 20px;
    width: 20px;
    left: 4px;
    bottom: 4px;
    background-color: white;
    transition: 0.3s;
    border-radius: 50%;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }
  
  .toggle-switch input:checked + .toggle-slider {
    background-color: #00ffff;
  }
  
  .toggle-switch input:checked + .toggle-slider:before {
    transform: translateX(24px);
  }
  
  .toggle-slider:hover {
    background-color: rgba(255, 255, 255, 0.3);
  }
  
  .toggle-switch input:checked + .toggle-slider:hover {
    background-color: #00e6e6;
  }
  
  .ghost-vision-active {
    margin-top: 0.75rem;
    padding: 0.5rem;
    background: rgba(0, 255, 255, 0.1);
    border-radius: 6px;
    text-align: center;
  }
  
  .ghost-indicator {
    font-size: 0.85rem;
    color: #00ffff;
    font-weight: 600;
    animation: ghostPulse 2s ease-in-out infinite;
  }
  
  @keyframes ghostPulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.6;
    }
  }

  /* Modal per grafico ingrandito */
  .chart-modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.85);
    backdrop-filter: blur(8px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 2rem;
    animation: fadeIn 0.3s ease;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  .chart-modal-content {
    background: rgba(15, 23, 42, 0.95);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    width: 100%;
    max-width: 90vw;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
    animation: slideUp 0.3s ease;
  }

  @keyframes slideUp {
    from {
      transform: translateY(20px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }

  .chart-modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .chart-modal-header h3 {
    margin: 0;
    font-size: 1.5rem;
    color: var(--text-light);
  }

  .chart-modal-close {
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: var(--text-muted);
    width: 36px;
    height: 36px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 1.2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
  }

  .chart-modal-close:hover {
    background: rgba(255, 255, 255, 0.2);
    color: white;
  }

  .chart-modal-body {
    padding: 2rem;
    flex: 1;
    overflow: auto;
  }

  .chart-modal-body :global(.chart-container) {
    height: 60vh;
    min-height: 400px;
  }

  @media (max-width: 768px) {
    .chart-modal-overlay {
      padding: 1rem;
    }

    .chart-modal-content {
      max-width: 100%;
      max-height: 100%;
      border-radius: 12px;
    }

    .chart-modal-header {
      padding: 1rem;
    }

    .chart-modal-header h3 {
      font-size: 1.2rem;
    }

    .chart-modal-body {
      padding: 1rem;
    }

    .chart-modal-body :global(.chart-container) {
      height: 50vh;
      min-height: 300px;
    }
  }
</style>
