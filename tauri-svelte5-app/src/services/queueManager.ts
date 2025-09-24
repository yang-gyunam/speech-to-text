/**
 * Processing queue manager with prioritization and advanced features
 */

interface QueueItem {
  id: string;
  file: File;
  settings: any;
  priority: number;
  createdAt: Date;
  estimatedDuration?: number;
  retryCount: number;
  maxRetries: number;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  result?: any;
  error?: string;
  onProgress?: (progress: any) => void;
  onComplete?: (result: any) => void;
  onError?: (error: string) => void;
}

interface QueueStats {
  total: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  cancelled: number;
  averageProcessingTime: number;
  estimatedTimeRemaining: number;
}

interface QueueManagerOptions {
  maxConcurrentJobs?: number;
  defaultPriority?: number;
  maxRetries?: number;
  retryDelay?: number;
  autoStart?: boolean;
}

class QueueManager {
  private static instance: QueueManager;
  private queue: QueueItem[] = [];
  private processing = new Map<string, QueueItem>();
  private completed: QueueItem[] = [];
  private failed: QueueItem[] = [];
  private maxConcurrentJobs: number;
  private defaultPriority: number;
  private maxRetries: number;
  private retryDelay: number;
  private autoStart: boolean;
  private isRunning = false;
  private processingTimes: number[] = [];

  private constructor(options: QueueManagerOptions = {}) {
    this.maxConcurrentJobs = options.maxConcurrentJobs || 2;
    this.defaultPriority = options.defaultPriority || 5;
    this.maxRetries = options.maxRetries || 3;
    this.retryDelay = options.retryDelay || 5000;
    this.autoStart = options.autoStart !== false;
  }

  static getInstance(options?: QueueManagerOptions): QueueManager {
    if (!QueueManager.instance) {
      QueueManager.instance = new QueueManager(options);
    }
    return QueueManager.instance;
  }

  /**
   * Add item to processing queue
   */
  addToQueue(
    file: File,
    settings: any,
    options: {
      priority?: number;
      estimatedDuration?: number;
      maxRetries?: number;
      onProgress?: (progress: any) => void;
      onComplete?: (result: any) => void;
      onError?: (error: string) => void;
    } = {}
  ): string {
    const id = this.generateId();
    
    const queueItem: QueueItem = {
      id,
      file,
      settings,
      priority: options.priority || this.defaultPriority,
      createdAt: new Date(),
      estimatedDuration: options.estimatedDuration,
      retryCount: 0,
      maxRetries: options.maxRetries || this.maxRetries,
      status: 'pending',
      onProgress: options.onProgress,
      onComplete: options.onComplete,
      onError: options.onError
    };

    // Insert in priority order (higher priority first)
    const insertIndex = this.queue.findIndex(item => item.priority < queueItem.priority);
    if (insertIndex === -1) {
      this.queue.push(queueItem);
    } else {
      this.queue.splice(insertIndex, 0, queueItem);
    }

    // Don't auto-start in test environment
    if (this.autoStart && !this.isRunning && typeof window !== 'undefined') {
      this.start();
    }

    return id;
  }

  /**
   * Start processing queue
   */
  start(): void {
    if (this.isRunning) return;
    
    this.isRunning = true;
    this.processQueue();
  }

  /**
   * Stop processing queue
   */
  stop(): void {
    this.isRunning = false;
  }

  /**
   * Pause processing (finish current jobs but don't start new ones)
   */
  pause(): void {
    this.isRunning = false;
  }

  /**
   * Resume processing
   */
  resume(): void {
    if (!this.isRunning) {
      this.isRunning = true;
      this.processQueue();
    }
  }

  /**
   * Cancel specific item
   */
  cancelItem(id: string): boolean {
    // Check if item is in queue
    const queueIndex = this.queue.findIndex(item => item.id === id);
    if (queueIndex !== -1) {
      this.queue.splice(queueIndex, 1);
      return true;
    }

    // Check if item is currently processing
    const processingItem = this.processing.get(id);
    if (processingItem) {
      processingItem.status = 'cancelled';
      this.processing.delete(id);
      // Note: Actual cancellation of processing would need to be handled by the processor
      return true;
    }

    return false;
  }

  /**
   * Clear all pending items
   */
  clearQueue(): void {
    this.queue = [];
  }

  /**
   * Retry failed item
   */
  retryItem(id: string): boolean {
    const failedIndex = this.failed.findIndex(item => item.id === id);
    if (failedIndex === -1) return false;

    const item = this.failed[failedIndex];
    if (item.retryCount >= item.maxRetries) return false;

    // Reset item and add back to queue
    item.status = 'pending';
    item.retryCount++;
    item.error = undefined;
    
    this.failed.splice(failedIndex, 1);
    
    // Insert with higher priority for retry
    const insertIndex = this.queue.findIndex(queueItem => queueItem.priority < item.priority + 1);
    if (insertIndex === -1) {
      this.queue.push(item);
    } else {
      this.queue.splice(insertIndex, 0, item);
    }

    // Don't auto-start in test environment
    if (this.autoStart && !this.isRunning && typeof window !== 'undefined') {
      this.start();
    }

    return true;
  }

  /**
   * Get queue statistics
   */
  getStats(): QueueStats {
    const total = this.queue.length + this.processing.size + this.completed.length + this.failed.length;
    const pending = this.queue.length;
    const processing = this.processing.size;
    const completed = this.completed.length;
    const failed = this.failed.length;
    const cancelled = this.queue.filter(item => item.status === 'cancelled').length;

    const averageProcessingTime = this.processingTimes.length > 0
      ? this.processingTimes.reduce((sum, time) => sum + time, 0) / this.processingTimes.length
      : 0;

    const estimatedTimeRemaining = pending * averageProcessingTime;

    return {
      total,
      pending,
      processing,
      completed,
      failed,
      cancelled,
      averageProcessingTime,
      estimatedTimeRemaining
    };
  }

  /**
   * Get queue items by status
   */
  getItemsByStatus(status: QueueItem['status']): QueueItem[] {
    switch (status) {
      case 'pending':
        return [...this.queue];
      case 'processing':
        return Array.from(this.processing.values());
      case 'completed':
        return [...this.completed];
      case 'failed':
        return [...this.failed];
      default:
        return [];
    }
  }

  /**
   * Get item by ID
   */
  getItem(id: string): QueueItem | null {
    // Check queue
    const queueItem = this.queue.find(item => item.id === id);
    if (queueItem) return queueItem;

    // Check processing
    const processingItem = this.processing.get(id);
    if (processingItem) return processingItem;

    // Check completed
    const completedItem = this.completed.find(item => item.id === id);
    if (completedItem) return completedItem;

    // Check failed
    const failedItem = this.failed.find(item => item.id === id);
    if (failedItem) return failedItem;

    return null;
  }

  /**
   * Process queue items
   */
  private async processQueue(): Promise<void> {
    while (this.isRunning && this.queue.length > 0 && this.processing.size < this.maxConcurrentJobs) {
      const item = this.queue.shift();
      if (!item) break;

      item.status = 'processing';
      this.processing.set(item.id, item);

      // Process item asynchronously
      this.processItem(item).catch(error => {
        console.error('Queue processing error:', error);
      });
    }

    // Continue processing if there are more items
    if (this.isRunning && this.queue.length > 0) {
      setTimeout(() => this.processQueue(), 1000);
    }
  }

  /**
   * Process individual item
   */
  private async processItem(item: QueueItem): Promise<void> {
    const startTime = Date.now();

    try {
      // Simulate processing (replace with actual processing logic)
      const result = await this.simulateProcessing(item);
      
      const endTime = Date.now();
      const processingTime = endTime - startTime;
      this.processingTimes.push(processingTime);
      
      // Keep only last 100 processing times for average calculation
      if (this.processingTimes.length > 100) {
        this.processingTimes.shift();
      }

      item.status = 'completed';
      item.result = result;
      
      this.processing.delete(item.id);
      this.completed.push(item);

      if (item.onComplete) {
        item.onComplete(result);
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      
      item.error = errorMessage;
      this.processing.delete(item.id);

      // Check if we should retry
      if (item.retryCount < item.maxRetries) {
        // Schedule retry
        setTimeout(() => {
          if (item.status !== 'cancelled') {
            this.retryItem(item.id);
          }
        }, this.retryDelay);
      } else {
        item.status = 'failed';
        this.failed.push(item);

        if (item.onError) {
          item.onError(errorMessage);
        }
      }
    }

    // Continue processing queue
    if (this.isRunning) {
      this.processQueue();
    }
  }

  /**
   * Simulate processing (replace with actual processing logic)
   */
  private async simulateProcessing(item: QueueItem): Promise<any> {
    const duration = item.estimatedDuration || 5000;
    const steps = 10;
    const stepDuration = duration / steps;

    for (let i = 0; i < steps; i++) {
      if (item.status === 'cancelled') {
        throw new Error('Processing cancelled');
      }

      await new Promise(resolve => setTimeout(resolve, stepDuration));
      
      if (item.onProgress) {
        item.onProgress({
          stage: 'processing',
          progress: ((i + 1) / steps) * 100,
          message: `Processing ${item.file.name}...`
        });
      }
    }

    return {
      transcribedText: `Mock transcription for ${item.file.name}`,
      processingTime: duration,
      retryCount: item.retryCount
    };
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `queue_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Cleanup queue manager
   */
  cleanup(): void {
    this.stop();
    this.clearQueue();
    this.processing.clear();
    this.completed = [];
    this.failed = [];
    this.processingTimes = [];
  }

  /**
   * Reset instance (for testing)
   */
  static resetInstance(): void {
    QueueManager.instance = null as any;
  }
}

// Export singleton instance
export const queueManager = QueueManager.getInstance();

// Export class for testing
export { QueueManager };

// Export types
export type { QueueItem, QueueStats, QueueManagerOptions };