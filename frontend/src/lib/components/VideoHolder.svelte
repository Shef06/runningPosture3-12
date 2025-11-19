<script>
  import { analysisStore } from '../stores/analysisStore.js';
  import { onMount, onDestroy } from 'svelte';
  import VideoAnalyzer from './VideoAnalyzer.svelte';
  import BaselineUploader from './BaselineUploader.svelte';
  
  let videoElement;
  let stream;
  let mediaRecorder;
  let recordedChunks = [];
  
  $: videoUrl = $analysisStore.videoUrl;
  $: isRecording = $analysisStore.isRecording;
  $: videoMethod = $analysisStore.videoMethod;
  $: selectedCamera = $analysisStore.selectedCamera;
  $: mainFlow = $analysisStore.mainFlow;
  $: baselineVideos = $analysisStore.baselineVideos;
  $: baselineVideoUrls = $analysisStore.baselineVideoUrls;
  $: isAnalyzing = $analysisStore.isAnalyzing;
  
  let currentVideoIndex = 0;
  let videoAnalyzerRef;
  
  // Naviga tra i video baseline
  function nextVideo() {
    if (currentVideoIndex < baselineVideos.length - 1) {
      currentVideoIndex++;
    }
  }
  
  function prevVideo() {
    if (currentVideoIndex > 0) {
      currentVideoIndex--;
    }
  }
  
  function selectVideo(index) {
    currentVideoIndex = index;
  }
  
  // Inizializza webcam
  async function initCamera() {
    try {
      // Ottieni lista telecamere disponibili
      const devices = await navigator.mediaDevices.enumerateDevices();
      const cameras = devices.filter(device => device.kind === 'videoinput');
      analysisStore.setAvailableCameras(cameras);
      
      // Usa la telecamera selezionata o la prima disponibile
      const deviceId = selectedCamera || (cameras[0]?.deviceId);
      
      if (deviceId) {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { deviceId: { exact: deviceId } },
          audio: false
        });
        
        if (videoElement) {
          videoElement.srcObject = stream;
        }
      }
    } catch (error) {
      console.error('Errore accesso camera:', error);
      analysisStore.setError('Impossibile accedere alla webcam');
    }
  }
  
  // Cambia telecamera
  async function changeCamera(deviceId) {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    analysisStore.setSelectedCamera(deviceId);
    await initCamera();
  }
  
  // Inizia registrazione
  async function startRecording() {
    if (!stream) {
      await initCamera();
    }
    
    recordedChunks = [];
    mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm' });
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        recordedChunks.push(event.data);
      }
    };
    
    mediaRecorder.onstop = () => {
      const blob = new Blob(recordedChunks, { type: 'video/webm' });
      analysisStore.setRecordedBlob(blob);
      analysisStore.setRecording(false);
    };
    
    mediaRecorder.start();
    analysisStore.setRecording(true);
  }
  
  // Ferma registrazione
  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    }
  }
  
  // Cleanup
  function cleanup() {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    if (mediaRecorder) {
      mediaRecorder = null;
    }
  }
  
  onMount(() => {
    if (videoMethod === 'record') {
      initCamera();
    }
    
    // Event listeners
    const handleChangeCamera = (e) => changeCamera(e.detail);
    const handleStartRecording = () => startRecording();
    const handleStopRecording = () => stopRecording();
    
    window.addEventListener('changecamera', handleChangeCamera);
    window.addEventListener('startrecording', handleStartRecording);
    window.addEventListener('stoprecording', handleStopRecording);
    
    return () => {
      window.removeEventListener('changecamera', handleChangeCamera);
      window.removeEventListener('startrecording', handleStartRecording);
      window.removeEventListener('stoprecording', handleStopRecording);
    };
  });
  
  onDestroy(cleanup);
  
  // Esponi funzioni per il parent
  export { startRecording, stopRecording, changeCamera };
  
  // Watch videoMethod per inizializzare camera
  $: if (videoMethod === 'record' && !stream) {
    initCamera();
  }
</script>

<div class="video-holder">
  <div class="video-container">
    {#if mainFlow === 'baseline' && videoMethod === 'upload' && baselineVideos.length === 5 && isAnalyzing}
      <!-- Creazione baseline con 5 video - invio diretto al backend -->
      <BaselineUploader />
    
    {:else if mainFlow === 'analyze' && videoUrl && videoMethod === 'upload'}
      <!-- Analisi video singolo con scheletro -->
      <VideoAnalyzer 
        bind:this={videoAnalyzerRef}
        videoUrl={videoUrl}
        onAnalysisComplete={() => {
          console.log('Analisi video completata');
          analysisStore.setMessage('✅ Analisi completata!');
        }}
      />
    
    {:else if mainFlow === 'baseline' && videoMethod === 'upload' && baselineVideos.length > 0}
      <!-- Gallery 5 video baseline -->
      <div class="baseline-gallery">
        <div class="main-video">
          <video src={baselineVideoUrls[currentVideoIndex]} controls class="video-display">
            <track kind="captions" />
          </video>
          
          <!-- Navigation -->
          {#if baselineVideos.length > 1}
            <div class="video-nav">
              <button 
                class="nav-btn prev" 
                on:click={prevVideo}
                disabled={currentVideoIndex === 0}
              >
                ‹
              </button>
              <span class="video-counter">
                {currentVideoIndex + 1} / {baselineVideos.length}
              </span>
              <button 
                class="nav-btn next" 
                on:click={nextVideo}
                disabled={currentVideoIndex === baselineVideos.length - 1}
              >
                ›
              </button>
            </div>
          {/if}
        </div>
        
        <!-- Thumbnail grid -->
        <div class="thumbnail-grid">
          {#each baselineVideos as video, index}
            <button 
              class="thumbnail-item" 
              class:active={index === currentVideoIndex}
              on:click={() => selectVideo(index)}
              title={video.name}
            >
              <video src={baselineVideoUrls[index]} class="thumbnail-preview">
                <track kind="captions" />
              </video>
              <span class="thumbnail-number">{index + 1}</span>
            </button>
          {/each}
        </div>
      </div>
      
    {:else if videoUrl && videoMethod === 'upload'}
      <!-- Video singolo caricato -->
      <video src={videoUrl} controls class="video-display">
        <track kind="captions" />
      </video>
    {:else if videoMethod === 'record'}
      {#if videoUrl}
        <!-- Video registrato (playback) -->
        <video src={videoUrl} controls class="video-display">
          <track kind="captions" />
        </video>
      {:else}
        <!-- Preview webcam -->
        <video bind:this={videoElement} autoplay playsinline muted class="video-display">
          <track kind="captions" />
        </video>
        
        {#if isRecording}
          <div class="recording-indicator">
            <span class="recording-dot"></span>
            REC
          </div>
        {/if}
      {/if}
    {:else}
      <!-- Placeholder -->
      <div class="video-placeholder">
        <div class="placeholder-content">
          <svg width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
          <p>Video Placeholder</p>
          <span class="hint">Il video apparirà qui</span>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .video-holder {
    height: 100%;
    width: 100%;
    display: flex;
    flex-direction: column;
    background: var(--secondary-bg);
    border-radius: var(--border-radius);
    padding: 1rem;
    box-shadow: var(--box-shadow);
    box-sizing: border-box;
  }
  
  .video-container {
    flex: 1;
    position: relative;
    background: rgba(0, 0, 0, 0.5);
    border-radius: 8px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 0;
    width: 100%;
  }
  
  .video-display {
    max-width: 100%;
    max-height: 100%;
    width: auto;
    height: auto;
    object-fit: contain;
  }
  
  .video-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .placeholder-content {
    text-align: center;
    color: rgba(255, 255, 255, 0.4);
  }
  
  .placeholder-content svg {
    opacity: 0.3;
    margin-bottom: 1rem;
  }
  
  .placeholder-content p {
    font-size: 1.2rem;
    margin-bottom: 0.5rem;
  }
  
  .hint {
    font-size: 0.9rem;
    opacity: 0.7;
  }
  
  .recording-indicator {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background: rgba(231, 76, 60, 0.9);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    animation: pulse 1.5s infinite;
  }
  
  .recording-dot {
    width: 12px;
    height: 12px;
    background: white;
    border-radius: 50%;
    animation: blink 1s infinite;
  }
  
  @keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
  }
  
  @keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
  }
  
  /* Baseline Gallery */
  .baseline-gallery {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    box-sizing: border-box;
  }
  
  .main-video {
    flex: 1;
    position: relative;
    background: black;
    border-radius: 8px;
    overflow: hidden;
    min-height: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .main-video .video-display {
    max-width: 100%;
    max-height: 100%;
    width: auto;
    height: auto;
    object-fit: contain;
  }
  
  .video-nav {
    position: absolute;
    bottom: 1rem;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 1rem;
    background: rgba(0, 0, 0, 0.8);
    padding: 0.5rem 1rem;
    border-radius: 20px;
    backdrop-filter: blur(10px);
  }
  
  .nav-btn {
    width: 32px;
    height: 32px;
    background: rgba(255, 255, 255, 0.2);
    border: none;
    border-radius: 50%;
    color: white;
    font-size: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.3s ease;
    padding: 0;
    line-height: 1;
  }
  
  .nav-btn:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.3);
    transform: scale(1.1);
  }
  
  .nav-btn:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }
  
  .video-counter {
    color: white;
    font-weight: 600;
    font-size: 0.9rem;
    min-width: 50px;
    text-align: center;
  }
  
  .thumbnail-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 0.5rem;
    height: 80px;
    flex-shrink: 0;
  }
  
  .thumbnail-item {
    position: relative;
    background: rgba(0, 0, 0, 0.5);
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-radius: 6px;
    overflow: hidden;
    cursor: pointer;
    transition: all 0.3s ease;
    padding: 0;
  }
  
  .thumbnail-item:hover {
    border-color: var(--accent-color);
    transform: translateY(-2px);
  }
  
  .thumbnail-item.active {
    border-color: var(--success-color);
    box-shadow: 0 0 10px var(--success-color);
  }
  
  .thumbnail-preview {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .thumbnail-number {
    position: absolute;
    top: 4px;
    left: 4px;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
  }
  
  .thumbnail-item.active .thumbnail-number {
    background: var(--success-color);
  }
  
  /* Rimuovi outline focus */
  video:focus,
  .thumbnail-item:focus,
  .nav-btn:focus {
    outline: none;
  }
</style>

