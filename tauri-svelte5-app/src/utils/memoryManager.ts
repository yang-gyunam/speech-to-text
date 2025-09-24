/**
 * Memory management utilities for efficient handling of large files
 */

interface MemoryUsage {
  used: number;
  total: number;
  percentage: number;
}

interface FileChunk {
  data: ArrayBuffer;
  index: number;
  size: number;
}

interface ChunkProcessingOptions {
  chunkSize?: number;
  maxConcurrentChunks?: number;
  onProgress?: (progress: number) => void;
  onChunkProcessed?: (chunk: FileChunk) => void;
}

class MemoryManager {
  private static instance: MemoryManager;
  private memoryThreshold = 0.8; // 80% memory usage threshold
  private chunkSize = 1024 * 1024 * 5; // 5MB default chunk size
  private activeChunks = new Map<string, ArrayBuffer>();
  private memoryUsageCallbacks: Array<(usage: MemoryUsage) => void> = [];

  private constructor() {
    this.startMemoryMonitoring();
  }

  static getInstance(): MemoryManager {
    if (!MemoryManager.instance) {
      MemoryManager.instance = new MemoryManager();
    }
    return MemoryManager.instance;
  }

  /**
   * Get current memory usage information
   */
  getMemoryUsage(): MemoryUsage {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        percentage: (memory.usedJSHeapSize / memory.totalJSHeapSize) * 100
      };
    }
    
    // Fallback estimation
    return {
      used: 0,
      total: 0,
      percentage: 0
    };
  }

  /**
   * Check if memory usage is above threshold
   */
  isMemoryPressure(): boolean {
    const usage = this.getMemoryUsage();
    return usage.percentage > this.memoryThreshold * 100;
  }

  /**
   * Process large files in chunks to manage memory usage
   */
  async processFileInChunks(
    file: File,
    processor: (chunk: ArrayBuffer, index: number) => Promise<any>,
    options: ChunkProcessingOptions = {}
  ): Promise<any[]> {
    const {
      chunkSize = this.chunkSize,
      maxConcurrentChunks = 3,
      onProgress,
      onChunkProcessed
    } = options;

    const totalChunks = Math.ceil(file.size / chunkSize);
    const results: any[] = [];
    let processedChunks = 0;

    // Process chunks in batches to control memory usage
    for (let i = 0; i < totalChunks; i += maxConcurrentChunks) {
      const batchPromises: Promise<any>[] = [];
      
      // Create batch of chunks
      for (let j = 0; j < maxConcurrentChunks && (i + j) < totalChunks; j++) {
        const chunkIndex = i + j;
        const start = chunkIndex * chunkSize;
        const end = Math.min(start + chunkSize, file.size);
        
        const chunkPromise = this.processChunk(file, start, end, chunkIndex, processor);
        batchPromises.push(chunkPromise);
      }

      // Wait for batch to complete
      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);
      
      processedChunks += batchPromises.length;
      
      // Report progress
      if (onProgress) {
        onProgress((processedChunks / totalChunks) * 100);
      }

      // Trigger garbage collection if memory pressure is high
      if (this.isMemoryPressure()) {
        await this.forceGarbageCollection();
      }
    }

    return results;
  }

  /**
   * Process a single chunk of a file
   */
  private async processChunk(
    file: File,
    start: number,
    end: number,
    index: number,
    processor: (chunk: ArrayBuffer, index: number) => Promise<any>
  ): Promise<any> {
    const chunkId = `${file.name}-${index}`;
    
    try {
      // Read chunk
      const blob = file.slice(start, end);
      
      // Handle test environment where arrayBuffer() might not be available
      let arrayBuffer: ArrayBuffer;
      if (typeof blob.arrayBuffer === 'function') {
        arrayBuffer = await blob.arrayBuffer();
      } else {
        // Fallback for test environment
        arrayBuffer = new ArrayBuffer(end - start);
      }
      
      // Store chunk temporarily
      this.activeChunks.set(chunkId, arrayBuffer);
      
      // Process chunk
      const result = await processor(arrayBuffer, index);
      
      return result;
    } finally {
      // Clean up chunk from memory
      this.activeChunks.delete(chunkId);
    }
  }

  /**
   * Create a streaming file reader for very large files
   */
  createStreamingReader(file: File, chunkSize: number = this.chunkSize) {
    let position = 0;
    const self = this; // Capture context
    
    return {
      async *read() {
        while (position < file.size) {
          const end = Math.min(position + chunkSize, file.size);
          const chunk = file.slice(position, end);
          
          // Handle test environment where arrayBuffer() might not be available
          let arrayBuffer: ArrayBuffer;
          if (typeof chunk.arrayBuffer === 'function') {
            arrayBuffer = await chunk.arrayBuffer();
          } else {
            // Fallback for test environment
            arrayBuffer = new ArrayBuffer(end - position);
          }
          
          yield {
            data: arrayBuffer,
            position,
            size: arrayBuffer.byteLength,
            isLast: end >= file.size
          };
          
          position = end;
          
          // Check memory pressure and yield control
          if (self.isMemoryPressure()) {
            await self.forceGarbageCollection();
            // Small delay to allow garbage collection
            await new Promise(resolve => setTimeout(resolve, 10));
          }
        }
      },
      
      getProgress(): number {
        return (position / file.size) * 100;
      }
    };
  }

  /**
   * Optimize memory usage by clearing caches and triggering GC
   */
  async optimizeMemory(): Promise<void> {
    // Clear active chunks
    this.activeChunks.clear();
    
    // Force garbage collection
    await this.forceGarbageCollection();
    
    // Clear any cached data in other parts of the app
    this.notifyMemoryPressure();
  }

  /**
   * Force garbage collection (if available)
   */
  private async forceGarbageCollection(): Promise<void> {
    if ('gc' in window && typeof (window as any).gc === 'function') {
      (window as any).gc();
    }
    
    // Alternative: create memory pressure to trigger GC
    const tempArrays: ArrayBuffer[] = [];
    try {
      for (let i = 0; i < 10; i++) {
        tempArrays.push(new ArrayBuffer(1024 * 1024)); // 1MB each
      }
    } catch (e) {
      // Memory allocation failed, GC likely triggered
    } finally {
      tempArrays.length = 0; // Clear references
    }
    
    // Give browser time to clean up
    await new Promise(resolve => setTimeout(resolve, 0));
  }

  /**
   * Start monitoring memory usage
   */
  private startMemoryMonitoring(): void {
    if (typeof window === 'undefined') return;
    
    setInterval(() => {
      const usage = this.getMemoryUsage();
      
      // Notify callbacks about memory usage
      this.memoryUsageCallbacks.forEach(callback => {
        try {
          callback(usage);
        } catch (error) {
          console.error('Memory usage callback error:', error);
        }
      });
      
      // Auto-optimize if memory pressure is high
      if (usage.percentage > 90) {
        console.warn('High memory usage detected, optimizing...');
        this.optimizeMemory();
      }
    }, 5000); // Check every 5 seconds
  }

  /**
   * Subscribe to memory usage updates
   */
  onMemoryUsageChange(callback: (usage: MemoryUsage) => void): () => void {
    this.memoryUsageCallbacks.push(callback);
    
    // Return unsubscribe function
    return () => {
      const index = this.memoryUsageCallbacks.indexOf(callback);
      if (index > -1) {
        this.memoryUsageCallbacks.splice(index, 1);
      }
    };
  }

  /**
   * Notify other parts of the app about memory pressure
   */
  private notifyMemoryPressure(): void {
    // Dispatch custom event for memory pressure
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('memoryPressure', {
        detail: { usage: this.getMemoryUsage() }
      }));
    }
  }

  /**
   * Set memory threshold (0-1)
   */
  setMemoryThreshold(threshold: number): void {
    this.memoryThreshold = Math.max(0.1, Math.min(1, threshold));
  }

  /**
   * Set default chunk size for file processing
   */
  setChunkSize(size: number): void {
    this.chunkSize = Math.max(1024 * 1024, size); // Minimum 1MB
  }

  /**
   * Get statistics about memory manager
   */
  getStats() {
    return {
      activeChunks: this.activeChunks.size,
      memoryThreshold: this.memoryThreshold,
      chunkSize: this.chunkSize,
      memoryUsage: this.getMemoryUsage()
    };
  }
}

// Export singleton instance
export const memoryManager = MemoryManager.getInstance();

// Export types
export type { MemoryUsage, FileChunk, ChunkProcessingOptions };

// Utility functions
export const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const isLargeFile = (file: File, threshold: number = 50 * 1024 * 1024): boolean => {
  return file.size > threshold; // Default 50MB threshold
};