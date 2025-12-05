<script>
  import { onMount, onDestroy } from 'svelte';
  import { analysisStore } from '../stores/analysisStore.js';
  
  export let videoElement; // Reference to the video element
  
  let ghostCanvas;
  let ghostCtx;
  let currentFrame = -1; // -1 per indicare nessun frame caricato
  let ghostImage = null;
  let animationFrame = null;
  let isLoading = false;
  let pendingRequest = null; // Per evitare richieste multiple
  let imageCache = new Map(); // Cache per le immagini già caricate
  let fps = 30; // Default, verrà aggiornato dai risultati
  
  $: ghostVisionEnabled = $analysisStore.ghostVisionEnabled;
  $: results = $analysisStore.results;
  
  // Aggiorna FPS dai risultati se disponibile
  $: if (results?.ghost_frames_count) {
    // Prova a ottenere FPS dalla baseline o usa default
    fps = results.fps || 30;
  }
  
  onMount(() => {
    if (ghostCanvas) {
      ghostCtx = ghostCanvas.getContext('2d');
      console.log('👻 GhostVisionOverlay: Componente montato');
      
      if (videoElement) {
        videoElement.addEventListener('play', handleVideoPlay);
        videoElement.addEventListener('pause', handleVideoPause);
        videoElement.addEventListener('seeked', handleVideoSeeked);
        videoElement.addEventListener('timeupdate', handleTimeUpdate);
        videoElement.addEventListener('loadedmetadata', updateCanvasDimensions);
        
        updateCanvasDimensions();
        console.log('✅ Event listeners registrati per video element');
      } else {
        console.warn('⚠️ GhostVisionOverlay: videoElement non disponibile');
      }
    }
    
    window.addEventListener('resize', updateCanvasDimensions);
  });
  
  onDestroy(() => {
    stopGhostUpdate();
    
    // Cancella richieste pending
    if (pendingRequest) {
      pendingRequest.abort();
      pendingRequest = null;
    }
    
    // Pulisci cache immagini
    imageCache.forEach(img => {
      if (img.src) {
        img.src = ''; // Release image
      }
    });
    imageCache.clear();
    ghostImage = null;
    
    if (videoElement) {
      videoElement.removeEventListener('play', handleVideoPlay);
      videoElement.removeEventListener('pause', handleVideoPause);
      videoElement.removeEventListener('seeked', handleVideoSeeked);
      videoElement.removeEventListener('timeupdate', handleTimeUpdate);
      videoElement.removeEventListener('loadedmetadata', updateCanvasDimensions);
    }
    window.removeEventListener('resize', updateCanvasDimensions);
  });
  
  // Watch for ghost vision toggle changes
  $: if (ghostVisionEnabled && videoElement) {
    if (!videoElement.paused) {
      startGhostUpdate();
    }
  } else {
    stopGhostUpdate();
  }
  
  function handleVideoPlay() {
    if (ghostVisionEnabled) {
      startGhostUpdate();
    }
  }
  
  function handleVideoPause() {
    stopGhostUpdate();
  }
  
  function handleVideoSeeked() {
    if (ghostVisionEnabled && videoElement) {
      currentFrame = -1; // Force reload
      updateGhostFrame();
    }
  }
  
  function handleTimeUpdate() {
    // Usato per sincronizzazione più precisa
    if (ghostVisionEnabled && !isLoading) {
      updateGhostFrame();
    }
  }
  
  function updateCanvasDimensions() {
    if (!ghostCanvas || !videoElement || !ghostCtx) return;
    
    const container = videoElement.parentElement;
    if (!container) return;
    
    const containerRect = container.getBoundingClientRect();
    const videoWidth = videoElement.videoWidth || 0;
    const videoHeight = videoElement.videoHeight || 0;
    
    if (videoWidth === 0 || videoHeight === 0) return;
    
    const containerAspect = containerRect.width / containerRect.height;
    const videoAspect = videoWidth / videoHeight;
    
    let displayWidth, displayHeight;
    if (videoAspect > containerAspect) {
      displayWidth = containerRect.width;
      displayHeight = containerRect.width / videoAspect;
    } else {
      displayWidth = containerRect.height * videoAspect;
      displayHeight = containerRect.height;
    }
    
    const offsetX = (containerRect.width - displayWidth) / 2;
    const offsetY = (containerRect.height - displayHeight) / 2;
    
    // Usa devicePixelRatio per canvas più nitido
    const dpr = window.devicePixelRatio || 1;
    const canvasWidth = displayWidth * dpr;
    const canvasHeight = displayHeight * dpr;
    
    // Salva le dimensioni di display per il drawing
    ghostCanvas.dataset.displayWidth = displayWidth;
    ghostCanvas.dataset.displayHeight = displayHeight;
    
    ghostCanvas.width = canvasWidth;
    ghostCanvas.height = canvasHeight;
    ghostCanvas.style.width = displayWidth + 'px';
    ghostCanvas.style.height = displayHeight + 'px';
    ghostCanvas.style.left = offsetX + 'px';
    ghostCanvas.style.top = offsetY + 'px';
    
    // Reset transform e scala per il device pixel ratio
    ghostCtx.setTransform(1, 0, 0, 1, 0, 0);
    ghostCtx.scale(dpr, dpr);
    
    // Redraw se abbiamo un'immagine
    if (ghostImage) {
      drawGhostImage();
    }
  }
  
  function startGhostUpdate() {
    if (!ghostVisionEnabled || !videoElement || videoElement.paused) return;
    
    if (animationFrame) return; // Già attivo
    
    console.log('▶️ GhostVisionOverlay: Avvio loop di aggiornamento frame');
    
    function updateLoop() {
      if (ghostVisionEnabled && videoElement && !videoElement.paused) {
        updateGhostFrame();
        animationFrame = requestAnimationFrame(updateLoop);
      } else {
        stopGhostUpdate();
      }
    }
    
    updateLoop();
  }
  
  function stopGhostUpdate() {
    if (animationFrame) {
      cancelAnimationFrame(animationFrame);
      animationFrame = null;
    }
    
    // Cancella richieste pending
    if (pendingRequest) {
      pendingRequest.abort();
      pendingRequest = null;
    }
    
    // Clear canvas
    if (ghostCtx && ghostCanvas) {
      ghostCtx.clearRect(0, 0, ghostCanvas.width, ghostCanvas.height);
    }
  }
  
  async function updateGhostFrame() {
    if (!ghostVisionEnabled || !videoElement || !ghostCtx || !ghostCanvas) return;
    if (isLoading) return; // Evita richieste multiple
    
    // Calculate current frame number based on video time
    const frameNumber = Math.floor(videoElement.currentTime * fps);
    
    // Se il frame è già caricato e nella cache, usa quello
    if (frameNumber === currentFrame && ghostImage) {
      drawGhostImage();
      return;
    }
    
    // Se stiamo già caricando questo frame, aspetta
    if (pendingRequest && currentFrame === frameNumber) {
      return;
    }
    
    // Nuovo frame - cancella richiesta precedente
    if (pendingRequest) {
      pendingRequest.abort();
    }
    
    currentFrame = frameNumber;
    
    // Controlla cache
    if (imageCache.has(frameNumber)) {
      ghostImage = imageCache.get(frameNumber);
      drawGhostImage();
      return;
    }
    
    // Fetch ghost frame from backend
    try {
      isLoading = true;
      const apiUrl = `http://localhost:5000/api/ghost_frame_by_number/${frameNumber}`;
      
      // Crea AbortController per cancellare richieste
      const controller = new AbortController();
      pendingRequest = controller;
      
      const response = await fetch(apiUrl, {
        signal: controller.signal
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success' && data.ghost_url) {
          await loadGhostImage(`http://localhost:5000${data.ghost_url}`, frameNumber);
        } else {
          // Frame non disponibile - pulisci canvas
          ghostImage = null;
          if (ghostCtx && ghostCanvas) {
            ghostCtx.clearRect(0, 0, ghostCanvas.width, ghostCanvas.height);
          }
        }
      } else if (response.status === 404) {
        // Frame non trovato - normale per frame fuori range
        ghostImage = null;
        if (ghostCtx && ghostCanvas) {
          ghostCtx.clearRect(0, 0, ghostCanvas.width, ghostCanvas.height);
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        // Richiesta cancellata - normale
        return;
      }
      console.warn(`❌ Errore nel caricare ghost frame #${frameNumber}:`, error);
      ghostImage = null;
    } finally {
      isLoading = false;
      pendingRequest = null;
    }
  }
  
  async function loadGhostImage(url, frameNumber) {
    return new Promise((resolve, reject) => {
      // Controlla se l'immagine è già in cache
      if (imageCache.has(frameNumber)) {
        ghostImage = imageCache.get(frameNumber);
        drawGhostImage();
        resolve();
        return;
      }
      
      const img = new Image();
      img.crossOrigin = 'anonymous';
      
      img.onload = () => {
        // Salva in cache (limita a 50 immagini per evitare memory leak)
        if (imageCache.size > 50) {
          const firstKey = imageCache.keys().next().value;
          const oldImg = imageCache.get(firstKey);
          if (oldImg && oldImg.src) {
            oldImg.src = '';
          }
          imageCache.delete(firstKey);
        }
        
        imageCache.set(frameNumber, img);
        ghostImage = img;
        drawGhostImage();
        resolve();
      };
      
      img.onerror = (err) => {
        console.warn(`❌ Errore nel caricare immagine ghost da ${url}:`, err);
        ghostImage = null;
        reject(err);
      };
      
      img.src = url;
    });
  }
  
  function drawGhostImage() {
    if (!ghostImage || !ghostCtx || !ghostCanvas) return;
    
    // Ottieni dimensioni di display (già scalate per DPR nel contesto)
    const displayWidth = parseFloat(ghostCanvas.dataset.displayWidth || ghostCanvas.style.width.replace('px', '') || 0);
    const displayHeight = parseFloat(ghostCanvas.dataset.displayHeight || ghostCanvas.style.height.replace('px', '') || 0);
    
    if (displayWidth === 0 || displayHeight === 0) return;
    
    // Clear canvas (usa dimensioni già scalate dal contesto)
    ghostCtx.clearRect(0, 0, displayWidth, displayHeight);
    
    // Set opacity for ghost effect
    ghostCtx.globalAlpha = 0.5; // 50% opacity
    
    // Draw the ghost image scaled to canvas size
    ghostCtx.drawImage(
      ghostImage,
      0, 0,
      ghostImage.width, ghostImage.height,
      0, 0,
      displayWidth, displayHeight
    );
    
    // Reset alpha
    ghostCtx.globalAlpha = 1.0;
  }
</script>

<canvas
  bind:this={ghostCanvas}
  class="ghost-canvas"
  class:visible={ghostVisionEnabled}
  class:loading={isLoading}
/>

<style>
  .ghost-canvas {
    position: absolute;
    top: 0;
    left: 0;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.2s ease;
    z-index: 10;
    image-rendering: -webkit-optimize-contrast;
    image-rendering: crisp-edges;
  }
  
  .ghost-canvas.visible {
    opacity: 1;
  }
  
  .ghost-canvas.loading {
    opacity: 0.7;
  }
</style>

