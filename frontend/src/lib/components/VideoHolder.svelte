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
  
  async function initCamera() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const cameras = devices.filter(device => device.kind === 'videoinput');
      analysisStore.setAvailableCameras(cameras);
      
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
  
  async function changeCamera(deviceId) {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    analysisStore.setSelectedCamera(deviceId);
    await initCamera();
  }
  
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
  
  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    }
  }
  
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
  
  export { startRecording, stopRecording, changeCamera };

  $: if (videoMethod === 'record' && !stream) {
    initCamera();
  }
</script>

<div class="video-holder">
  <div class="video-container">
    {#if mainFlow === 'baseline' && videoMethod === 'upload' && baselineVideos.length === 5 && isAnalyzing}
      <BaselineUploader />
    
    {:else if mainFlow === 'analyze' && videoUrl && videoMethod === 'upload'}
      <VideoAnalyzer 
        bind:this={videoAnalyzerRef}
        videoUrl={videoUrl}
        onAnalysisComplete={() => {
          console.log('Analisi video completata');
          analysisStore.setMessage('✅ Analisi completata!');
        }}
      />
    
    {:else if mainFlow === 'baseline' && videoMethod === 'upload' && baselineVideos.length > 0}
      <div class="baseline-gallery">
        <div class="main-video">
          <video src={baselineVideoUrls[currentVideoIndex]} controls class="video-display">
            <track kind="captions" />
          </video>
          
          {#if baselineVideos.length > 1}
            <div class="video-nav">
              <button class="nav-btn prev" on:click={prevVideo} disabled={currentVideoIndex === 0}>‹</button>
              <span class="video-counter">{currentVideoIndex + 1} / {baselineVideos.length}</span>
              <button class="nav-btn next" on:click={nextVideo} disabled={currentVideoIndex === baselineVideos.length - 1}>›</button>
            </div>
          {/if}
        </div>
        
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
      <video src={videoUrl} controls class="video-display">
        <track kind="captions" />
      </video>
    {:else if videoMethod === 'record'}
      {#if videoUrl}
        <video src={videoUrl} controls class="video-display">
          <track kind="captions" />
        </video>
      {:else}
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
      <div class="video-placeholder">
        <div class="placeholder-content">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <p>Anteprima Video</p>
          <span class="hint">Il video o la webcam appariranno qui</span>
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
    position: relative;
  }
  
  .video-container {
    flex: 1;
    position: relative;
    background: #000; /* Nero puro per il video */
    border-radius: calc(var(--border-radius) - 4px);
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
    margin: 1rem;
    min-height: 0;
  }
  
  .video-display {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }
  
  .video-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
    opacity: 0.5;
  }
  
  .placeholder-content p {
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
    font-weight: 500;
  }
  
  .hint { font-size: 0.9rem; opacity: 0.7; }

  /* Indicatore REC */
  .recording-indicator {
    position: absolute;
    top: 2rem;
    right: 2rem;
    background: rgba(239, 68, 68, 0.9);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 30px;
    font-size: 0.8rem;
    letter-spacing: 1px;
    box-shadow: 0 0 15px rgba(239, 68, 68, 0.5);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 700;
    z-index: 10;
  }
  
  .recording-dot {
    width: 8px;
    height: 8px;
    background: white;
    border-radius: 50%;
    animation: blink 1s infinite;
  }
  
  @keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0; } }
  
  /* Baseline Gallery */
  .baseline-gallery {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .main-video {
    flex: 1;
    position: relative;
    background: black;
    overflow: hidden;
    min-height: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .video-nav {
    position: absolute;
    bottom: 1.5rem;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 1rem;
    background: rgba(0, 0, 0, 0.6);
    padding: 0.5rem 1.5rem;
    border-radius: 30px;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.1);
  }
  
  .nav-btn {
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 50%;
    color: white;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 1.2rem;
    transition: all 0.2s;
  }
  
  .nav-btn:hover:not(:disabled) { background: rgba(255,255,255,0.3); }
  .nav-btn:disabled { opacity: 0.3; cursor: not-allowed; }
  
  .video-counter {
    color: white;
    font-weight: 600;
    font-size: 0.9rem;
    font-variant-numeric: tabular-nums;
  }
  
  .thumbnail-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 0.5rem;
    height: 70px;
    flex-shrink: 0;
    padding: 0 0.5rem 0.5rem 0.5rem;
  }
  
  .thumbnail-item {
    position: relative;
    background: #000;
    border: 2px solid transparent;
    border-radius: 6px;
    overflow: hidden;
    cursor: pointer;
    transition: all 0.2s;
    opacity: 0.6;
    padding: 0;
  }
  
  .thumbnail-item:hover { opacity: 1; transform: translateY(-2px); }
  
  .thumbnail-item.active {
    border-color: #3b82f6;
    opacity: 1;
    box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
  }
  
  .thumbnail-preview {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .thumbnail-number {
    position: absolute;
    top: 2px;
    left: 2px;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    width: 18px;
    height: 18px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: 700;
  }
  
  .thumbnail-item.active .thumbnail-number {
    background: #3b82f6;
  }
</style>