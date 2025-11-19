<script>
  import { onMount, onDestroy } from 'svelte';
  import { analysisStore } from '../stores/analysisStore.js';
  
  export let videoUrl;
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
  let collectedFrames = [];
  let frameCount = 0;
  
  $: isAnalyzing = $analysisStore.isAnalyzing;
  $: baselineRanges = $analysisStore.baselineRanges;
  $: baselineThresholds = $analysisStore.baselineThresholds;
  $: videoFile = $analysisStore.videoFile;
  $: speed = $analysisStore.speed;
  $: fps = $analysisStore.fps;
  $: height = $analysisStore.height;
  $: mass = $analysisStore.mass;
  
  onMount(async () => {
    if (typeof window !== 'undefined') {
      await initializeMediaPipe();
      window.addEventListener('resize', handleResize);
      
      // Log per debug: verifica se E_max è disponibile
      const storeState = $analysisStore;
      if (storeState.baselineThresholds) {
        console.log('✅ E_max disponibile nello store:', storeState.baselineThresholds.e_max);
      } else {
        console.warn('⚠️ E_max NON disponibile nello store - verifica localStorage o rifai baseline');
      }
    }
  });
  
  // Auto-start: invia video al backend quando isAnalyzing diventa true
  $: if (isAnalyzing && videoFile && !isProcessing && speed && fps) {
    // Usa setTimeout per evitare problemi di reattività
    setTimeout(() => {
      if (!isProcessing) {
        sendVideoToBackend();
      }
    }, 100);
  }
  
  // Auto-stop quando isAnalyzing diventa false (non più necessario per backend)
  // $: if (!isAnalyzing && isProcessing) {
  //   stopAnalysis();
  // }
  
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
      
      console.log('✅ MediaPipe Pose inizializzato');
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
    if (!canvasElement || !canvasCtx || !videoElement) return;
    
    // Pulisci il canvas
    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    
    // Disegna lo scheletro se ci sono landmark
    if (results.poseLandmarks) {
      // Raccogli i dati per l'analisi finale
      frameCount++;
      
      if (results.poseLandmarks) {
        // Calcola metriche biomeccaniche principali
        const metrics = calculateBiomechanicalMetrics(results.poseLandmarks);
        
        collectedFrames.push({
          frameNumber: frameCount,
          timestamp: videoElement?.currentTime || 0,
          landmarks: results.poseLandmarks,
          angles: metrics.angles,       // Legacy per compatibilità UI
          features: metrics.features    // Nuove feature allineate al backend
        });
      }
      
      // Aggiorna le dimensioni del canvas ad ogni frame
      // (per gestire resize dinamici durante la riproduzione)
      updateCanvasDimensions();
      
      // Disegna le connessioni (le "ossa" dello scheletro)
      // MediaPipe scalerà automaticamente le coordinate normalizzate al canvas
      if (window.drawConnectors && window.POSE_CONNECTIONS) {
        window.drawConnectors(
          canvasCtx,
          results.poseLandmarks,
          window.POSE_CONNECTIONS,
          { color: '#00FF00', lineWidth: 4 }
        );
      }
      
      // Disegna i landmark (i "giunti" dello scheletro)
      if (window.drawLandmarks) {
        window.drawLandmarks(
          canvasCtx,
          results.poseLandmarks,
          { color: '#FF0000', lineWidth: 2, radius: 3 }
        );
      }
    }
    
    canvasCtx.restore();
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
    // Calcola l'angolo tra tre punti (a-b-c)
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
      // Invia il frame corrente a MediaPipe
      await pose.send({ image: videoElement });
      
      // Continua a processare il prossimo frame
      animationFrame = requestAnimationFrame(processFrame);
    } catch (error) {
      console.error('Errore nel processamento del frame:', error);
    }
  }
  
  function updateCanvasDimensions() {
    if (!canvasElement || !videoElement) return;
    
    // Calcola le dimensioni effettive del video visualizzato
    // (considerando object-fit: contain)
    const containerRect = videoElement.parentElement.getBoundingClientRect();
    const videoWidth = videoElement.videoWidth;
    const videoHeight = videoElement.videoHeight;
    
    if (videoWidth === 0 || videoHeight === 0) return;
    
    // Calcola le dimensioni visualizzate effettive del video
    const containerAspect = containerRect.width / containerRect.height;
    const videoAspect = videoWidth / videoHeight;
    
    let displayWidth, displayHeight;
    if (videoAspect > containerAspect) {
      // Il video è più largo del container
      displayWidth = containerRect.width;
      displayHeight = containerRect.width / videoAspect;
    } else {
      // Il video è più alto del container
      displayWidth = containerRect.height * videoAspect;
      displayHeight = containerRect.height;
    }
    
    // Calcola l'offset per centrare il video
    const offsetX = (containerRect.width - displayWidth) / 2;
    const offsetY = (containerRect.height - displayHeight) / 2;
    
    // Imposta le dimensioni del canvas
    canvasElement.width = displayWidth;
    canvasElement.height = displayHeight;
    
    // Posiziona il canvas esattamente sopra il video
    canvasElement.style.width = displayWidth + 'px';
    canvasElement.style.height = displayHeight + 'px';
    canvasElement.style.left = offsetX + 'px';
    canvasElement.style.top = offsetY + 'px';
    
    if (!canvasCtx) {
      canvasCtx = canvasElement.getContext('2d');
    }
  }
  
  function handleVideoLoaded() {
    if (canvasElement && videoElement) {
      updateCanvasDimensions();
      const rect = videoElement.getBoundingClientRect();
      console.log(`📹 Video caricato: ${videoElement.videoWidth}x${videoElement.videoHeight}, Display: ${rect.width}x${rect.height}, Canvas: ${canvasElement.width}x${canvasElement.height}`);
    }
  }
  
  // Ricalcola dimensioni canvas quando la finestra viene ridimensionata
  function handleResize() {
    if (canvasElement && videoElement) {
      updateCanvasDimensions();
    }
  }
  
  /**
   * Invia il video al backend per analisi completa
   * Tutti i calcoli vengono eseguiti dal backend
   */
  async function sendVideoToBackend() {
    if (!videoFile) {
      analysisStore.setError('Video non disponibile');
      return;
    }
    
    // Valida e converte parametri obbligatori
    const speedNum = typeof speed === 'string' ? parseFloat(speed) : speed;
    const fpsNum = typeof fps === 'string' ? parseFloat(fps) : fps;
    
    if (!speedNum || isNaN(speedNum) || speedNum <= 0) {
      analysisStore.setError('Velocità del tapis roulant (speed) è obbligatoria e deve essere un numero valido');
      return;
    }
    
    if (!fpsNum || isNaN(fpsNum) || fpsNum <= 0) {
      analysisStore.setError('FPS del video è obbligatorio e deve essere un numero valido');
      return;
    }
    
    // Imposta loading nello store per mostrare overlay in StepHolder
    analysisStore.setLoading(true);
    analysisStore.clearMessages();
    isProcessing = true;
    
    try {
      console.log('📤 Invio video al backend per analisi...');
      console.log('📊 Parametri:', { speed: speedNum, fps: fpsNum, videoFile: videoFile?.name });
      
      const formData = new FormData();
      formData.append('video', videoFile);
      formData.append('speed', speedNum.toString());
      formData.append('fps', fpsNum.toString());
      if (height) formData.append('height', height.toString());
      if (mass) formData.append('mass', mass.toString());
      
      const response = await fetch('http://localhost:5000/api/detect_anomaly', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        // Prova a leggere il messaggio di errore dal backend
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.message || errorMessage;
          console.error('❌ Errore backend:', errorData);
        } catch (e) {
          console.error('❌ Errore nel leggere risposta backend:', e);
        }
        throw new Error(errorMessage);
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        // Salva i risultati completi nello store
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
        
        analysisStore.setMessage('✅ Analisi completata con successo!');
        console.log('✅ Analisi completata:', data);
        
        // Call the completion callback if provided
        if (onAnalysisComplete) {
          onAnalysisComplete();
        }
    } else {
        const errorMsg = data.message || 'Errore nell\'analisi';
        analysisStore.setError(errorMsg);
      }
    } catch (error) {
      const errorMsg = error.message || `Errore di connessione: ${error.message}`;
      analysisStore.setError(errorMsg);
      console.error('❌ Errore invio video al backend:', error);
      console.error('❌ Dettagli errore:', {
        videoFile: videoFile?.name,
        speed: speedNum,
        fps: fpsNum,
        errorMessage: error.message
      });
    } finally {
      isProcessing = false;
      analysisStore.setAnalyzing(false);
      analysisStore.setLoading(false);
    }
  }
  
  // Funzione rimossa: startAnalysis() - ora tutto viene gestito dal backend
  // MediaPipe può essere mantenuto solo per visualizzazione opzionale dello scheletro
  
  function stopAnalysis() {
    analysisStore.setAnalyzing(false);
    isProcessing = false;
    
    if (animationFrame) {
      cancelAnimationFrame(animationFrame);
      animationFrame = null;
    }
    
    if (videoElement) {
      videoElement.pause();
    }
    
    console.log('⏸️ Analisi fermata');
  }
  
  function handleVideoEnded() {
    console.log('✅ Video terminato (preview)');
    // Nota: L'analisi completa viene gestita dal backend tramite sendVideoToBackend()
    // Questa funzione viene chiamata solo se il video viene riprodotto per preview
  }
  
  // ============================================================================
  // NOTA IMPORTANTE: TUTTI I CALCOLI SONO STATI SPOSTATI NEL BACKEND
  // ============================================================================
  // Il frontend non calcola più nulla. Tutti i calcoli (statistiche, anomaly score,
  // livelli, colori, ecc.) vengono eseguiti dal backend e restituiti già pronti.
  // 
  // Le funzioni di calcolo sono state rimosse:
  // - calculateFinalResults() -> Backend restituisce risultati completi
  // - calculateStats() -> Backend calcola statistiche
  // - calculateWeightedAnomalyScore() -> Backend calcola anomaly score
  // - getAnomalyLevel() -> Backend restituisce livello già calcolato
  // - getAnomalyColor() -> Backend restituisce colore già calcolato
  // - computeNormalizedDeviation() -> Backend calcola deviazioni
  // - calculateTemporalMetrics() -> Backend calcola metriche temporali
  // ============================================================================
  
  // Funzione rimossa: calculateFinalResults()
  // Funzione rimossa: convertScoreToEquivalentError()
  // Funzione rimossa: getAnomalyLevel()
  // Funzione rimossa: getAnomalyColor()
  // Funzione rimossa: calculateStats()
  // Funzione rimossa: computeNormalizedDeviation()
  // Funzione rimossa: normalizeBaselineFeatureRanges()
  // Funzione rimossa: calculateTemporalMetrics()
  // Funzione rimossa: detectContactDurations()
  // Funzione rimossa: smoothSeries()
  // 
  // TUTTE queste funzioni sono state spostate nel backend.
  // Il frontend riceve i risultati già calcolati dal backend tramite API.
  
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
  
  // Esporta le funzioni per il controllo esterno
  // Export rimosso: startAnalysis non esiste più (ora tutto gestito dal backend)
  // export { startAnalysis, stopAnalysis };
</script>

<div class="video-analyzer">
  <div class="video-container-wrapper">
    <video
      bind:this={videoElement}
      src={videoUrl}
      class="analysis-video"
      on:loadedmetadata={handleVideoLoaded}
      on:ended={handleVideoEnded}
      preload="auto"
      playsinline
    >
      <track kind="captions" />
    </video>
    
    <canvas
      bind:this={canvasElement}
      class="skeleton-canvas"
      class:visible={isAnalyzing}
    />
  </div>
  
  {#if isAnalyzing}
    <div class="analysis-indicator">
      <span class="pulse-dot"></span>
      Analisi in corso...
    </div>
  {/if}
</div>

<style>
  .video-analyzer {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  
  .video-container-wrapper {
    flex: 1;
    position: relative;
    background: black;
    border-radius: 8px;
    overflow: hidden;
    min-height: 0;
  }
  
  .analysis-video {
    width: 100%;
    height: 100%;
    object-fit: contain;
    display: block;
  }
  
  .skeleton-canvas {
    position: absolute;
    top: 0;
    left: 0;
    /* NON usare width/height 100% - il canvas deve avere dimensioni esatte */
    /* Le dimensioni vengono impostate dinamicamente in JavaScript */
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease;
    /* Il canvas viene posizionato esattamente sopra il video */
    /* Le dimensioni del canvas corrispondono alle dimensioni visualizzate del video */
  }
  
  .skeleton-canvas.visible {
    opacity: 1;
  }
  
  .analysis-indicator {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.5rem;
    background: rgba(46, 204, 113, 0.1);
    border: 1px solid var(--success-color);
    border-radius: 8px;
    color: var(--success-color);
    font-weight: 600;
    font-size: 0.9rem;
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
</style>

