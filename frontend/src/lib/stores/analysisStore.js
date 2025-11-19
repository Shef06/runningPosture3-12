/**
 * Store Svelte per gestire lo stato dell'analisi
 */
import { writable } from 'svelte/store';

// Stato iniziale
const initialState = {
  // Flusso principale
  mainFlow: null, // 'baseline' | 'analyze'
  
  // Step corrente
  currentStep: 1,
  
  // Metodo di acquisizione video
  videoMethod: null, // 'upload' | 'record'
  
  // Video/Recording
  videoFile: null,
  videoUrl: null,
  baselineVideos: [], // Array di 5 video per baseline
  baselineVideoUrls: [], // URLs per preview
  recordedBlob: null,
  isRecording: false,
  selectedCamera: null,
  availableCameras: [],
  
  // Calibrazione
  speed: null, // km/h - obbligatorio
  fps: null, // obbligatorio
  height: 180, // cm
  mass: 70, // kg
  
  // Risultati
  results: null,
  
  // Baseline ranges (salvati separatamente per confronti)
  baselineRanges: null, // { leftKneeAngle: {min, max}, rightKneeAngle: {min, max}, ... }
  
  // Baseline thresholds (E_max e soglie dinamiche dal backend)
  baselineThresholds: null, // { e_max, optimal, good, moderate, attention, critical }
  
  // Analisi in corso
  isAnalyzing: false,
  
  // UI
  loading: false,
  error: null,
  message: null
};

function createAnalysisStore() {
  const { subscribe, set, update } = writable(initialState);
  
  // Carica dati salvati da localStorage all'inizializzazione
  if (typeof window !== 'undefined') {
    try {
      const savedThresholds = localStorage.getItem('baselineThresholds');
      if (savedThresholds) {
        const parsed = JSON.parse(savedThresholds);
        initialState.baselineThresholds = parsed;
      }
      
      const savedRanges = localStorage.getItem('baselineRanges');
      if (savedRanges) {
        const parsed = JSON.parse(savedRanges);
        initialState.baselineRanges = parsed;
      }
    } catch (error) {
      console.warn('⚠️ Errore nel caricare dati da localStorage:', error);
    }
  }
  
  return {
    subscribe,
    
    // Reset completo
    reset: () => set(initialState),
    
    // Imposta flusso principale
    setMainFlow: (flow) => update(state => ({ ...state, mainFlow: flow, currentStep: 2 })),
    
    // Naviga tra gli step
    nextStep: () => update(state => ({ ...state, currentStep: state.currentStep + 1 })),
    prevStep: () => update(state => ({ ...state, currentStep: Math.max(1, state.currentStep - 1) })),
    goToStep: (step) => update(state => ({ ...state, currentStep: step })),
    
    // Metodo video
    setVideoMethod: (method) => update(state => ({ 
      ...state, 
      videoMethod: method,
      currentStep: 3 
    })),
    
    // Upload video singolo
    setVideoFile: (file) => update(state => {
      if (state.videoUrl) {
        URL.revokeObjectURL(state.videoUrl);
      }
      return {
        ...state,
        videoFile: file,
        videoUrl: file ? URL.createObjectURL(file) : null
      };
    }),
    
    // Upload multiplo baseline (5 video)
    setBaselineVideos: (files) => update(state => {
      // Revoca vecchi URL
      state.baselineVideoUrls.forEach(url => URL.revokeObjectURL(url));
      
      // Crea nuovi URL
      const urls = files.map(file => URL.createObjectURL(file));
      
      return {
        ...state,
        baselineVideos: files,
        baselineVideoUrls: urls
      };
    }),
    
    // Aggiungi singolo video alla baseline
    addBaselineVideo: (file) => update(state => {
      if (state.baselineVideos.length >= 5) {
        return state; // Già 5 video
      }
      const newVideos = [...state.baselineVideos, file];
      const newUrl = URL.createObjectURL(file);
      const newUrls = [...state.baselineVideoUrls, newUrl];
      
      return {
        ...state,
        baselineVideos: newVideos,
        baselineVideoUrls: newUrls
      };
    }),
    
    // Rimuovi video dalla baseline
    removeBaselineVideo: (index) => update(state => {
      URL.revokeObjectURL(state.baselineVideoUrls[index]);
      const newVideos = state.baselineVideos.filter((_, i) => i !== index);
      const newUrls = state.baselineVideoUrls.filter((_, i) => i !== index);
      
      return {
        ...state,
        baselineVideos: newVideos,
        baselineVideoUrls: newUrls
      };
    }),
    
    // Recording
    setRecording: (isRecording) => update(state => ({ ...state, isRecording })),
    setRecordedBlob: (blob) => update(state => {
      if (state.videoUrl) {
        URL.revokeObjectURL(state.videoUrl);
      }
      return {
        ...state,
        recordedBlob: blob,
        videoUrl: blob ? URL.createObjectURL(blob) : null
      };
    }),
    setSelectedCamera: (cameraId) => update(state => ({ ...state, selectedCamera: cameraId })),
    setAvailableCameras: (cameras) => update(state => ({ ...state, availableCameras: cameras })),
    
    // Calibrazione
    setCalibration: (speed, fps, height, mass) => update(state => ({
      ...state,
      speed: speed !== null && speed !== undefined ? speed : state.speed,
      fps: fps !== null && fps !== undefined ? fps : state.fps,
      height: height || state.height,
      mass: mass || state.mass
    })),
    
    // Risultati
    setResults: (results) => update(state => ({ ...state, results, currentStep: 6 })),
    
    // Baseline ranges (salvati separatamente)
    setBaselineRanges: (ranges) => {
      // Salva in localStorage per persistenza
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('baselineRanges', JSON.stringify(ranges));
        } catch (error) {
          console.warn('⚠️ Errore nel salvare ranges in localStorage:', error);
        }
      }
      
      update(state => ({ 
        ...state, 
        baselineRanges: ranges 
      }));
    },
    
    // Baseline thresholds (E_max e soglie dinamiche)
    setBaselineThresholds: (thresholds) => {
      // Salva in localStorage per persistenza
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('baselineThresholds', JSON.stringify(thresholds));
        } catch (error) {
          console.warn('⚠️ Errore nel salvare thresholds in localStorage:', error);
        }
      }
      
      update(state => ({ 
        ...state, 
        baselineThresholds: thresholds 
      }));
    },
    
    // Analisi
    setAnalyzing: (isAnalyzing) => update(state => ({ ...state, isAnalyzing })),
    
    // UI feedback
    setLoading: (loading) => update(state => ({ ...state, loading })),
    setError: (error) => update(state => ({ ...state, error, loading: false })),
    setMessage: (message) => update(state => ({ ...state, message })),
    clearMessages: () => update(state => ({ ...state, error: null, message: null }))
  };
}

export const analysisStore = createAnalysisStore();

