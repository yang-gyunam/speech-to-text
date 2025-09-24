import { fileService } from './fileService';
import { processingService } from './processingService';
// import { tauriService } from './tauriService';
import type { 
  AudioFile, 
  TranscriptionResult, 
  AppSettings, 
  ProcessingProgress,
  ErrorState 
} from '../types';

export interface BatchFileStatus {
  file: AudioFile;
  status: 'pending' | 'processing' | 'completed' | 'error';
  result?: TranscriptionResult;
  error?: string;
  progress?: number;
}

export interface BatchProgress {
  totalFiles: number;
  completedFiles: number;
  failedFiles: number;
  currentFileIndex: number;
  overallProgress: number;
  currentFile?: string;
  estimatedTimeRemaining?: number;
}

export interface BatchCallbacks {
  onProgress?: (progress: BatchProgress) => void;
  onFileComplete?: (fileStatus: BatchFileStatus) => void;
  onFileError?: (fileStatus: BatchFileStatus) => void;
  onComplete?: (results: BatchFileStatus[]) => void;
  onError?: (error: ErrorState) => void;
}

export class BatchWorkflowService {
  private fileStatuses: Map<string, BatchFileStatus> = new Map();
  private currentJobId: string | null = null;
  private callbacks: BatchCallbacks = {};
  private startTime: number = 0;

  /**
   * Initialize batch processing with callbacks
   */
  initialize(callbacks: BatchCallbacks): void {
    this.callbacks = callbacks;
  }

  /**
   * Start batch processing workflow
   */
  async startBatchProcessing(files: File[], settings: AppSettings): Promise<string> {
    try {
      // Reset state
      this.fileStatuses.clear();
      this.startTime = Date.now();

      // Validate files first
      const validation = await fileService.validateFiles(files);
      
      if (validation.invalid.length > 0) {
        const errorMessages = validation.invalid.map(({ file, error }) => 
          `${file.name}: ${error}`
        ).join('\n');
        
        this.callbacks.onError?.({
          type: 'file',
          message: `${validation.invalid.length} file(s) failed validation`,
          details: errorMessages,
          recoverable: true
        });
      }

      if (validation.valid.length === 0) {
        throw new Error('No valid audio files found');
      }

      // Initialize file statuses
      validation.valid.forEach(audioFile => {
        this.fileStatuses.set(audioFile.id, {
          file: audioFile,
          status: 'pending'
        });
      });

      // Start batch processing
      // const filePaths = validation.valid.map(f => f.path);
      const jobId = await processingService.processBatchFiles(
        files, 
        settings, 
        {
          onProgress: (progress) => this.handleProgress(progress),
          onComplete: (result) => this.handleFileComplete(result),
          onError: (error) => this.handleError(error)
        }
      );

      this.currentJobId = jobId;
      return jobId;
    } catch (error) {
      this.callbacks.onError?.({
        type: 'processing',
        message: 'Failed to start batch processing',
        details: error instanceof Error ? error.message : 'Unknown error',
        recoverable: true
      });
      throw error;
    }
  }

  /**
   * Cancel batch processing
   */
  async cancelBatchProcessing(): Promise<boolean> {
    if (!this.currentJobId) {
      return false;
    }

    try {
      const success = await processingService.cancelProcessing(this.currentJobId);
      if (success) {
        this.currentJobId = null;
        // Mark all pending files as cancelled
        this.fileStatuses.forEach((status, id) => {
          if (status.status === 'pending' || status.status === 'processing') {
            this.fileStatuses.set(id, {
              ...status,
              status: 'error',
              error: 'Processing cancelled'
            });
          }
        });
      }
      return success;
    } catch (error) {
      this.callbacks.onError?.({
        type: 'system',
        message: 'Failed to cancel batch processing',
        details: error instanceof Error ? error.message : 'Unknown error',
        recoverable: false
      });
      return false;
    }
  }

  /**
   * Get current batch progress
   */
  getBatchProgress(): BatchProgress {
    const statuses = Array.from(this.fileStatuses.values());
    const totalFiles = statuses.length;
    const completedFiles = statuses.filter(s => s.status === 'completed').length;
    const failedFiles = statuses.filter(s => s.status === 'error').length;
    const processingFiles = statuses.filter(s => s.status === 'processing');
    
    const currentFileIndex = completedFiles + failedFiles;
    const overallProgress = totalFiles > 0 ? (currentFileIndex / totalFiles) * 100 : 0;
    
    // Estimate remaining time based on elapsed time and progress
    let estimatedTimeRemaining: number | undefined;
    if (overallProgress > 0 && overallProgress < 100) {
      const elapsedTime = Date.now() - this.startTime;
      const totalEstimatedTime = (elapsedTime / overallProgress) * 100;
      estimatedTimeRemaining = totalEstimatedTime - elapsedTime;
    }

    return {
      totalFiles,
      completedFiles,
      failedFiles,
      currentFileIndex,
      overallProgress,
      currentFile: processingFiles[0]?.file.name,
      estimatedTimeRemaining
    };
  }

  /**
   * Get file statuses
   */
  getFileStatuses(): BatchFileStatus[] {
    return Array.from(this.fileStatuses.values());
  }

  /**
   * Get results summary
   */
  getResultsSummary(): {
    successful: TranscriptionResult[];
    failed: Array<{ file: AudioFile; error: string }>;
    totalProcessingTime: number;
  } {
    const statuses = Array.from(this.fileStatuses.values());
    const successful = statuses
      .filter(s => s.status === 'completed' && s.result)
      .map(s => s.result!);
    
    const failed = statuses
      .filter(s => s.status === 'error')
      .map(s => ({ file: s.file, error: s.error || 'Unknown error' }));
    
    const totalProcessingTime = successful.reduce((total, result) => 
      total + result.processingTime, 0
    );

    return {
      successful,
      failed,
      totalProcessingTime
    };
  }

  /**
   * Handle individual file progress
   */
  private handleProgress(progress: ProcessingProgress): void {
    // Update file status if we have file information
    if (progress.currentFile) {
      const fileStatus = Array.from(this.fileStatuses.values())
        .find(s => s.file.name === progress.currentFile);
      
      if (fileStatus) {
        this.fileStatuses.set(fileStatus.file.id, {
          ...fileStatus,
          status: 'processing',
          progress: progress.progress
        });
      }
    }

    // Emit batch progress
    const batchProgress = this.getBatchProgress();
    this.callbacks.onProgress?.(batchProgress);
  }

  /**
   * Handle individual file completion
   */
  private handleFileComplete(result: TranscriptionResult): void {
    const fileStatus = Array.from(this.fileStatuses.values())
      .find(s => s.file.id === result.originalFile.id);
    
    if (fileStatus) {
      const updatedStatus: BatchFileStatus = {
        ...fileStatus,
        status: 'completed',
        result,
        progress: 100
      };
      
      this.fileStatuses.set(fileStatus.file.id, updatedStatus);
      this.callbacks.onFileComplete?.(updatedStatus);
    }

    // Check if all files are complete
    const statuses = Array.from(this.fileStatuses.values());
    const allComplete = statuses.every(s => 
      s.status === 'completed' || s.status === 'error'
    );

    if (allComplete) {
      this.callbacks.onComplete?.(statuses);
      this.currentJobId = null;
    }

    // Emit batch progress
    const batchProgress = this.getBatchProgress();
    this.callbacks.onProgress?.(batchProgress);
  }

  /**
   * Handle processing error
   */
  private handleError(error: Error): void {
    this.callbacks.onError?.({
      type: 'processing',
      message: 'Batch processing error',
      details: error.message,
      recoverable: true
    });
  }

  /**
   * Retry failed files
   */
  async retryFailedFiles(settings: AppSettings): Promise<void> {
    const failedStatuses = Array.from(this.fileStatuses.values())
      .filter(s => s.status === 'error');
    
    if (failedStatuses.length === 0) {
      return;
    }

    // Reset failed files to pending
    failedStatuses.forEach(status => {
      this.fileStatuses.set(status.file.id, {
        ...status,
        status: 'pending',
        error: undefined,
        progress: 0
      });
    });

    // Create File objects from failed files (this is a simplified approach)
    const filesToRetry = failedStatuses.map(status => 
      new File([], status.file.name)
    );

    // Start processing for failed files only
    try {
      const jobId = await processingService.processBatchFiles(
        filesToRetry,
        settings,
        {
          onProgress: (progress) => this.handleProgress(progress),
          onComplete: (result) => this.handleFileComplete(result),
          onError: (error) => this.handleError(error)
        }
      );
      
      this.currentJobId = jobId;
    } catch (error) {
      this.callbacks.onError?.({
        type: 'processing',
        message: 'Failed to retry failed files',
        details: error instanceof Error ? error.message : 'Unknown error',
        recoverable: true
      });
    }
  }

  /**
   * Remove file from batch
   */
  removeFile(fileId: string): void {
    this.fileStatuses.delete(fileId);
    
    // Emit updated progress
    const batchProgress = this.getBatchProgress();
    this.callbacks.onProgress?.(batchProgress);
  }

  /**
   * Clear all files and reset state
   */
  clear(): void {
    this.fileStatuses.clear();
    this.currentJobId = null;
    this.startTime = 0;
  }

  /**
   * Check if batch processing is active
   */
  isProcessing(): boolean {
    return this.currentJobId !== null;
  }

  /**
   * Cleanup resources
   */
  cleanup(): void {
    this.clear();
  }
}

// Singleton instance
export const batchWorkflowService = new BatchWorkflowService();