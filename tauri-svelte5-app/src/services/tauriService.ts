import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import type { 
  AudioFile, 
  TranscriptionResult, 
  AppSettings, 
  ProcessingProgress 
} from '../types';

export interface TauriService {
  // File operations
  validateAudioFile(filePath: string): Promise<AudioFile>;
  validateMultipleFiles(filePaths: string[]): Promise<AudioFile[]>;
  saveTextFile(content: string, filePath: string): Promise<void>;
  saveBinaryFile(filename: string, content: string, isBase64: boolean): Promise<string>;
  selectOutputDirectory(): Promise<string | null>;
  selectFiles(): Promise<string[]>;
  
  // Processing operations
  processAudioFile(filePath: string, settings: AppSettings): Promise<TranscriptionResult>;
  startBatchProcessing(filePaths: string[], settings: AppSettings): Promise<string>;
  cancelProcessing(jobId: string): Promise<boolean>;
  
  // Settings operations
  loadSettings(): Promise<AppSettings>;
  saveSettings(settings: AppSettings): Promise<void>;
  
  // System operations
  getSupportedFormats(): Promise<string[]>;
  checkCliAvailability(): Promise<boolean>;
  
  // Event listeners
  onProcessingProgress(callback: (progress: ProcessingProgress) => void): Promise<() => void>;
  onFileCompleted(callback: (result: TranscriptionResult) => void): Promise<() => void>;
  onBatchCompleted(callback: (data: any) => void): Promise<() => void>;
}

class TauriServiceImpl implements TauriService {
  async validateAudioFile(filePath: string): Promise<AudioFile> {
    try {
      return await invoke<AudioFile>('validate_audio_file', { filePath });
    } catch (error) {
      throw new Error(`Failed to validate audio file: ${error}`);
    }
  }

  async validateMultipleFiles(filePaths: string[]): Promise<AudioFile[]> {
    try {
      return await invoke<AudioFile[]>('validate_multiple_files', { filePaths });
    } catch (error) {
      throw new Error(`Failed to validate audio files: ${error}`);
    }
  }

  async saveTextFile(content: string, filePath: string): Promise<void> {
    try {
      await invoke('save_text_file', { content, filePath });
    } catch (error) {
      throw new Error(`Failed to save text file: ${error}`);
    }
  }

  async saveBinaryFile(filename: string, content: string, isBase64: boolean): Promise<string> {
    try {
      return await invoke<string>('save_binary_file', { filename, content, isBase64 });
    } catch (error) {
      throw new Error(`Failed to save binary file: ${error}`);
    }
  }

  async selectOutputDirectory(): Promise<string | null> {
    try {
      return await invoke<string | null>('select_output_directory');
    } catch (error) {
      throw new Error(`Failed to select output directory: ${error}`);
    }
  }

  async selectFiles(): Promise<string[]> {
    try {
      return await invoke<string[]>('select_files', { multiple: false });
    } catch (error) {
      throw new Error(`Failed to select files: ${error}`);
    }
  }

  async processAudioFile(filePath: string, settings: AppSettings): Promise<TranscriptionResult> {
    try {
      console.log('🔥 tauriService.processAudioFile called with:', filePath);

      // Convert frontend settings to backend format
      const backendSettings = {
        language: settings.language,
        model_size: settings.modelSize,
        output_directory: settings.outputDirectory,
        include_metadata: settings.includeMetadata,
        auto_save: settings.autoSave,
        theme: settings.theme,
        max_concurrent_jobs: settings.maxConcurrentJobs,
        enable_gpu_acceleration: settings.enableGpuAcceleration,
        memory_optimization: settings.memoryOptimization,
        enable_voice_activity_detection: settings.enableVoiceActivityDetection,
        noise_reduction: settings.noiseReduction,
        output_format: settings.outputFormat,
        compact_mode: settings.compactMode,
        show_advanced_options: settings.showAdvancedOptions,
        enable_notifications: settings.enableNotifications,
        auto_check_updates: settings.autoCheckUpdates,
      };

      console.log('🔥 About to invoke process_audio_file with settings:', backendSettings);
      const result = await invoke<TranscriptionResult>('process_audio_file', { filePath, settings: backendSettings });
      console.log('🔥 process_audio_file completed successfully:', result);
      return result;
    } catch (error) {
      console.error('🔥 process_audio_file failed:', error);
      const errorMessage = error instanceof Error ? error.message : JSON.stringify(error);
      throw new Error(`Failed to process audio file: ${errorMessage}`);
    }
  }

  async startBatchProcessing(filePaths: string[], settings: AppSettings): Promise<string> {
    try {
      // Convert frontend settings to backend format
      const backendSettings = {
        language: settings.language,
        model_size: settings.modelSize,
        output_directory: settings.outputDirectory,
        include_metadata: settings.includeMetadata,
        auto_save: settings.autoSave,
        theme: settings.theme,
        max_concurrent_jobs: settings.maxConcurrentJobs,
        enable_gpu_acceleration: settings.enableGpuAcceleration,
        memory_optimization: settings.memoryOptimization,
        enable_voice_activity_detection: settings.enableVoiceActivityDetection,
        noise_reduction: settings.noiseReduction,
        output_format: settings.outputFormat,
        compact_mode: settings.compactMode,
        show_advanced_options: settings.showAdvancedOptions,
        enable_notifications: settings.enableNotifications,
        auto_check_updates: settings.autoCheckUpdates,
      };

      return await invoke<string>('start_batch_processing', { filePaths, settings: backendSettings });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : JSON.stringify(error);
      throw new Error(`Failed to start batch processing: ${errorMessage}`);
    }
  }

  async cancelProcessing(jobId: string): Promise<boolean> {
    try {
      return await invoke<boolean>('cancel_processing_job', { jobId });
    } catch (error) {
      throw new Error(`Failed to cancel processing: ${error}`);
    }
  }

  async loadSettings(): Promise<AppSettings> {
    try {
      const backendSettings = await invoke<any>('load_settings');

      // Convert backend settings to frontend format
      return {
        language: backendSettings.language,
        modelSize: backendSettings.model_size,
        outputDirectory: backendSettings.output_directory,
        includeMetadata: backendSettings.include_metadata,
        autoSave: backendSettings.auto_save,
        theme: backendSettings.theme,
        maxConcurrentJobs: backendSettings.max_concurrent_jobs,
        enableGpuAcceleration: backendSettings.enable_gpu_acceleration,
        memoryOptimization: backendSettings.memory_optimization,
        enableVoiceActivityDetection: backendSettings.enable_voice_activity_detection,
        noiseReduction: backendSettings.noise_reduction,
        outputFormat: backendSettings.output_format,
        compactMode: backendSettings.compact_mode,
        showAdvancedOptions: backendSettings.show_advanced_options,
        enableNotifications: backendSettings.enable_notifications,
        autoCheckUpdates: backendSettings.auto_check_updates,
      };
    } catch (error) {
      // Return default settings if loading fails
      console.warn('Failed to load settings, using defaults:', error);
      const defaultBackendSettings = await invoke<any>('get_default_settings');

      // Convert default backend settings to frontend format
      return {
        language: defaultBackendSettings.language,
        modelSize: defaultBackendSettings.model_size,
        outputDirectory: defaultBackendSettings.output_directory,
        includeMetadata: defaultBackendSettings.include_metadata,
        autoSave: defaultBackendSettings.auto_save,
        theme: defaultBackendSettings.theme,
        maxConcurrentJobs: defaultBackendSettings.max_concurrent_jobs,
        enableGpuAcceleration: defaultBackendSettings.enable_gpu_acceleration,
        memoryOptimization: defaultBackendSettings.memory_optimization,
        enableVoiceActivityDetection: defaultBackendSettings.enable_voice_activity_detection,
        noiseReduction: defaultBackendSettings.noise_reduction,
        outputFormat: defaultBackendSettings.output_format,
        compactMode: defaultBackendSettings.compact_mode,
        showAdvancedOptions: defaultBackendSettings.show_advanced_options,
        enableNotifications: defaultBackendSettings.enable_notifications,
        autoCheckUpdates: defaultBackendSettings.auto_check_updates,
      };
    }
  }

  async saveSettings(settings: AppSettings): Promise<void> {
    try {
      // Convert frontend settings to backend format
      const backendSettings = {
        language: settings.language,
        model_size: settings.modelSize,
        output_directory: settings.outputDirectory,
        include_metadata: settings.includeMetadata,
        auto_save: settings.autoSave,
        theme: settings.theme,
        max_concurrent_jobs: settings.maxConcurrentJobs,
        enable_gpu_acceleration: settings.enableGpuAcceleration,
        memory_optimization: settings.memoryOptimization,
        enable_voice_activity_detection: settings.enableVoiceActivityDetection,
        noise_reduction: settings.noiseReduction,
        output_format: settings.outputFormat,
        compact_mode: settings.compactMode,
        show_advanced_options: settings.showAdvancedOptions,
        enable_notifications: settings.enableNotifications,
        auto_check_updates: settings.autoCheckUpdates,
      };

      await invoke('save_settings', { settings: backendSettings });
    } catch (error) {
      throw new Error(`Failed to save settings: ${error}`);
    }
  }

  async getSupportedFormats(): Promise<string[]> {
    try {
      return await invoke<string[]>('get_supported_formats');
    } catch (error) {
      // Return default formats if command fails
      return ['.m4a', '.wav', '.mp3', '.aac', '.flac', '.ogg'];
    }
  }

  async checkCliAvailability(): Promise<boolean> {
    try {
      return await invoke<boolean>('check_cli_availability');
    } catch (error) {
      return false;
    }
  }

  async onProcessingProgress(callback: (progress: ProcessingProgress) => void): Promise<() => void> {
    const unlisten = await listen<ProcessingProgress>('file-progress', (event) => {
      callback(event.payload);
    });
    return unlisten;
  }

  async onFileCompleted(callback: (result: TranscriptionResult) => void): Promise<() => void> {
    const unlisten = await listen<TranscriptionResult>('file-completed', (event) => {
      callback(event.payload);
    });
    return unlisten;
  }

  async onBatchCompleted(callback: (data: any) => void): Promise<() => void> {
    const unlisten = await listen('batch-completed', (event) => {
      callback(event.payload);
    });
    return unlisten;
  }
}

// Singleton instance
export const tauriService: TauriService = new TauriServiceImpl();