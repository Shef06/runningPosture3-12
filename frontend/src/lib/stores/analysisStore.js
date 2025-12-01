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
  
  // Vista del video
  viewType: 'posterior', // 'posterior' | 'lateral'
  
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
  // RIMOSSI: height, mass
  
  // Risultati
  results: null,
  
  // Baseline ranges
  baselineRanges: null, 
  
  // Baseline thresholds
  baselineThresholds: null,
  
  // Analisi in corso
  isAnalyzing: false,
  
  // UI
  loading: false,
  error: null,
  message: null
};

function createAnalysisStore() {
  const { subscribe, set, update } = writable(initialState);
  
  // Carica dati salvati da localStorage
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
    
    // Reset completo - pulisce tutti gli stati e gli URL
    reset: () => {
      // Pulisci gli URL dei video prima di resettare
      update(state => {
        // Revoca URL video singolo
        if (state.videoUrl) {
          URL.revokeObjectURL(state.videoUrl);
        }
        // Revoca URL video baseline
        if (state.baselineVideoUrls && state.baselineVideoUrls.length > 0) {
          state.baselineVideoUrls.forEach(url => {
            if (url) URL.revokeObjectURL(url);
          });
        }
        return state;
      });
      
      // Crea uno stato pulito (senza dati da localStorage per baselineRanges e baselineThresholds)
      const cleanState = {
        ...initialState,
        // Mantieni baselineRanges e baselineThresholds da localStorage se esistono
        baselineRanges: initialState.baselineRanges,
        baselineThresholds: initialState.baselineThresholds
      };
      
      set(cleanState);
      
      // Ferma la camera stream se attiva (evento globale)
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('stopcamera'));
      }
    },
    
    // Imposta flusso principale
    setMainFlow: (flow) => update(state => ({ ...state, mainFlow: flow, currentStep: 2 })),
    
    // Naviga tra gli step
    nextStep: () => update(state => ({ ...state, currentStep: state.currentStep + 1 })),
    prevStep: () => update(state => ({ ...state, currentStep: Math.max(1, state.currentStep - 1) })),
    goToStep: (step) => update(state => ({ ...state, currentStep: step })),
    
    // Vista del video
    setViewType: (viewType) => update(state => ({ 
      ...state, 
      viewType: viewType,
      currentStep: 3 
    })),
    
    // Metodo video
    setVideoMethod: (method) => update(state => ({ 
      ...state, 
      videoMethod: method,
      currentStep: 4 
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
      state.baselineVideoUrls.forEach(url => URL.revokeObjectURL(url));
      const urls = files.map(file => URL.createObjectURL(file));
      return {
        ...state,
        baselineVideos: files,
        baselineVideoUrls: urls
      };
    }),
    
    // Aggiungi singolo video alla baseline
    addBaselineVideo: (file) => update(state => {
      if (state.baselineVideos.length >= 5) return state;
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
    
    // Calibrazione: Rimosso height e mass
    setCalibration: (speed, fps) => update(state => ({
      ...state,
      speed: speed !== null && speed !== undefined ? speed : state.speed,
      fps: fps !== null && fps !== undefined ? fps : state.fps
    })),
    
    // Risultati
    setResults: (results) => update(state => ({ ...state, results, currentStep: 7 })),
    
    // Baseline ranges
    setBaselineRanges: (ranges) => {
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('baselineRanges', JSON.stringify(ranges));
        } catch (error) {
          console.warn('⚠️ Errore nel salvare ranges in localStorage:', error);
        }
      }
      update(state => ({ ...state, baselineRanges: ranges }));
    },
    
    // Baseline thresholds
    setBaselineThresholds: (thresholds) => {
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('baselineThresholds', JSON.stringify(thresholds));
        } catch (error) {
          console.warn('⚠️ Errore nel salvare thresholds in localStorage:', error);
        }
      }
      update(state => ({ ...state, baselineThresholds: thresholds }));
    },
    
    // Analisi
    setAnalyzing: (isAnalyzing) => update(state => ({ ...state, isAnalyzing })),
    
    // UI feedback
    setLoading: (loading) => update(state => ({ ...state, loading })),
    setError: (error) => update(state => ({ ...state, error, loading: false })),
    setMessage: (message) => update(state => ({ ...state, message })),
    clearMessages: () => update(state => ({ ...state, error: null, message: null })),
    
    // Funzioni helper per pulire lo stato quando si torna indietro
    clearResults: () => update(state => ({ ...state, results: null, isAnalyzing: false })),
    
    clearCalibration: () => update(state => ({ ...state, speed: null, fps: null })),
    
    clearVideoData: () => update(state => {
      // Revoca URL video singolo
      if (state.videoUrl) {
        URL.revokeObjectURL(state.videoUrl);
      }
      // Revoca URL video baseline
      if (state.baselineVideoUrls && state.baselineVideoUrls.length > 0) {
        state.baselineVideoUrls.forEach(url => {
          if (url) URL.revokeObjectURL(url);
        });
      }
      return {
        ...state,
        videoFile: null,
        videoUrl: null,
        baselineVideos: [],
        baselineVideoUrls: [],
        recordedBlob: null,
        isRecording: false
      };
    }),
    
    clearVideoMethod: () => update(state => ({ ...state, videoMethod: null })),
    
    clearViewType: () => update(state => ({ ...state, viewType: 'posterior' }))
  };
}

export const analysisStore = createAnalysisStore();