import { tauriService } from './tauriService';
import type { AudioFile } from '../types';

export interface FileValidationResult {
  valid: AudioFile[];
  invalid: Array<{
    file: File;
    error: string;
  }>;
}

export class FileService {
  private readonly SUPPORTED_FORMATS = ['.m4a', '.wav', '.mp3', '.aac', '.flac', '.ogg', '.wma'];
  private readonly MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB

  /**
   * Validate and convert File objects to AudioFile objects
   */
  async validateFiles(files: File[]): Promise<FileValidationResult> {
    const result: FileValidationResult = {
      valid: [],
      invalid: []
    };

    for (const file of files) {
      try {
        // Basic client-side validation
        const clientError = this.validateFileClientSide(file);
        if (clientError) {
          result.invalid.push({ file, error: clientError });
          continue;
        }

        // Create temporary file path for validation
        // In a real implementation, we would save the file to a temporary location
        const tempPath = await this.saveFileTemporarily(file);
        
        // Validate with Tauri backend
        const audioFile = await tauriService.validateAudioFile(tempPath);
        result.valid.push(audioFile);
      } catch (error) {
        result.invalid.push({ 
          file, 
          error: error instanceof Error ? error.message : 'Unknown validation error' 
        });
      }
    }

    return result;
  }

  /**
   * Client-side file validation
   */
  private validateFileClientSide(file: File): string | null {
    // Check file size
    if (file.size > this.MAX_FILE_SIZE) {
      return `File size (${this.formatFileSize(file.size)}) exceeds maximum allowed size (${this.formatFileSize(this.MAX_FILE_SIZE)})`;
    }

    // Check file format
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!this.SUPPORTED_FORMATS.includes(extension)) {
      return `Unsupported file format. Supported formats: ${this.SUPPORTED_FORMATS.join(', ')}`;
    }

    // Check MIME type if available
    if (file.type && !file.type.startsWith('audio/') && !file.type.includes('video/')) {
      return 'File does not appear to be an audio file';
    }

    return null;
  }

  /**
   * Save file temporarily for processing
   */
  private async saveFileTemporarily(file: File): Promise<string> {
    try {
      // Convert File to ArrayBuffer
      const arrayBuffer = await file.arrayBuffer();
      const uint8Array = new Uint8Array(arrayBuffer);
      
      // Convert to base64 for transfer to backend
      const base64Content = btoa(String.fromCharCode(...uint8Array));
      
      // Generate unique filename
      const timestamp = Date.now();
      const sanitizedName = file.name.replace(/[^a-zA-Z0-9.-]/g, '_');
      const fileName = `${timestamp}-${sanitizedName}`;
      
      // Save file using Tauri backend
      const tempPath = await tauriService.saveBinaryFile(fileName, base64Content, true);
      
      return tempPath;
    } catch (error) {
      throw new Error(`Failed to save file temporarily: ${error}`);
    }
  }

  /**
   * Convert File objects to file paths for processing
   */
  async prepareFilesForProcessing(files: File[]): Promise<string[]> {
    const filePaths: string[] = [];
    
    for (const file of files) {
      const tempPath = await this.saveFileTemporarily(file);
      filePaths.push(tempPath);
    }
    
    return filePaths;
  }

  /**
   * Format file size for display
   */
  formatFileSize(bytes: number): string {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * Get supported file formats
   */
  getSupportedFormats(): string[] {
    return [...this.SUPPORTED_FORMATS];
  }

  /**
   * Check if a file format is supported
   */
  isFormatSupported(fileName: string): boolean {
    const extension = '.' + fileName.split('.').pop()?.toLowerCase();
    return this.SUPPORTED_FORMATS.includes(extension);
  }

  /**
   * Get file extension from file name
   */
  getFileExtension(fileName: string): string {
    return fileName.split('.').pop()?.toLowerCase() || '';
  }

  /**
   * Generate output file name for transcription
   */
  generateOutputFileName(inputFileName: string, outputDir?: string): string {
    const baseName = inputFileName.replace(/\.[^/.]+$/, '');
    const outputFileName = `${baseName}.txt`;
    
    if (outputDir) {
      return `${outputDir}/${outputFileName}`;
    }
    
    return outputFileName;
  }

  /**
   * Save transcription result to file
   */
  async saveTranscriptionResult(content: string, filePath: string): Promise<void> {
    try {
      await tauriService.saveTextFile(content, filePath);
    } catch (error) {
      throw new Error(`Failed to save transcription result: ${error}`);
    }
  }

  /**
   * Select output directory using system dialog
   */
  async selectOutputDirectory(): Promise<string | null> {
    try {
      return await tauriService.selectOutputDirectory();
    } catch (error) {
      throw new Error(`Failed to select output directory: ${error}`);
    }
  }
}

// Singleton instance
export const fileService = new FileService();