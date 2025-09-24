import { writable } from 'svelte/store';
import type {
  AudioFile,
  TranscriptionResult,
  ProcessingJob,
  AppSettings,
  AppView,
  ProcessingProgress,
  ErrorState,
  ErrorLog,
  DiagnosticResult
} from '../types';
import type { ToastError } from '../components/error/ErrorToast';

interface AppStore {
  // State
  currentView: AppView;
  files: AudioFile[];
  currentProcessing: ProcessingJob | null;
  results: TranscriptionResult[];
  settings: AppSettings;
  processingProgress: ProcessingProgress | null;
  error: ErrorState | null;

  // Error handling state
  errorLogs: ErrorLog[];
  toastErrors: ToastError[];
  diagnostics: DiagnosticResult[];
}

// Default settings
const defaultSettings: AppSettings = {
  language: 'ko',
  modelSize: 'base',
  outputDirectory: '',
  includeMetadata: true,
  autoSave: false,
  theme: 'system',
  // Advanced performance options
  maxConcurrentJobs: 2,
  enableGpuAcceleration: false,
  memoryOptimization: true,
  // Advanced processing options
  enableVoiceActivityDetection: true,
  noiseReduction: false,
  outputFormat: 'txt',
  // UI preferences
  compactMode: false,
  showAdvancedOptions: false,
  enableNotifications: true,
  autoCheckUpdates: true,
};

// Initial state
const initialState: AppStore = {
  currentView: 'upload',
  files: [],
  currentProcessing: null,
  results: [],
  settings: defaultSettings,
  processingProgress: null,
  error: null,

  // Error handling state
  errorLogs: [],
  toastErrors: [],
  diagnostics: [],
};

// Create writable store
const { subscribe, set, update } = writable<AppStore>(initialState);

// Actions
export const appStore = {
  subscribe,

  // View actions
  setCurrentView: (view: AppView) => update(state => ({ ...state, currentView: view })),

  // File actions
  addFiles: (newFiles: File[]) => {
    update(state => {
      const audioFiles: AudioFile[] = newFiles.map((file, index) => ({
        id: `${Date.now()}-${index}`,
        name: file.name,
        path: '', // Will be set when file is processed
        size: file.size,
        format: file.name.split('.').pop()?.toLowerCase() || '',
        status: 'pending'
      }));

      return {
        ...state,
        files: [...state.files, ...audioFiles],
        error: null
      };
    });
  },

  removeFile: (id: string) => update(state => ({
    ...state,
    files: state.files.filter(file => file.id !== id)
  })),

  clearFiles: () => update(state => ({ ...state, files: [] })),

  // Processing actions
  startProcessing: (fileIds: string[]) => {
    update(state => {
      const filesToProcess = state.files.filter(file => fileIds.includes(file.id));

      if (filesToProcess.length === 0) return state;

      const processingJob: ProcessingJob = {
        id: `job-${Date.now()}`,
        files: filesToProcess,
        currentFileIndex: 0,
        progress: 0,
        stage: 'initializing',
        startTime: Date.now()
      };

      return {
        ...state,
        currentProcessing: processingJob,
        currentView: 'processing',
        error: null
      };
    });
  },

  updateProgress: (progress: ProcessingProgress) => update(state => ({
    ...state,
    processingProgress: progress,
    currentProcessing: state.currentProcessing ? {
      ...state.currentProcessing,
      progress: progress.progress,
      stage: progress.stage
    } : null
  })),

  completeProcessing: () => update(state => ({
    ...state,
    currentProcessing: null,
    processingProgress: null,
    currentView: 'results'
  })),

  cancelProcessing: () => update(state => ({
    ...state,
    currentProcessing: null,
    processingProgress: null,
    currentView: 'upload'
  })),

  // Result actions
  addResult: (result: TranscriptionResult) => update(state => ({
    ...state,
    results: [...state.results, result]
  })),

  // Settings actions
  updateSettings: (newSettings: Partial<AppSettings>) => update(state => ({
    ...state,
    settings: { ...state.settings, ...newSettings }
  })),

  // Error actions
  setError: (error: ErrorState | null) => update(state => ({ ...state, error })),
  clearError: () => update(state => ({ ...state, error: null })),

  // Error handling actions
  logError: (logData: Omit<ErrorLog, 'id' | 'timestamp'>) => {
    update(state => {
      const log: ErrorLog = {
        ...logData,
        id: `log-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date()
      };

      return {
        ...state,
        errorLogs: [log, ...state.errorLogs].slice(0, 1000) // Keep last 1000 logs
      };
    });
  },

  clearErrorLogs: () => update(state => ({ ...state, errorLogs: [] })),

  addToastError: (toastData: Omit<ToastError, 'id'>) => {
    update(state => {
      const toast: ToastError = {
        ...toastData,
        id: `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      };

      return {
        ...state,
        toastErrors: [...state.toastErrors, toast]
      };
    });
  },

  dismissToastError: (id: string) => update(state => ({
    ...state,
    toastErrors: state.toastErrors.filter(toast => toast.id !== id)
  })),

  clearToastErrors: () => update(state => ({ ...state, toastErrors: [] })),

  setDiagnostics: (diagnostics: DiagnosticResult[]) => update(state => ({ ...state, diagnostics })),

  createErrorFromException: (error: Error, context = {}) => {
    const errorState: ErrorState = {
      id: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type: 'system',
      severity: 'high',
      message: error.message || 'Unknown error occurred',
      details: error.stack,
      recoverable: true,
      timestamp: new Date(),
      context,
      technicalInfo: {
        stackTrace: error.stack,
        errorCode: error.name
      }
    };

    // Also log the error
    appStore.logError({
      level: 'error',
      category: 'system',
      message: error.message,
      details: {
        stack: error.stack,
        name: error.name,
        context
      }
    });

    return errorState;
  }
};