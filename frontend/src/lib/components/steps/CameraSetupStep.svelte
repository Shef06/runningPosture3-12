<script>
  import { analysisStore } from '../../stores/analysisStore.js';
  
  $: availableCameras = $analysisStore.availableCameras;
  $: selectedCamera = $analysisStore.selectedCamera;
  
  function selectCamera(event) {
    const deviceId = event.target.value;
    analysisStore.setSelectedCamera(deviceId);
    // Notifica il VideoHolder di cambiare camera
    window.dispatchEvent(new CustomEvent('changecamera', { detail: deviceId }));
  }
  
  function continueToCalibration() {
    analysisStore.nextStep();
  }
</script>

<div class="step-container">
  <h3>Calibrazione Telecamera</h3>
  <p class="step-description">
    Seleziona la telecamera da utilizzare. L'anteprima apparirà nel video holder.
  </p>
  
  <div class="form-group">
    <label for="camera-select">Seleziona Telecamera:</label>
    <select id="camera-select" on:change={selectCamera} value={selectedCamera}>
      {#if availableCameras.length === 0}
        <option>Caricamento telecamere...</option>
      {:else}
        {#each availableCameras as camera}
          <option value={camera.deviceId}>
            {camera.label || `Camera ${camera.deviceId.substring(0, 8)}`}
          </option>
        {/each}
      {/if}
    </select>
  </div>
  
  <div class="info-box compact">
    <p><strong>📹 Istruzioni:</strong></p>
    <ul>
      <li>Inquadrare corpo intero</li>
      <li>Buona illuminazione</li>
      <li>Vista frontale</li>
      <li>Camera ferma</li>
    </ul>
  </div>
  
  <button 
    class="btn-primary" 
    on:click={continueToCalibration}
    disabled={!selectedCamera || availableCameras.length === 0}
  >
    Continua →
  </button>
</div>

<style>
  @import './steps-common.css';
  
  .info-box.compact ul {
    margin-bottom: 0;
  }
</style>

