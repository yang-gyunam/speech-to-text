// Core data types for the Speech to Text GUI application

export interface AudioFile {
  id: string;
  name: string;
  path: string;
  size: number;
  format: string;
  duration?: number;
  status: 'pending' | 'processing' | 'completed' | 'error';
}

export interface TranscriptionResult {
  id: string;
  originalFile: AudioFile;
  transcribedText: string;
  metadata: TranscriptionMetadata;
  outputPath: string;
  processingTime: number;
  confidence?: number;
}

export interface TranscriptionMetadata {
  language: string;
  modelSize: string;
  timestamp: string;
  audioInfo: {
    duration: number;
    sampleRate: number;
    channels: number;
  };
}

export interface ProcessingJob {
  id: string;
  files: AudioFile[];
  currentFileIndex: number;
  progress: number;
  stage: ProcessingStage;
  startTime: number;
  estimatedCompletion?: number;
  isCancelled?: boolean;
  canCancel?: boolean;
}

export type ProcessingStage = 
  | 'initializing'
  | 'loading_model'
  | 'preprocessing'
  | 'transcribing'
  | 'postprocessing'
  | 'saving';

export interface AppSettings {
  language: string;
  modelSize: 'tiny' | 'base' | 'small' | 'medium' | 'large';
  outputDirectory: string;
  includeMetadata: boolean;
  autoSave: boolean;
  theme: 'light' | 'dark' | 'system';
  // Advanced performance options
  maxConcurrentJobs: number;
  enableGpuAcceleration: boolean;
  memoryOptimization: boolean;
  // Advanced processing options
  enableVoiceActivityDetection: boolean;
  noiseReduction: boolean;
  outputFormat: 'txt' | 'srt' | 'vtt' | 'json';
  // UI preferences
  compactMode: boolean;
  showAdvancedOptions: boolean;
  enableNotifications: boolean;
  autoCheckUpdates: boolean;
}

export type AppView = 'upload' | 'processing' | 'results' | 'batch';

export interface ProcessingProgress {
  stage: ProcessingStage;
  progress: number;
  timestamp: Date;
  currentFile?: string;
  timeElapsed?: number;
  estimatedTimeRemaining?: number;
  jobId?: string;
  fileIndex?: number;
  totalFiles?: number;
  canCancel?: boolean;
  message?: string;
}

export interface ErrorState {
  id: string;
  type: 'file' | 'processing' | 'system' | 'network' | 'permission' | 'validation';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  details?: string;
  recoverable: boolean;
  timestamp: Date;
  context?: {
    fileName?: string;
    operation?: string;
    stage?: ProcessingStage;
    userAction?: string;
  };
  suggestions?: ErrorSuggestion[];
  technicalInfo?: {
    errorCode?: string;
    stackTrace?: string;
    systemInfo?: SystemInfo;
  };
}

export interface ErrorSuggestion {
  id: string;
  title: string;
  description: string;
  action?: 'retry' | 'restart' | 'contact_support' | 'check_system' | 'update_settings';
  actionData?: any;
  priority: 'primary' | 'secondary';
}

export interface SystemInfo {
  platform: string;
  version: string;
  memory: {
    total: number;
    available: number;
  };
  diskSpace: {
    available: number;
  };
  dependencies: {
    python: boolean;
    whisper: boolean;
    ffmpeg: boolean;
  };
}

export interface DiagnosticResult {
  id: string;
  name: string;
  status: 'pass' | 'fail' | 'warning' | 'info';
  message: string;
  details?: string;
  suggestions?: string[];
  timestamp: Date;
}

export interface ErrorLog {
  id: string;
  timestamp: Date;
  level: 'error' | 'warning' | 'info' | 'debug';
  category: string;
  message: string;
  details?: any;
  userId?: string;
  sessionId?: string;
}