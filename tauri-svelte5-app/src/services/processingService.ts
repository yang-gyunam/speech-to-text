import { tauriService } from './tauriService';
import { MacOSIntegrationService } from './macosIntegrationService';
import type { 
  AudioFile, 
  TranscriptionResult, 
  AppSettings, 
  ProcessingProgress,
  ProcessingJob 
} from '../types';

export interface ProcessingCallbacks {
  onProgress?: (progress: ProcessingProgress) => void;
  onComplete?: (result: TranscriptionResult) => void;
  onError?: (error: Error) => void;
  onCancel?: () => void;
}

export class ProcessingService {
  private activeJobs = new Map<string, ProcessingJob>();
  private progressUnlisteners = new Map<string, () => void>();
  private completionUnlisteners = new Map<string, () => void>();

  /**
   * Process a single audio file
   */
  async processSingleFile(
    file: File | AudioFile,
    settings: AppSettings,
    callbacks?: ProcessingCallbacks,
    originalFilePath?: string
  ): Promise<TranscriptionResult> {
    const jobId = `single-${Date.now()}`;
    
    try {
      let audioFile: AudioFile;
      
      if ('path' in file) {
        // It's already an AudioFile object
        audioFile = file;
      } else {
        // It's a File object, need to validate
        const filePath = file.name; // This would be the actual saved file path
        
        try {
          audioFile = await tauriService.validateAudioFile(filePath);
        } catch (error) {
          throw new Error(`Invalid audio file: ${error}`);
        }
      }

      // Create processing job
      const job: ProcessingJob = {
        id: jobId,
        files: [audioFile],
        currentFileIndex: 0,
        progress: 0,
        stage: 'initializing',
        startTime: Date.now(),
        canCancel: true
      };

      this.activeJobs.set(jobId, job);

      // Show processing started notification on macOS
      await MacOSIntegrationService.showProcessingStartedNotification(audioFile.name);

      // Set up progress monitoring with macOS integration
      if (callbacks?.onProgress) {
        const enhancedProgressCallback = async (progress: ProcessingProgress) => {
          // Update dock progress on macOS
          await MacOSIntegrationService.updateProcessingProgress(progress.progress / 100);
          
          // Call original callback
          callbacks.onProgress?.(progress);
        };
        
        const progressUnlisten = await tauriService.onProcessingProgress(enhancedProgressCallback);
        this.progressUnlisteners.set(jobId, progressUnlisten);
      }

      // Set up completion monitoring with macOS integration
      if (callbacks?.onComplete) {
        const enhancedCompletionCallback = async (result: TranscriptionResult) => {
          // Show completion notification on macOS
          await MacOSIntegrationService.showProcessingCompletedNotification(result.originalFile.name, true);
          
          // Clear dock progress
          await MacOSIntegrationService.clearDockProgress();
          
          // Call original callback
          callbacks.onComplete?.(result);
        };
        
        const completionUnlisten = await tauriService.onFileCompleted(enhancedCompletionCallback);
        this.completionUnlisteners.set(jobId, completionUnlisten);
      }

      // Start processing
      console.log('🔥 About to call processAudioFile with audioFile:', audioFile);
      console.log('🔥 audioFile.path:', audioFile.path);

      // Use originalFilePath if audioFile.path is empty (serialization workaround)
      let filePath = audioFile.path;
      if (!filePath && originalFilePath) {
        console.log('⚠️ audioFile.path is empty, using originalFilePath:', originalFilePath);
        filePath = originalFilePath;
      }

      if (!filePath) {
        throw new Error(`No valid file path available. audioFile.path: "${audioFile.path}", originalFilePath: "${originalFilePath}"`);
      }

      const result = await tauriService.processAudioFile(filePath, settings);
      
      // Clean up
      this.cleanupJob(jobId);
      
      return result;
    } catch (error) {
      // Show error notification on macOS
      const audioFile = this.activeJobs.get(jobId)?.files[0];
      if (audioFile) {
        await MacOSIntegrationService.showProcessingCompletedNotification(audioFile.name, false);
      }
      
      // Clear dock progress
      await MacOSIntegrationService.clearDockProgress();
      
      this.cleanupJob(jobId);
      if (callbacks?.onError) {
        callbacks.onError(error as Error);
      }
      throw error;
    }
  }

  /**
   * Process multiple files in batch
   */
  async processBatchFiles(
    files: File[], 
    settings: AppSettings, 
    callbacks?: ProcessingCallbacks
  ): Promise<string> {
    const jobId = `batch-${Date.now()}`;
    
    try {
      // Convert files to file paths (in real implementation, we'd save files first)
      const filePaths = files.map(file => file.name);
      
      // Validate all files first
      const audioFiles = await tauriService.validateMultipleFiles(filePaths);
      
      if (audioFiles.length === 0) {
        throw new Error('No valid audio files found');
      }

      // Create processing job
      const job: ProcessingJob = {
        id: jobId,
        files: audioFiles,
        currentFileIndex: 0,
        progress: 0,
        stage: 'initializing',
        startTime: Date.now(),
        canCancel: true
      };

      this.activeJobs.set(jobId, job);

      // Update dock badge with file count on macOS
      await MacOSIntegrationService.updateProcessingBadge(audioFiles.length);

      // Set up progress monitoring with macOS integration
      if (callbacks?.onProgress) {
        const enhancedProgressCallback = async (progress: ProcessingProgress) => {
          // Update dock progress on macOS
          await MacOSIntegrationService.updateProcessingProgress(progress.progress / 100);
          
          // Call original callback
          callbacks.onProgress?.(progress);
        };
        
        const progressUnlisten = await tauriService.onProcessingProgress(enhancedProgressCallback);
        this.progressUnlisteners.set(jobId, progressUnlisten);
      }

      // Set up batch completion monitoring with macOS integration
      if (callbacks?.onComplete) {
        const batchUnlisten = await tauriService.onBatchCompleted(async (data) => {
          // Show batch completion notification on macOS
          const totalFiles = audioFiles.length;
          const successCount = data.results ? data.results.length : 0;
          await MacOSIntegrationService.showBatchCompletedNotification(totalFiles, successCount);
          
          // Clear dock badge and progress
          await MacOSIntegrationService.clearDockBadge();
          await MacOSIntegrationService.clearDockProgress();
          
          // Convert batch completion to individual results
          if (data.results && Array.isArray(data.results)) {
            data.results.forEach((result: TranscriptionResult) => {
              callbacks.onComplete?.(result);
            });
          }
        });
        this.completionUnlisteners.set(jobId, batchUnlisten);
      }

      // Start batch processing
      const batchJobId = await tauriService.startBatchProcessing(filePaths, settings);
      
      return batchJobId;
    } catch (error) {
      // Clear dock badge and progress on error
      await MacOSIntegrationService.clearDockBadge();
      await MacOSIntegrationService.clearDockProgress();
      
      this.cleanupJob(jobId);
      if (callbacks?.onError) {
        callbacks.onError(error as Error);
      }
      throw error;
    }
  }

  /**
   * Cancel an active processing job
   */
  async cancelProcessing(jobId: string): Promise<boolean> {
    try {
      const success = await tauriService.cancelProcessing(jobId);
      if (success) {
        this.cleanupJob(jobId);
      }
      return success;
    } catch (error) {
      console.error('Failed to cancel processing:', error);
      return false;
    }
  }

  /**
   * Get active processing job
   */
  getActiveJob(jobId: string): ProcessingJob | undefined {
    return this.activeJobs.get(jobId);
  }

  /**
   * Get all active jobs
   */
  getActiveJobs(): ProcessingJob[] {
    return Array.from(this.activeJobs.values());
  }

  /**
   * Clean up job resources
   */
  private cleanupJob(jobId: string): void {
    this.activeJobs.delete(jobId);
    
    const progressUnlisten = this.progressUnlisteners.get(jobId);
    if (progressUnlisten) {
      progressUnlisten();
      this.progressUnlisteners.delete(jobId);
    }
    
    const completionUnlisten = this.completionUnlisteners.get(jobId);
    if (completionUnlisten) {
      completionUnlisten();
      this.completionUnlisteners.delete(jobId);
    }
  }

  /**
   * Clean up all resources
   */
  cleanup(): void {
    for (const jobId of this.activeJobs.keys()) {
      this.cleanupJob(jobId);
    }
  }
}

// Singleton instance
export const processingService = new ProcessingService();