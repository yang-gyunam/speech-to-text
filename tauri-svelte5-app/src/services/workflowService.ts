import { fileService } from './fileService';
import { processingService } from './processingService';
import { tauriService } from './tauriService';
import type { 
  AudioFile, 
  TranscriptionResult, 
  AppSettings, 
  ProcessingProgress,
  ErrorState,
  AppView 
} from '../types';

export interface WorkflowCallbacks {
  onViewChange?: (view: AppView) => void;
  onFilesAdded?: (files: AudioFile[]) => void;
  onProcessingStart?: () => void;
  onProgress?: (progress: ProcessingProgress) => void;
  onComplete?: (result: TranscriptionResult) => void;
  onError?: (error: ErrorState) => void;
  onCancel?: () => void;
}

export interface WorkflowState {
  currentView: AppView;
  files: AudioFile[];
  currentResult: TranscriptionResult | null;
  isProcessing: boolean;
  error: ErrorState | null;
}

export class WorkflowService {
  private state: WorkflowState = {
    currentView: 'upload',
    files: [],
    currentResult: null,
    isProcessing: false,
    error: null
  };

  private callbacks: WorkflowCallbacks = {};
  private currentJobId: string | null = null;

  /**
   * Initialize the workflow service with callbacks
   */
  initialize(callbacks: WorkflowCallbacks): void {
    this.callbacks = callbacks;
  }

  /**
   * Validate a single file without starting processing
   */
  async validateSingleFile(filePath: string): Promise<AudioFile> {
    return await tauriService.validateAudioFile(filePath);
  }

  /**
   * Handle file path selection from Tauri dialog
   */
  async handleFilePathSelection(filePaths: string[], settings: AppSettings): Promise<void> {
    try {
      this.clearError();

      // Processing file paths

      // Validate files using backend one by one for better error reporting
      const audioFiles: AudioFile[] = [];
      const errors: string[] = [];

      for (const filePath of filePaths) {
        try {
          // Validating file
          const audioFile = await tauriService.validateAudioFile(filePath);
          audioFiles.push(audioFile);
          // File validated successfully
        } catch (error) {
          console.error('File validation failed:', filePath, error);
          errors.push(`${filePath}: ${error}`);
        }
      }
      
      if (audioFiles.length === 0) {
        this.setError({
          type: 'file',
          message: 'No valid audio files found',
          details: errors.length > 0 ? errors.join('\n') : 'Please select supported audio files (.m4a, .wav, .mp3, .aac, .flac)',
          recoverable: true
        });
        return;
      }

      // Show warnings for failed files but continue with valid ones
      if (errors.length > 0) {
        console.warn('Some files failed validation:', errors);
      }

      // Update state with valid files
      this.state.files = audioFiles;
      this.callbacks.onFilesAdded?.(audioFiles);

      // Valid files processed

      // Determine workflow path - don't auto-start processing
      if (audioFiles.length === 1) {
        // Single file - show ready to process state
        // Single file ready for processing
        this.callbacks.onViewChange?.('upload'); // Stay on upload view with start button
      } else {
        // Multiple files - switch to batch view
        // Switching to batch view
        this.callbacks.onViewChange?.('batch');
      }
    } catch (error) {
      console.error('handleFilePathSelection error:', error);
      this.setError({
        type: 'file',
        message: 'Failed to validate files',
        details: error instanceof Error ? error.message : 'Unknown error',
        recoverable: true
      });
    }
  }

  /**
   * Handle file selection from upload
   */
  async handleFileSelection(files: File[], settings: AppSettings): Promise<void> {
    try {
      this.clearError();

      // Validate files
      const validation = await fileService.validateFiles(files);
      
      if (validation.invalid.length > 0) {
        const errorMessages = validation.invalid.map(({ file, error }) => 
          `${file.name}: ${error}`
        ).join('\n');
        
        this.setError({
          type: 'file',
          message: `${validation.invalid.length} file(s) failed validation`,
          details: errorMessages,
          recoverable: true
        });
      }

      if (validation.valid.length === 0) {
        this.setError({
          type: 'file',
          message: 'No valid audio files found',
          details: 'Please select supported audio files (.m4a, .wav, .mp3, .aac, .flac)',
          recoverable: true
        });
        return;
      }

      // Update state with valid files
      this.state.files = validation.valid;
      this.callbacks.onFilesAdded?.(validation.valid);

      // Determine workflow path
      if (validation.valid.length === 1) {
        // Single file - start processing immediately
        await this.startSingleFileProcessing(files[0], settings);
      } else {
        // Multiple files - go to batch view
        this.setView('batch');
      }
    } catch (error) {
      this.setError({
        type: 'system',
        message: 'Failed to process file selection',
        details: error instanceof Error ? error.message : 'Unknown error',
        recoverable: true
      });
    }
  }

  /**
   * Start single file processing workflow
   */
  async startSingleFileProcessing(file: File | AudioFile, settings: AppSettings, originalFilePath?: string): Promise<void> {
    try {
      this.clearError();
      this.state.isProcessing = true;
      this.setView('processing');
      this.callbacks.onProcessingStart?.();

      // Start processing with callbacks
      const result = await processingService.processSingleFile(file, settings, {
        onProgress: (progress) => {
          this.callbacks.onProgress?.(progress);
        },
        onComplete: (result) => {
          this.handleProcessingComplete(result);
        },
        onError: (error) => {
          this.handleProcessingError(error);
        }
      }, originalFilePath);

      // If we get here, processing completed successfully
      this.handleProcessingComplete(result);
    } catch (error) {
      this.handleProcessingError(error as Error);
    }
  }

  /**
   * Start batch processing workflow
   */
  async startBatchProcessing(files: File[], settings: AppSettings): Promise<void> {
    try {
      this.clearError();
      this.state.isProcessing = true;
      this.setView('processing');
      this.callbacks.onProcessingStart?.();

      // Start batch processing
      const jobId = await processingService.processBatchFiles(files, settings, {
        onProgress: (progress) => {
          this.callbacks.onProgress?.(progress);
        },
        onComplete: (result) => {
          // For batch processing, we might handle results differently
          // For now, we'll just handle the last result
          this.handleProcessingComplete(result);
        },
        onError: (error) => {
          this.handleProcessingError(error);
        }
      });

      this.currentJobId = jobId;
    } catch (error) {
      this.handleProcessingError(error as Error);
    }
  }

  /**
   * Cancel current processing
   */
  async cancelProcessing(): Promise<void> {
    try {
      if (this.currentJobId) {
        const success = await processingService.cancelProcessing(this.currentJobId);
        if (success) {
          this.handleProcessingCancel();
        } else {
          this.setError({
            type: 'system',
            message: 'Failed to cancel processing',
            details: 'The processing job could not be cancelled',
            recoverable: false
          });
        }
      } else {
        this.handleProcessingCancel();
      }
    } catch (error) {
      this.setError({
        type: 'system',
        message: 'Error cancelling processing',
        details: error instanceof Error ? error.message : 'Unknown error',
        recoverable: false
      });
    }
  }

  /**
   * Handle successful processing completion
   */
  private handleProcessingComplete(result: TranscriptionResult): void {
    this.state.isProcessing = false;
    this.state.currentResult = result;
    this.currentJobId = null;
    this.setView('results');
    this.callbacks.onComplete?.(result);
  }

  /**
   * Handle processing error
   */
  private handleProcessingError(error: Error): void {
    this.state.isProcessing = false;
    this.currentJobId = null;
    
    this.setError({
      type: 'processing',
      message: 'Processing failed',
      details: error.message,
      recoverable: true
    });
    
    // Return to upload view on error
    this.setView('upload');
  }

  /**
   * Handle processing cancellation
   */
  private handleProcessingCancel(): void {
    this.state.isProcessing = false;
    this.currentJobId = null;
    this.setView('upload');
    this.callbacks.onCancel?.();
  }

  /**
   * Reset workflow to initial state
   */
  resetWorkflow(): void {
    this.state = {
      currentView: 'upload',
      files: [],
      currentResult: null,
      isProcessing: false,
      error: null
    };
    this.currentJobId = null;
    this.setView('upload');
  }

  /**
   * Save edited transcription result
   */
  async saveTranscriptionResult(content: string, result: TranscriptionResult): Promise<void> {
    try {
      await fileService.saveTranscriptionResult(content, result.outputPath);
    } catch (error) {
      this.setError({
        type: 'system',
        message: 'Failed to save transcription',
        details: error instanceof Error ? error.message : 'Unknown error',
        recoverable: true
      });
    }
  }

  /**
   * Set current view
   */
  private setView(view: AppView): void {
    this.state.currentView = view;
    this.callbacks.onViewChange?.(view);
  }

  /**
   * Set error state
   */
  private setError(error: ErrorState): void {
    this.state.error = error;
    this.callbacks.onError?.(error);
  }

  /**
   * Clear error state
   */
  private clearError(): void {
    this.state.error = null;
  }

  /**
   * Get current workflow state
   */
  getState(): WorkflowState {
    return { ...this.state };
  }

  /**
   * Check if processing can be cancelled
   */
  canCancelProcessing(): boolean {
    return this.state.isProcessing && this.currentJobId !== null;
  }

  /**
   * Cleanup resources
   */
  cleanup(): void {
    processingService.cleanup();
    this.currentJobId = null;
  }
}

// Singleton instance
export const workflowService = new WorkflowService();