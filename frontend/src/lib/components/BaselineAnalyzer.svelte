<script>
  import { onMount, onDestroy } from 'svelte';
  import { analysisStore } from '../stores/analysisStore.js';
  
  export let videoUrls = [];
  export let videoFiles = []; // File objects per invio al backend
  export let onAnalysisComplete = null;
  
  let videoElement;
  let canvasElement;
  let canvasCtx;
  let pose;
  let animationFrame;
  let isProcessing = false;
  
const LANDMARKS = {
  LEFT_SHOULDER: 11,
  RIGHT_SHOULDER: 12,
  LEFT_HIP: 23,
  RIGHT_HIP: 24,
  LEFT_KNEE: 25,
  RIGHT_KNEE: 26,
  LEFT_ANKLE: 27,
  RIGHT_ANKLE: 28,
  LEFT_HEEL: 29,
  RIGHT_HEEL: 30,
  LEFT_FOOT_INDEX: 31,
  RIGHT_FOOT_INDEX: 32
};

  // Dati raccolti durante l'analisi
  let allVideosData = []; // Array di array (uno per video)
  let currentVideoIndex = 0;
  let currentVideoFrames = [];
  let frameCount = 0;
  
  $: isAnalyzing = $analysisStore.isAnalyzing;
  $: progress = videoUrls.length > 0 ? ((currentVideoIndex / videoUrls.length) * 100).toFixed(0) : 0;
  
  onMount(async () => {
    if (typeof window !== 'undefined') {
      await initializeMediaPipe();
      window.addEventListener('resize', handleResize);
    }
  });
  
  // Auto-start analisi quando isAnalyzing diventa true
  $: if (isAnalyzing && videoElement && pose && !isProcessing && videoUrls.length > 0) {
    setTimeout(() => startBaselineAnalysis(), 300);
  }
  
  onDestroy(() => {
    cleanup();
  });
  
  async function initializeMediaPipe() {
    try {
      // Carica MediaPipe dinamicamente da CDN se non già disponibile
      if (typeof window.Pose === 'undefined') {
        await loadMediaPipeFromCDN();
      }
      
      // Attendi che MediaPipe sia disponibile
      await new Promise((resolve, reject) => {
        const maxAttempts = 50; // 5 secondi max
        let attempts = 0;
        
        const checkMediaPipe = () => {
          // Prova diversi possibili percorsi per Pose
          const Pose = window.Pose || 
                      window.mediapipe?.pose?.Pose || 
                      (window.mediapipe && window.mediapipe.pose && window.mediapipe.pose.default);
          
          if (Pose && typeof Pose === 'function') {
            window.Pose = Pose; // Salva per uso futuro
            resolve();
          } else if (attempts < maxAttempts) {
            attempts++;
            setTimeout(checkMediaPipe, 100);
          } else {
            reject(new Error('MediaPipe non caricato dopo 5 secondi'));
          }
        };
        
        checkMediaPipe();
      });
      
      // Usa MediaPipe da window (caricato da CDN)
      const Pose = window.Pose;
      
      // Carica drawing utils se non disponibili
      if (!window.drawConnectors || !window.drawLandmarks) {
        await loadDrawingUtilsFromCDN();
      }
      
      // Estrai POSE_CONNECTIONS da Pose se disponibile
      if (!window.POSE_CONNECTIONS && window.Pose && window.Pose.POSE_CONNECTIONS) {
        window.POSE_CONNECTIONS = window.Pose.POSE_CONNECTIONS;
      }
      
      const drawConnectors = window.drawConnectors;
      const drawLandmarks = window.drawLandmarks;
      const POSE_CONNECTIONS = window.POSE_CONNECTIONS;
      
      // Salva le funzioni di disegno globalmente per usarle dopo
      if (drawConnectors) window.drawConnectors = drawConnectors;
      if (drawLandmarks) window.drawLandmarks = drawLandmarks;
      if (POSE_CONNECTIONS) window.POSE_CONNECTIONS = POSE_CONNECTIONS;
      
      // Verifica che Pose sia disponibile
      if (!Pose || typeof Pose !== 'function') {
        throw new Error('Pose non è disponibile come costruttore');
      }
      
      // Inizializza Pose
      pose = new Pose({
        locateFile: (file) => {
          return `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`;
        }
      });
      
      pose.setOptions({
        modelComplexity: 1,
        smoothLandmarks: true,
        enableSegmentation: false,
        smoothSegmentation: false,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
      });
      
      pose.onResults(onPoseResults);
      
      console.log('✅ MediaPipe Pose inizializzato per Baseline');
    } catch (error) {
      console.error('❌ Errore inizializzazione MediaPipe:', error);
      analysisStore.setError('Errore nel caricamento di MediaPipe: ' + error.message);
    }
  }
  
  function loadMediaPipeFromCDN() {
    return new Promise((resolve, reject) => {
      // Verifica se già caricato
      if (document.querySelector('script[src*="@mediapipe/pose"]')) {
        resolve();
        return;
      }
      
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js';
      script.crossOrigin = 'anonymous';
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Errore nel caricamento di MediaPipe Pose'));
      document.head.appendChild(script);
    });
  }
  
  function loadDrawingUtilsFromCDN() {
    return new Promise((resolve, reject) => {
      // Verifica se già caricato
      if (document.querySelector('script[src*="@mediapipe/drawing_utils"]')) {
        resolve();
        return;
      }
      
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js';
      script.crossOrigin = 'anonymous';
      script.onload = () => {
        // Attendi che le funzioni siano disponibili
        setTimeout(() => {
          if (window.drawConnectors && window.drawLandmarks) {
            resolve();
          } else {
            // Prova a estrarre da window.mediapipe
            if (window.mediapipe?.drawing_utils) {
              window.drawConnectors = window.mediapipe.drawing_utils.drawConnectors;
              window.drawLandmarks = window.mediapipe.drawing_utils.drawLandmarks;
              window.POSE_CONNECTIONS = window.mediapipe.pose?.POSE_CONNECTIONS;
              resolve();
            } else {
              reject(new Error('Drawing utils non disponibili'));
            }
          }
        }, 100);
      };
      script.onerror = () => reject(new Error('Errore nel caricamento di Drawing Utils'));
      document.head.appendChild(script);
    });
  }
  
  function onPoseResults(results) {
    // Per la baseline, processiamo solo i dati senza disegnare
    if (results.poseLandmarks) {
      frameCount++;
      
      const metrics = calculateBiomechanicalMetrics(results.poseLandmarks);
      
      currentVideoFrames.push({
        frameNumber: frameCount,
        timestamp: videoElement?.currentTime || 0,
        landmarks: results.poseLandmarks,
        angles: metrics.angles,
        features: metrics.features
      });
    }
  }
  
  function calculateBiomechanicalMetrics(landmarks) {
    const leftHip = landmarks[LANDMARKS.LEFT_HIP];
    const rightHip = landmarks[LANDMARKS.RIGHT_HIP];
    const leftKnee = landmarks[LANDMARKS.LEFT_KNEE];
    const rightKnee = landmarks[LANDMARKS.RIGHT_KNEE];
    const leftAnkle = landmarks[LANDMARKS.LEFT_ANKLE];
    const rightAnkle = landmarks[LANDMARKS.RIGHT_ANKLE];
    const leftShoulder = landmarks[LANDMARKS.LEFT_SHOULDER];
    const rightShoulder = landmarks[LANDMARKS.RIGHT_SHOULDER];
    
    const leftKneeAngle = calculateAngle(leftHip, leftKnee, leftAnkle);
    const rightKneeAngle = calculateAngle(rightHip, rightKnee, rightAnkle);
    
    const cpdAngle = Math.atan2(
      rightHip.y - leftHip.y,
      Math.abs(rightHip.x - leftHip.x) + 1e-6
    ) * 180 / Math.PI;
    
    const shoulderMidpoint = {
      x: (leftShoulder.x + rightShoulder.x) / 2,
      y: (leftShoulder.y + rightShoulder.y) / 2
    };
    const hipMidpoint = {
      x: (leftHip.x + rightHip.x) / 2,
      y: (leftHip.y + rightHip.y) / 2
    };
    
    const trunkAngle = Math.atan2(
      shoulderMidpoint.x - hipMidpoint.x,
      shoulderMidpoint.y - hipMidpoint.y
    ) * 180 / Math.PI;
    
    const bos = Math.abs(rightAnkle.x - leftAnkle.x);
    
    const eversionLeft = calculateRearfootEversion(landmarks, 'left');
    const eversionRight = calculateRearfootEversion(landmarks, 'right');
    const eversionAvg = (eversionLeft + eversionRight) / 2;
    
    const leftFootHeight = Math.max(
      landmarks[LANDMARKS.LEFT_ANKLE].y,
      landmarks[LANDMARKS.LEFT_HEEL]?.y ?? landmarks[LANDMARKS.LEFT_ANKLE].y,
      landmarks[LANDMARKS.LEFT_FOOT_INDEX]?.y ?? landmarks[LANDMARKS.LEFT_ANKLE].y
    );
    const rightFootHeight = Math.max(
      landmarks[LANDMARKS.RIGHT_ANKLE].y,
      landmarks[LANDMARKS.RIGHT_HEEL]?.y ?? landmarks[LANDMARKS.RIGHT_ANKLE].y,
      landmarks[LANDMARKS.RIGHT_FOOT_INDEX]?.y ?? landmarks[LANDMARKS.RIGHT_ANKLE].y
    );
    
    return {
      angles: {
        leftKneeAngle,
        rightKneeAngle,
        pelvicDrop: Math.abs(leftHip.y - rightHip.y),
        trunkAngle
      },
      features: {
        cpd: cpdAngle,
        bos,
        eversion: eversionAvg,
        trunkLean: trunkAngle,
        leftFootHeight,
        rightFootHeight
      }
    };
  }
  
  function calculateAngle(a, b, c) {
    const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
    let angle = Math.abs(radians * 180 / Math.PI);
    
    if (angle > 180) {
      angle = 360 - angle;
    }
    
    return angle;
  }
  
  function calculateRearfootEversion(landmarks, side = 'left') {
    const ankle = landmarks[side === 'left' ? LANDMARKS.LEFT_ANKLE : LANDMARKS.RIGHT_ANKLE];
    const heel = landmarks[side === 'left' ? LANDMARKS.LEFT_HEEL : LANDMARKS.RIGHT_HEEL];
    const footIndex = landmarks[side === 'left' ? LANDMARKS.LEFT_FOOT_INDEX : LANDMARKS.RIGHT_FOOT_INDEX];
    
    if (!ankle || !heel || !footIndex) {
      return 0;
    }
    
    const vectorHeel = {
      x: heel.x - ankle.x,
      y: heel.y - ankle.y
    };
    const vectorFoot = {
      x: footIndex.x - ankle.x,
      y: footIndex.y - ankle.y
    };
    
    const heelMagnitude = Math.hypot(vectorHeel.x, vectorHeel.y);
    const footMagnitude = Math.hypot(vectorFoot.x, vectorFoot.y);
    
    if (heelMagnitude === 0 || footMagnitude === 0) {
      return 0;
    }
    
    const dotProduct = vectorHeel.x * vectorFoot.x + vectorHeel.y * vectorFoot.y;
    const cosAngle = Math.min(1, Math.max(-1, dotProduct / (heelMagnitude * footMagnitude)));
    let angle = Math.acos(cosAngle) * 180 / Math.PI;
    
    const cross = vectorHeel.x * vectorFoot.y - vectorHeel.y * vectorFoot.x;
    if (cross < 0) {
      angle = -angle;
    }
    
    return angle;
  }
  
  async function processFrame() {
    if (!videoElement || !pose || !isAnalyzing || videoElement.paused || videoElement.ended) {
      return;
    }
    
    try {
      await pose.send({ image: videoElement });
      animationFrame = requestAnimationFrame(processFrame);
    } catch (error) {
      console.error('Errore nel processamento del frame:', error);
    }
  }
  
  function handleVideoLoaded() {
    if (canvasElement && videoElement) {
      // Sincronizza le dimensioni del canvas con il video visualizzato
      const rect = videoElement.getBoundingClientRect();
      canvasElement.width = rect.width;
      canvasElement.height = rect.height;
      canvasCtx = canvasElement.getContext('2d');
      
      console.log(`📹 Video ${currentVideoIndex + 1}/5 caricato: ${videoElement.videoWidth}x${videoElement.videoHeight}, Display: ${rect.width}x${rect.height}`);
    }
  }
  
  // Ricalcola dimensioni canvas quando la finestra viene ridimensionata
  function handleResize() {
    if (canvasElement && videoElement) {
      const rect = videoElement.getBoundingClientRect();
      canvasElement.width = rect.width;
      canvasElement.height = rect.height;
    }
  }
  
  async function startBaselineAnalysis() {
    if (!videoElement || !pose || videoUrls.length !== 5) {
      analysisStore.setError('Sono richiesti esattamente 5 video per la baseline');
      return;
    }
    
    allVideosData = [];
    currentVideoIndex = 0;
    isProcessing = true;
    
    console.log('🎬 Avvio analisi baseline con 5 video');
    
    await processNextVideo();
  }
  
  async function processNextVideo() {
    if (currentVideoIndex >= videoUrls.length) {
      // Tutti i video processati
      await finishBaselineAnalysis();
      return;
    }
    
    // Reset per nuovo video
    currentVideoFrames = [];
    frameCount = 0;
    
    // Carica il video corrente
    videoElement.src = videoUrls[currentVideoIndex];
    videoElement.load();
    
    console.log(`📹 Processamento video ${currentVideoIndex + 1}/5...`);
  }
  
  function handleVideoEnded() {
    console.log(`✅ Video ${currentVideoIndex + 1}/5 completato`);
    
    // Salva i dati del video corrente
    allVideosData.push({
      videoIndex: currentVideoIndex,
      frames: currentVideoFrames,
      frameCount: currentVideoFrames.length,
      duration: videoElement?.duration || 0
    });
    
    // Passa al prossimo video
    currentVideoIndex++;
    
    if (currentVideoIndex < videoUrls.length) {
      processNextVideo();
    } else {
      finishBaselineAnalysis();
    }
  }
  
  async function finishBaselineAnalysis() {
    console.log('✅ Tutti i 5 video processati localmente (MediaPipe)');
    isProcessing = false;
    analysisStore.setAnalyzing(false);
    
    // NOTA: I calcoli baseline vengono ora fatti SOLO dal backend
    // Il frontend non calcola più nulla, solo invia i video al backend
    // e riceve i risultati già elaborati
    
    // Invia i video al backend per ottenere TUTTI i risultati (range, statistiche, thresholds, ecc.)
    await sendVideosToBackend();
    
    // I risultati vengono salvati nello store da sendVideosToBackend()
  }
  
  /**
   * Invia i video al backend per ottenere E_max e soglie dinamiche
   */
  async function sendVideosToBackend() {
    // Usa videoFiles se disponibili, altrimenti prova a recuperarli dallo store
    let filesToSend = videoFiles;
    
    if (!filesToSend || filesToSend.length === 0) {
      // Prova a recuperare i file dallo store
      const storeState = $analysisStore;
      if (storeState.baselineVideos && storeState.baselineVideos.length === 5) {
        filesToSend = storeState.baselineVideos;
      } else {
        console.warn('⚠️ File video non disponibili per invio al backend');
        return;
      }
    }
    
    if (filesToSend.length !== 5) {
      console.warn('⚠️ Numero di file video non corretto:', filesToSend.length);
      return;
    }
    
    // Imposta loading nello store per mostrare overlay in StepHolder
    analysisStore.setLoading(true);
    
    try {
      console.log('📤 Invio video al backend per calcolo E_max...');
      
      const formData = new FormData();
      filesToSend.forEach(file => {
        formData.append('videos', file);
      });
      
      // Aggiungi parametri di calibrazione se disponibili
      const storeState = $analysisStore;
      if (storeState.speed) {
        formData.append('speed', storeState.speed);
      }
      if (storeState.fps) {
        formData.append('fps', storeState.fps);
      }
      if (storeState.height) {
        formData.append('height', storeState.height);
      }
      if (storeState.mass) {
        formData.append('mass', storeState.mass);
      }
      
      const response = await fetch('http://localhost:5000/api/create_baseline', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'success' && data.details && data.details.thresholds) {
        // Valida i thresholds prima di salvarli
        const thresholds = data.details.thresholds;
        if (thresholds.e_max && thresholds.e_max > 0 && isFinite(thresholds.e_max)) {
          // Salva E_max e thresholds nello store
          analysisStore.setBaselineThresholds(thresholds);
          console.log('💾 E_max salvato dal backend:', thresholds.e_max);
          console.log('📊 Soglie dinamiche salvate:', {
            optimal: thresholds.optimal,
            good: thresholds.good,
            moderate: thresholds.moderate,
            attention: thresholds.attention,
            critical: thresholds.critical
          });
        } else {
          console.warn('⚠️ E_max non valido nei thresholds:', thresholds.e_max);
        }
      } else if (data.status === 'error') {
        console.error('❌ Backend ha restituito errore:', data.message);
        console.warn('⚠️ Il sistema continuerà a funzionare con soglie fisse');
      } else {
        console.warn('⚠️ Backend non ha restituito thresholds:', data);
      }
    } catch (error) {
      // Non bloccare il flusso se il backend non è disponibile
      console.warn('⚠️ Errore nell\'invio video al backend (non critico):', error.message);
      console.warn('⚠️ Il sistema continuerà a funzionare con soglie fisse');
    } finally {
      // Rimuovi loading dallo store
      analysisStore.setLoading(false);
    }
  }
  
  // ============================================================================
  // FUNZIONI DI CALCOLO RIMOSSE - TUTTO SPOSTATO NEL BACKEND
  // ============================================================================
  // Le seguenti funzioni sono state rimosse perché i calcoli vengono ora
  // eseguiti completamente dal backend:
  // - calculateBaselineResults() -> Backend restituisce risultati completi
  // - calculateStats() -> Backend calcola statistiche
  // - calculateTemporalMetrics() -> Backend calcola metriche temporali
  // - buildRangeObject() -> Backend calcola e formatta ranges
  // ============================================================================
  
  // Funzione rimossa: calculateBaselineResults()
  // Funzione rimossa: calculateStats()
  // Funzione rimossa: calculateTemporalMetrics()
  // Funzione rimossa: buildRangeObject()
  // 
  // TUTTI i calcoli vengono ora eseguiti dal backend e restituiti già pronti.
  
  function cleanup() {
    if (animationFrame) {
      cancelAnimationFrame(animationFrame);
    }
    
    if (pose) {
      pose.close();
    }
    
    if (typeof window !== 'undefined') {
      window.removeEventListener('resize', handleResize);
    }
  }
  
  // Funzione rimossa: buildRangeObject()
  // I range vengono ora calcolati e formattati dal backend
  
  // Quando il video è pronto, avvialo
  async function handleCanPlay() {
    if (isProcessing) {
      // Aspetta un momento per assicurarsi che le dimensioni siano corrette
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Ricalcola dimensioni canvas
      handleResize();
      
      try {
        await videoElement.play();
        processFrame();
      } catch (error) {
        console.error('Errore avvio video:', error);
      }
    }
  }
</script>

<div class="baseline-analyzer">
  <!-- Video nascosto - processamento in background -->
  <video
    bind:this={videoElement}
    class="hidden-video"
    on:loadedmetadata={handleVideoLoaded}
    on:canplay={handleCanPlay}
    on:ended={handleVideoEnded}
    preload="auto"
    playsinline
    muted
  >
    <track kind="captions" />
  </video>
  
  <canvas bind:this={canvasElement} class="hidden-canvas" />
  
  <div class="processing-display">
    <div class="processing-icon">⚙️</div>
    <h3>Creazione Baseline in Corso</h3>
    <p class="processing-description">
      I 5 video vengono analizzati in background per calcolare i range biomeccanici di riferimento.
    </p>
  </div>
  
  {#if isAnalyzing}
    <div class="progress-section">
      <div class="progress-info">
        <span class="pulse-dot"></span>
        <span>Analisi Baseline: Video {currentVideoIndex + 1} di {videoUrls.length}</span>
      </div>
      
      <div class="progress-bar">
        <div class="progress-fill" style="width: {progress}%"></div>
      </div>
      
      <div class="progress-text">
        {progress}% completato
      </div>
    </div>
  {/if}
</div>

<style>
  .baseline-analyzer {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  
  /* Video e canvas nascosti - solo per processamento */
  .hidden-video,
  .hidden-canvas {
    display: none;
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
    margin: 0;
  }
  
  .progress-section {
    padding: 1rem;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 8px;
    margin-top: 1rem;
  }
  
  .progress-info {
    display: flex;
    align-items: center;
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
    transition: width 0.3s ease;
    border-radius: 4px;
  }
  
  .progress-text {
    text-align: center;
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.85rem;
  }
</style>

