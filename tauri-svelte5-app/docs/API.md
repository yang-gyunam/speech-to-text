# API Reference

This document provides comprehensive documentation for all Tauri commands, events, and data structures used in the Speech to Text application.

## Table of Contents

- [Commands](#commands)
  - [File Processing](#file-processing)
  - [Settings Management](#settings-management)
  - [System Integration](#system-integration)
  - [Diagnostics](#diagnostics)
- [Events](#events)
- [Data Types](#data-types)
- [Error Handling](#error-handling)
- [Usage Examples](#usage-examples)

## Commands

### File Processing

#### `process_audio_file`

Processes a single audio file and returns the transcription result.

**Signature:**
```rust
#[tauri::command]
async fn process_audio_file(
    file_path: String,
    settings: AppSettings,
    window: tauri::Window,
) -> Result<TranscriptionResult, String>
```

**Parameters:**
- `file_path` (string): Absolute path to the audio file
- `settings` (AppSettings): Processing configuration
- `window` (tauri::Window): Window handle for progress events

**Returns:**
- `TranscriptionResult`: Complete transcription with metadata
- `String`: Error message if processing fails

**TypeScript Usage:**
```typescript
import { invoke } from '@tauri-apps/api/tauri';

const result = await invoke<TranscriptionResult>('process_audio_file', {
  filePath: '/Users/john/audio.m4a',
  settings: {
    language: 'korean',
    modelSize: 'base',
    outputDirectory: '/Users/john/Documents',
    includeMetadata: true,
    autoSave: false,
    theme: 'system'
  }
});
```

**Events Emitted:**
- `processing_started`: When processing begins
- `processing_progress`: Progress updates during processing
- `processing_completed`: When processing finishes
- `processing_error`: If an error occurs

---

#### `process_batch_files`

Processes multiple audio files in sequence with progress tracking.

**Signature:**
```rust
#[tauri::command]
async fn process_batch_files(
    file_paths: Vec<String>,
    settings: AppSettings,
    window: tauri::Window,
) -> Result<Vec<TranscriptionResult>, String>
```

**Parameters:**
- `file_paths` (string[]): Array of absolute file paths
- `settings` (AppSettings): Processing configuration
- `window` (tauri::Window): Window handle for progress events

**Returns:**
- `Vec<TranscriptionResult>`: Array of transcription results
- `String`: Error message if batch processing fails

**TypeScript Usage:**
```typescript
const results = await invoke<TranscriptionResult[]>('process_batch_files', {
  filePaths: [
    '/Users/john/audio1.m4a',
    '/Users/john/audio2.wav',
    '/Users/john/audio3.mp3'
  ],
  settings: currentSettings
});
```

**Events Emitted:**
- `batch_started`: When batch processing begins
- `batch_file_started`: When each file starts processing
- `batch_file_completed`: When each file completes
- `batch_progress`: Overall batch progress
- `batch_completed`: When entire batch finishes

---

#### `cancel_processing`

Cancels the currently running processing operation.

**Signature:**
```rust
#[tauri::command]
async fn cancel_processing() -> Result<(), String>
```

**Parameters:** None

**Returns:**
- `()`: Success
- `String`: Error message if cancellation fails

**TypeScript Usage:**
```typescript
await invoke('cancel_processing');
```

**Events Emitted:**
- `processing_cancelled`: When processing is successfully cancelled

---

#### `get_processing_status`

Gets the current processing status and progress information.

**Signature:**
```rust
#[tauri::command]
async fn get_processing_status() -> Result<Option<ProcessingStatus>, String>
```

**Parameters:** None

**Returns:**
- `Option<ProcessingStatus>`: Current processing status or null if not processing
- `String`: Error message if status retrieval fails

**TypeScript Usage:**
```typescript
const status = await invoke<ProcessingStatus | null>('get_processing_status');
if (status) {
  console.log(`Processing ${status.currentFile} - ${status.progress}%`);
}
```

### Settings Management

#### `load_settings`

Loads application settings from the configuration file.

**Signature:**
```rust
#[tauri::command]
async fn load_settings() -> Result<AppSettings, String>
```

**Parameters:** None

**Returns:**
- `AppSettings`: Current application settings
- `String`: Error message if loading fails

**TypeScript Usage:**
```typescript
const settings = await invoke<AppSettings>('load_settings');
```

---

#### `save_settings`

Saves application settings to the configuration file.

**Signature:**
```rust
#[tauri::command]
async fn save_settings(settings: AppSettings) -> Result<(), String>
```

**Parameters:**
- `settings` (AppSettings): Settings to save

**Returns:**
- `()`: Success
- `String`: Error message if saving fails

**TypeScript Usage:**
```typescript
await invoke('save_settings', { settings: newSettings });
```

---

#### `reset_settings`

Resets all settings to their default values.

**Signature:**
```rust
#[tauri::command]
async fn reset_settings() -> Result<AppSettings, String>
```

**Parameters:** None

**Returns:**
- `AppSettings`: Default settings
- `String`: Error message if reset fails

**TypeScript Usage:**
```typescript
const defaultSettings = await invoke<AppSettings>('reset_settings');
```

### System Integration

#### `select_directory`

Opens a directory selection dialog and returns the chosen path.

**Signature:**
```rust
#[tauri::command]
async fn select_directory(title: Option<String>) -> Result<Option<String>, String>
```

**Parameters:**
- `title` (string, optional): Dialog title

**Returns:**
- `Option<String>`: Selected directory path or null if cancelled
- `String`: Error message if dialog fails

**TypeScript Usage:**
```typescript
const directory = await invoke<string | null>('select_directory', {
  title: 'Choose Output Directory'
});
```

---

#### `reveal_in_finder`

Reveals a file or directory in Finder (macOS).

**Signature:**
```rust
#[tauri::command]
async fn reveal_in_finder(path: String) -> Result<(), String>
```

**Parameters:**
- `path` (string): Absolute path to reveal

**Returns:**
- `()`: Success
- `String`: Error message if reveal fails

**TypeScript Usage:**
```typescript
await invoke('reveal_in_finder', { path: '/Users/john/transcription.txt' });
```

---

#### `get_supported_formats`

Returns a list of supported audio file formats.

**Signature:**
```rust
#[tauri::command]
async fn get_supported_formats() -> Result<Vec<AudioFormat>, String>
```

**Parameters:** None

**Returns:**
- `Vec<AudioFormat>`: Array of supported formats with details
- `String`: Error message if retrieval fails

**TypeScript Usage:**
```typescript
const formats = await invoke<AudioFormat[]>('get_supported_formats');
```

---

#### `validate_file`

Validates an audio file for processing compatibility.

**Signature:**
```rust
#[tauri::command]
async fn validate_file(file_path: String) -> Result<FileValidationResult, String>
```

**Parameters:**
- `file_path` (string): Path to the file to validate

**Returns:**
- `FileValidationResult`: Validation result with file information
- `String`: Error message if validation fails

**TypeScript Usage:**
```typescript
const validation = await invoke<FileValidationResult>('validate_file', {
  filePath: '/Users/john/audio.m4a'
});

if (validation.isValid) {
  console.log(`File is valid: ${validation.fileInfo.duration}s`);
} else {
  console.error(`Validation failed: ${validation.error}`);
}
```

### Diagnostics

#### `run_system_diagnostics`

Runs comprehensive system diagnostics and returns the results.

**Signature:**
```rust
#[tauri::command]
async fn run_system_diagnostics() -> Result<SystemDiagnostics, String>
```

**Parameters:** None

**Returns:**
- `SystemDiagnostics`: Complete system diagnostic information
- `String`: Error message if diagnostics fail

**TypeScript Usage:**
```typescript
const diagnostics = await invoke<SystemDiagnostics>('run_system_diagnostics');
console.log(`Available memory: ${diagnostics.memory.available}MB`);
```

---

#### `get_performance_metrics`

Gets current performance metrics and statistics.

**Signature:**
```rust
#[tauri::command]
async fn get_performance_metrics() -> Result<PerformanceMetrics, String>
```

**Parameters:** None

**Returns:**
- `PerformanceMetrics`: Current performance statistics
- `String`: Error message if retrieval fails

**TypeScript Usage:**
```typescript
const metrics = await invoke<PerformanceMetrics>('get_performance_metrics');
```

---

#### `clear_cache`

Clears application cache and temporary files.

**Signature:**
```rust
#[tauri::command]
async fn clear_cache() -> Result<CacheClearResult, String>
```

**Parameters:** None

**Returns:**
- `CacheClearResult`: Information about cleared cache
- `String`: Error message if clearing fails

**TypeScript Usage:**
```typescript
const result = await invoke<CacheClearResult>('clear_cache');
console.log(`Cleared ${result.bytesFreed} bytes`);
```

## Events

### Processing Events

#### `processing_started`

Emitted when audio processing begins.

**Payload:**
```typescript
interface ProcessingStartedEvent {
  fileId: string;
  fileName: string;
  filePath: string;
  estimatedDuration?: number;
}
```

**Usage:**
```typescript
import { listen } from '@tauri-apps/api/event';

const unlisten = await listen<ProcessingStartedEvent>('processing_started', (event) => {
  console.log(`Started processing: ${event.payload.fileName}`);
});
```

---

#### `processing_progress`

Emitted during processing to provide progress updates.

**Payload:**
```typescript
interface ProcessingProgressEvent {
  fileId: string;
  progress: number; // 0.0 to 1.0
  stage: ProcessingStage;
  timeElapsed: number; // milliseconds
  estimatedTimeRemaining?: number; // milliseconds
  currentOperation?: string;
}
```

**Usage:**
```typescript
const unlisten = await listen<ProcessingProgressEvent>('processing_progress', (event) => {
  const { progress, stage, timeElapsed } = event.payload;
  updateProgressBar(progress * 100);
  updateStageIndicator(stage);
});
```

---

#### `processing_completed`

Emitted when processing completes successfully.

**Payload:**
```typescript
interface ProcessingCompletedEvent {
  fileId: string;
  result: TranscriptionResult;
  processingTime: number; // milliseconds
}
```

**Usage:**
```typescript
const unlisten = await listen<ProcessingCompletedEvent>('processing_completed', (event) => {
  displayTranscriptionResult(event.payload.result);
});
```

---

#### `processing_error`

Emitted when processing encounters an error.

**Payload:**
```typescript
interface ProcessingErrorEvent {
  fileId: string;
  error: string;
  errorCode?: string;
  recoverable: boolean;
}
```

**Usage:**
```typescript
const unlisten = await listen<ProcessingErrorEvent>('processing_error', (event) => {
  showErrorMessage(event.payload.error, event.payload.recoverable);
});
```

### Batch Processing Events

#### `batch_started`

Emitted when batch processing begins.

**Payload:**
```typescript
interface BatchStartedEvent {
  batchId: string;
  totalFiles: number;
  estimatedTotalTime?: number;
}
```

---

#### `batch_file_started`

Emitted when processing starts for each file in a batch.

**Payload:**
```typescript
interface BatchFileStartedEvent {
  batchId: string;
  fileId: string;
  fileName: string;
  fileIndex: number;
  totalFiles: number;
}
```

---

#### `batch_progress`

Emitted to provide overall batch progress updates.

**Payload:**
```typescript
interface BatchProgressEvent {
  batchId: string;
  completedFiles: number;
  totalFiles: number;
  overallProgress: number; // 0.0 to 1.0
  currentFile?: string;
  estimatedTimeRemaining?: number;
}
```

---

#### `batch_completed`

Emitted when batch processing completes.

**Payload:**
```typescript
interface BatchCompletedEvent {
  batchId: string;
  results: TranscriptionResult[];
  successCount: number;
  errorCount: number;
  totalProcessingTime: number;
}
```

### System Events

#### `settings_changed`

Emitted when application settings are updated.

**Payload:**
```typescript
interface SettingsChangedEvent {
  previousSettings: AppSettings;
  newSettings: AppSettings;
  changedFields: string[];
}
```

---

#### `error_occurred`

Emitted when a system-level error occurs.

**Payload:**
```typescript
interface ErrorOccurredEvent {
  error: string;
  errorCode?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: number;
  context?: Record<string, any>;
}
```

## Data Types

### Core Types

#### `AppSettings`

Application configuration settings.

```typescript
interface AppSettings {
  language: string;
  modelSize: ModelSize;
  outputDirectory: string;
  includeMetadata: boolean;
  autoSave: boolean;
  theme: Theme;
  performance: PerformanceSettings;
  ui: UISettings;
}

type ModelSize = 'tiny' | 'base' | 'small' | 'medium' | 'large';
type Theme = 'light' | 'dark' | 'system';
```

#### `TranscriptionResult`

Result of audio transcription processing.

```typescript
interface TranscriptionResult {
  id: string;
  originalFile: AudioFileInfo;
  transcribedText: string;
  metadata: TranscriptionMetadata;
  outputPath?: string;
  processingTime: number; // milliseconds
  confidence?: number; // 0.0 to 1.0
  segments?: TranscriptionSegment[];
}
```

#### `AudioFileInfo`

Information about an audio file.

```typescript
interface AudioFileInfo {
  id: string;
  name: string;
  path: string;
  size: number; // bytes
  format: string;
  duration?: number; // seconds
  sampleRate?: number;
  channels?: number;
  bitRate?: number;
}
```

#### `TranscriptionMetadata`

Metadata associated with a transcription.

```typescript
interface TranscriptionMetadata {
  language: string;
  modelSize: ModelSize;
  processingDate: string; // ISO 8601
  audioInfo: AudioInfo;
  processingStats: ProcessingStats;
  qualityMetrics?: QualityMetrics;
}
```

#### `ProcessingStatus`

Current processing status information.

```typescript
interface ProcessingStatus {
  isProcessing: boolean;
  currentFile?: string;
  fileId?: string;
  progress: number; // 0.0 to 1.0
  stage: ProcessingStage;
  timeElapsed: number; // milliseconds
  estimatedTimeRemaining?: number; // milliseconds
  queueLength: number;
}

type ProcessingStage = 
  | 'initializing'
  | 'loading_model'
  | 'preprocessing'
  | 'transcribing'
  | 'postprocessing'
  | 'saving'
  | 'completed'
  | 'error';
```

### System Types

#### `SystemDiagnostics`

System diagnostic information.

```typescript
interface SystemDiagnostics {
  system: SystemInfo;
  memory: MemoryInfo;
  storage: StorageInfo;
  performance: PerformanceInfo;
  dependencies: DependencyInfo[];
  recommendations: string[];
}

interface SystemInfo {
  os: string;
  version: string;
  arch: string;
  cpuCount: number;
  cpuModel: string;
}

interface MemoryInfo {
  total: number; // bytes
  available: number; // bytes
  used: number; // bytes
  percentage: number; // 0.0 to 100.0
}
```

#### `AudioFormat`

Supported audio format information.

```typescript
interface AudioFormat {
  extension: string;
  mimeType: string;
  description: string;
  maxFileSize?: number; // bytes
  recommendedFor: string[];
  qualityRating: number; // 1-5 stars
}
```

#### `FileValidationResult`

Result of file validation.

```typescript
interface FileValidationResult {
  isValid: boolean;
  fileInfo?: AudioFileInfo;
  error?: string;
  warnings?: string[];
  recommendations?: string[];
}
```

### Performance Types

#### `PerformanceMetrics`

Performance statistics and metrics.

```typescript
interface PerformanceMetrics {
  filesProcessed: number;
  totalProcessingTime: number; // milliseconds
  averageProcessingTime: number; // milliseconds
  successRate: number; // 0.0 to 1.0
  errorRate: number; // 0.0 to 1.0
  memoryUsage: MemoryUsage;
  cpuUsage: number; // 0.0 to 100.0
  diskUsage: DiskUsage;
}

interface MemoryUsage {
  current: number; // bytes
  peak: number; // bytes
  average: number; // bytes
}

interface DiskUsage {
  cacheSize: number; // bytes
  tempFiles: number;
  outputFiles: number;
}
```

## Error Handling

### Error Types

All commands return errors as strings, but the application defines structured error types internally:

```typescript
interface AppError {
  code: string;
  message: string;
  details?: string;
  recoverable: boolean;
  suggestions?: string[];
}

// Common error codes
type ErrorCode = 
  | 'FILE_NOT_FOUND'
  | 'UNSUPPORTED_FORMAT'
  | 'INSUFFICIENT_MEMORY'
  | 'PROCESSING_FAILED'
  | 'SETTINGS_ERROR'
  | 'SYSTEM_ERROR'
  | 'NETWORK_ERROR'
  | 'PERMISSION_DENIED';
```

### Error Handling Patterns

#### Command Error Handling

```typescript
try {
  const result = await invoke<TranscriptionResult>('process_audio_file', {
    filePath: selectedFile.path,
    settings: currentSettings
  });
  
  // Handle success
  setTranscriptionResult(result);
  
} catch (error) {
  // Handle error
  console.error('Processing failed:', error);
  
  // Parse error if it's a structured error
  try {
    const appError: AppError = JSON.parse(error as string);
    showErrorDialog(appError.message, appError.suggestions);
  } catch {
    // Fallback for simple string errors
    showErrorDialog(error as string);
  }
}
```

#### Event Error Handling

```typescript
const unlisten = await listen<ProcessingErrorEvent>('processing_error', (event) => {
  const { error, recoverable, errorCode } = event.payload;
  
  if (recoverable) {
    showRetryDialog(error);
  } else {
    showFatalErrorDialog(error);
  }
  
  // Log error for debugging
  console.error(`Processing error [${errorCode}]:`, error);
});
```

## Usage Examples

### Complete File Processing Workflow

```typescript
import { invoke } from '@tauri-apps/api/tauri';
import { listen } from '@tauri-apps/api/event';

class AudioProcessor {
  private progressCallback?: (progress: number) => void;
  private unlistenProgress?: () => void;
  
  async processFile(filePath: string, settings: AppSettings): Promise<TranscriptionResult> {
    // Set up progress listening
    this.unlistenProgress = await listen<ProcessingProgressEvent>(
      'processing_progress',
      (event) => {
        this.progressCallback?.(event.payload.progress);
      }
    );
    
    try {
      // Validate file first
      const validation = await invoke<FileValidationResult>('validate_file', {
        filePath
      });
      
      if (!validation.isValid) {
        throw new Error(validation.error || 'File validation failed');
      }
      
      // Start processing
      const result = await invoke<TranscriptionResult>('process_audio_file', {
        filePath,
        settings
      });
      
      return result;
      
    } finally {
      // Clean up event listener
      this.unlistenProgress?.();
    }
  }
  
  setProgressCallback(callback: (progress: number) => void) {
    this.progressCallback = callback;
  }
  
  async cancelProcessing() {
    await invoke('cancel_processing');
  }
}

// Usage
const processor = new AudioProcessor();
processor.setProgressCallback((progress) => {
  console.log(`Progress: ${Math.round(progress * 100)}%`);
});

const result = await processor.processFile('/path/to/audio.m4a', settings);
console.log('Transcription:', result.transcribedText);
```

### Batch Processing with Queue Management

```typescript
class BatchProcessor {
  private batchId?: string;
  private onBatchProgress?: (progress: BatchProgressEvent) => void;
  
  async processBatch(filePaths: string[], settings: AppSettings): Promise<TranscriptionResult[]> {
    // Listen for batch events
    const unlistenBatchProgress = await listen<BatchProgressEvent>(
      'batch_progress',
      (event) => {
        this.onBatchProgress?.(event.payload);
      }
    );
    
    const unlistenBatchCompleted = await listen<BatchCompletedEvent>(
      'batch_completed',
      (event) => {
        console.log(`Batch completed: ${event.payload.successCount}/${event.payload.totalFiles} files`);
      }
    );
    
    try {
      const results = await invoke<TranscriptionResult[]>('process_batch_files', {
        filePaths,
        settings
      });
      
      return results;
      
    } finally {
      unlistenBatchProgress();
      unlistenBatchCompleted();
    }
  }
  
  setBatchProgressCallback(callback: (progress: BatchProgressEvent) => void) {
    this.onBatchProgress = callback;
  }
}
```

### Settings Management

```typescript
class SettingsManager {
  private currentSettings?: AppSettings;
  
  async loadSettings(): Promise<AppSettings> {
    this.currentSettings = await invoke<AppSettings>('load_settings');
    return this.currentSettings;
  }
  
  async updateSettings(updates: Partial<AppSettings>): Promise<void> {
    if (!this.currentSettings) {
      await this.loadSettings();
    }
    
    const newSettings = { ...this.currentSettings!, ...updates };
    
    await invoke('save_settings', { settings: newSettings });
    this.currentSettings = newSettings;
    
    // Settings change event will be emitted automatically
  }
  
  async resetToDefaults(): Promise<AppSettings> {
    this.currentSettings = await invoke<AppSettings>('reset_settings');
    return this.currentSettings;
  }
  
  getCurrentSettings(): AppSettings | undefined {
    return this.currentSettings;
  }
}
```

This API reference provides comprehensive documentation for all available commands, events, and data types in the Speech to Text application. Use this as a reference when developing frontend features or integrating with the Tauri backend.