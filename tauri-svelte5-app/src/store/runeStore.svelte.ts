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

// Create reactive state using Svelte 5 runes
let currentViewState = $state<AppView>('upload');
let filesState = $state<AudioFile[]>([]);
let currentProcessingState = $state<ProcessingJob | null>(null);
let resultsState = $state<TranscriptionResult[]>([]);
let settingsState = $state<AppSettings>(defaultSettings);
let processingProgressState = $state<ProcessingProgress | null>(null);
let errorState = $state<ErrorState | null>(null);

// Error handling state
let errorLogsState = $state<ErrorLog[]>([]);
let toastErrorsState = $state<ToastError[]>([]);
let diagnosticsState = $state<DiagnosticResult[]>([]);

// Export getter functions for state access
export function getCurrentView() { return currentViewState; }
export function getFiles() { return filesState; }
export function getCurrentProcessing() { return currentProcessingState; }
export function getResults() { return resultsState; }
export function getSettings() { return settingsState; }
export function getProcessingProgress() { return processingProgressState; }
export function getError() { return errorState; }
export function getErrorLogs() { return errorLogsState; }
export function getToastErrors() { return toastErrorsState; }
export function getDiagnostics() { return diagnosticsState; }

// Actions
export const actions = {
  // View actions
  setCurrentView(view: AppView) {
    currentViewState = view;
  },

  // File actions
  addFiles(newFiles: File[]) {
    const audioFiles: AudioFile[] = newFiles.map((file, index) => ({
      id: `${Date.now()}-${index}`,
      name: file.name,
      path: '', // Will be set when file is processed
      size: file.size,
      format: file.name.split('.').pop()?.toLowerCase() || '',
      status: 'pending'
    }));

    filesState.push(...audioFiles);
    errorState = null;
  },

  removeFile(id: string) {
    filesState = filesState.filter(file => file.id !== id);
  },

  clearFiles() {
    filesState = [];
  },

  // Processing actions
  startProcessing(fileIds: string[]) {
    const filesToProcess = filesState.filter(file => fileIds.includes(file.id));

    if (filesToProcess.length === 0) return;

    const processingJob: ProcessingJob = {
      id: `job-${Date.now()}`,
      files: filesToProcess,
      currentFileIndex: 0,
      progress: 0,
      stage: 'initializing',
      startTime: Date.now()
    };

    currentProcessingState = processingJob;
    currentViewState = 'processing';
    errorState = null;
  },

  updateProgress(progress: ProcessingProgress) {
    processingProgressState = progress;
    if (currentProcessingState) {
      currentProcessingState.progress = progress.progress;
      currentProcessingState.stage = progress.stage;
    }
  },

  completeProcessing() {
    currentProcessingState = null;
    processingProgressState = null;
    currentViewState = 'results';
  },

  cancelProcessing() {
    currentProcessingState = null;
    processingProgressState = null;
    currentViewState = 'upload';
  },

  // Result actions
  addResult(result: TranscriptionResult) {
    resultsState.push(result);
  },

  // Settings actions
  updateSettings(newSettings: Partial<AppSettings>) {
    settingsState = { ...settingsState, ...newSettings };
  },

  // Error actions
  setError(newError: ErrorState | null) {
    errorState = newError;
  },

  clearError() {
    errorState = null;
  },

  // Error handling actions
  logError(logData: Omit<ErrorLog, 'id' | 'timestamp'>) {
    const log: ErrorLog = {
      ...logData,
      id: `log-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date()
    };

    errorLogsState.unshift(log);
    // Keep last 1000 logs
    if (errorLogsState.length > 1000) {
      errorLogsState = errorLogsState.slice(0, 1000);
    }
  },

  clearErrorLogs() {
    errorLogsState = [];
  },

  addToastError(toastData: Omit<ToastError, 'id'>) {
    const toast: ToastError = {
      ...toastData,
      id: `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    };

    toastErrorsState.push(toast);
  },

  dismissToastError(id: string) {
    toastErrorsState = toastErrorsState.filter(toast => toast.id !== id);
  },

  clearToastErrors() {
    toastErrorsState = [];
  },

  setDiagnostics(newDiagnostics: DiagnosticResult[]) {
    diagnosticsState = newDiagnostics;
  },

  createErrorFromException(errorObj: Error, context = {}): ErrorState {
    const errorState: ErrorState = {
      id: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type: 'system',
      severity: 'high',
      message: errorObj.message || 'Unknown error occurred',
      details: errorObj.stack,
      recoverable: true,
      timestamp: new Date(),
      context,
      technicalInfo: {
        stackTrace: errorObj.stack,
        errorCode: errorObj.name
      }
    };

    // Also log the error
    this.logError({
      level: 'error',
      category: 'system',
      message: errorObj.message,
      details: {
        stack: errorObj.stack,
        name: errorObj.name,
        context
      }
    });

    return errorState;
  }
};