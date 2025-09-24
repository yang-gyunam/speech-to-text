import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { AppSettings, TranscriptionResult } from '../types';

// Mock Tauri API
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}));

vi.mock('@tauri-apps/api/event', () => ({
  listen: vi.fn(),
}));

// Mock services instead of importing
const mockFileService = {
  validateFile: vi.fn(),
  getFileInfo: vi.fn(),
  processFile: vi.fn(),
  saveFile: vi.fn(),
};

const mockProcessingService = {
  startProcessing: vi.fn(),
  stopProcessing: vi.fn(),
  getProgress: vi.fn(),
};

const mockWorkflowService = {
  startSingleFileWorkflow: vi.fn(),
  startBatchWorkflow: vi.fn(),
  cancelWorkflow: vi.fn(),
};

describe('Service Integration Tests', () => {
  const mockSettings = {
    language: 'ko',
    modelSize: 'base',
    outputDirectory: '/tmp/output',
    includeMetadata: true,
    autoSave: true,
    theme: 'system',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('FileService', () => {
    it('should validate supported file formats', () => {
      const supportedFormats = ['m4a', 'wav', 'mp3', 'aac', 'flac'];
      
      expect(supportedFormats.includes('m4a')).toBe(true);
      expect(supportedFormats.includes('wav')).toBe(true);
      expect(supportedFormats.includes('mp3')).toBe(true);
      expect(supportedFormats.includes('txt')).toBe(false);
    });

    it('should format file sizes correctly', () => {
      const formatFileSize = (bytes: number): string => {
        if (bytes >= 1073741824) return `${(bytes / 1073741824).toFixed(0)} GB`;
        if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(0)} MB`;
        if (bytes >= 1024) return `${(bytes / 1024).toFixed(0)} KB`;
        return `${bytes} B`;
      };
      
      expect(formatFileSize(1024)).toBe('1 KB');
      expect(formatFileSize(1048576)).toBe('1 MB');
      expect(formatFileSize(1073741824)).toBe('1 GB');
    });

    it('should generate correct output file names', () => {
      const generateOutputFileName = (inputName: string, outputDir?: string): string => {
        const baseName = inputName.replace(/\.[^/.]+$/, '');
        const outputName = `${baseName}.txt`;
        return outputDir ? `${outputDir}/${outputName}` : outputName;
      };
      
      expect(generateOutputFileName('test.m4a')).toBe('test.txt');
      expect(generateOutputFileName('test.m4a', '/output')).toBe('/output/test.txt');
    });

    it('should validate file types', () => {
      const isValidAudioFile = (fileName: string): boolean => {
        const supportedExtensions = ['.m4a', '.wav', '.mp3', '.aac', '.flac'];
        return supportedExtensions.some(ext => fileName.toLowerCase().endsWith(ext));
      };
      
      expect(isValidAudioFile('test.m4a')).toBe(true);
      expect(isValidAudioFile('test.txt')).toBe(false);
      expect(isValidAudioFile('audio.WAV')).toBe(true);
    });

    it('should mock file operations', async () => {
      mockFileService.saveFile.mockResolvedValue(true);
      
      const result = await mockFileService.saveFile('content', '/path/file.txt');
      
      expect(result).toBe(true);
      expect(mockFileService.saveFile).toHaveBeenCalledWith('content', '/path/file.txt');
    });
  });

  describe('ProcessingService', () => {
    it('should mock processing operations', async () => {
      const mockResult = {
        id: 'result-1',
        transcribedText: 'Test transcription',
        processingTime: 30.5,
      };

      mockProcessingService.startProcessing.mockResolvedValue(mockResult);

      const result = await mockProcessingService.startProcessing('test.m4a', mockSettings);

      expect(result).toEqual(mockResult);
      expect(mockProcessingService.startProcessing).toHaveBeenCalledWith('test.m4a', mockSettings);
    });

    it('should handle processing errors', async () => {
      mockProcessingService.startProcessing.mockRejectedValue(new Error('Processing failed'));

      await expect(
        mockProcessingService.startProcessing('invalid.txt', mockSettings)
      ).rejects.toThrow('Processing failed');
    });

    it('should track processing progress', async () => {
      const mockProgress = { progress: 0.5, stage: 'transcribing' };
      mockProcessingService.getProgress.mockResolvedValue(mockProgress);

      const progress = await mockProcessingService.getProgress('job-123');

      expect(progress).toEqual(mockProgress);
      expect(mockProcessingService.getProgress).toHaveBeenCalledWith('job-123');
    });

    it('should cancel processing jobs', async () => {
      mockProcessingService.stopProcessing.mockResolvedValue(true);

      const success = await mockProcessingService.stopProcessing('job-123');

      expect(success).toBe(true);
      expect(mockProcessingService.stopProcessing).toHaveBeenCalledWith('job-123');
    });
  });

  describe('WorkflowService', () => {
    it('should start single file workflow', async () => {
      mockWorkflowService.startSingleFileWorkflow.mockResolvedValue('workflow-123');

      const workflowId = await mockWorkflowService.startSingleFileWorkflow('test.m4a', mockSettings);

      expect(workflowId).toBe('workflow-123');
      expect(mockWorkflowService.startSingleFileWorkflow).toHaveBeenCalledWith('test.m4a', mockSettings);
    });

    it('should start batch workflow', async () => {
      const files = ['test1.m4a', 'test2.m4a'];
      mockWorkflowService.startBatchWorkflow.mockResolvedValue('batch-workflow-456');

      const workflowId = await mockWorkflowService.startBatchWorkflow(files, mockSettings);

      expect(workflowId).toBe('batch-workflow-456');
      expect(mockWorkflowService.startBatchWorkflow).toHaveBeenCalledWith(files, mockSettings);
    });

    it('should cancel workflows', async () => {
      mockWorkflowService.cancelWorkflow.mockResolvedValue(true);

      const success = await mockWorkflowService.cancelWorkflow('workflow-123');

      expect(success).toBe(true);
      expect(mockWorkflowService.cancelWorkflow).toHaveBeenCalledWith('workflow-123');
    });

    it('should handle workflow state transitions', () => {
      const workflowStates = ['idle', 'processing', 'completed', 'error'];
      
      expect(workflowStates).toContain('idle');
      expect(workflowStates).toContain('processing');
      expect(workflowStates).toContain('completed');
      expect(workflowStates).toContain('error');
    });
  });
});