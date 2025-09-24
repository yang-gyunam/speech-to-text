/**
 * Service for managing Web Workers for background processing
 */

interface WorkerTask {
  id: string;
  resolve: (value: any) => void;
  reject: (error: Error) => void;
  onProgress?: (progress: any) => void;
}

interface WorkerServiceOptions {
  maxWorkers?: number;
  workerTimeout?: number;
}

class WorkerService {
  private static instance: WorkerService;
  private workers: Worker[] = [];
  private availableWorkers: Worker[] = [];
  private busyWorkers: Set<Worker> = new Set();
  private taskQueue: WorkerTask[] = [];
  private activeTasks = new Map<string, WorkerTask>();
  private maxWorkers: number;
  private workerTimeout: number;

  private constructor(options: WorkerServiceOptions = {}) {
    this.maxWorkers = options.maxWorkers || navigator.hardwareConcurrency || 2;
    this.workerTimeout = options.workerTimeout || 300000; // 5 minutes
    this.initializeWorkers();
  }

  static getInstance(options?: WorkerServiceOptions): WorkerService {
    if (!WorkerService.instance) {
      WorkerService.instance = new WorkerService(options);
    }
    return WorkerService.instance;
  }

  /**
   * Initialize worker pool
   */
  private initializeWorkers(): void {
    for (let i = 0; i < this.maxWorkers; i++) {
      this.createWorker();
    }
  }

  /**
   * Create a new worker
   */
  private createWorker(): Worker {
    try {
      // Check if we're in a browser environment
      if (typeof window === 'undefined' || typeof Worker === 'undefined' || typeof URL === 'undefined') {
        throw new Error('Worker not supported in this environment');
      }
      
      // Create worker from the processing worker file
      const workerBlob = new Blob([this.getWorkerScript()], { type: 'application/javascript' });
      const workerUrl = URL.createObjectURL(workerBlob);
      const worker = new Worker(workerUrl);

      // Set up message handler
      worker.onmessage = (event) => {
        this.handleWorkerMessage(worker, event);
      };

      // Set up error handler
      worker.onerror = (error) => {
        console.error('Worker error:', error);
        this.handleWorkerError(worker, error);
      };

      this.workers.push(worker);
      this.availableWorkers.push(worker);

      return worker;
    } catch (error) {
      console.error('Failed to create worker:', error);
      throw new Error('Worker creation failed');
    }
  }

  /**
   * Get worker script as string (inline for simplicity)
   */
  private getWorkerScript(): string {
    return `
      // Inline worker script for audio processing
      let currentTask = null;
      let isProcessing = false;

      self.onmessage = async (event) => {
        const { id, type, payload } = event.data;

        try {
          switch (type) {
            case 'process':
              await handleProcessingTask(id, payload);
              break;
            case 'cancel':
              handleCancelTask(id);
              break;
            default:
              sendError(id, 'Unknown message type: ' + type);
          }
        } catch (error) {
          sendError(id, error.message || 'Unknown error');
        }
      };

      async function handleProcessingTask(id, payload) {
        if (isProcessing) {
          sendError(id, 'Worker is already processing a task');
          return;
        }

        isProcessing = true;
        currentTask = { id, ...payload };

        try {
          sendProgress(id, { stage: 'initializing', progress: 0 });

          // Simulate chunked processing
          const chunks = await processFileInChunks(payload.file, id);
          sendProgress(id, { stage: 'processing', progress: 50 });

          // Simulate transcription
          const result = await simulateTranscription(chunks, payload.settings, id);
          sendSuccess(id, result);
        } catch (error) {
          sendError(id, error.message);
        } finally {
          isProcessing = false;
          currentTask = null;
        }
      }

      async function processFileInChunks(file, taskId) {
        const chunkSize = 1024 * 1024 * 2; // 2MB
        const totalChunks = Math.ceil(file.size / chunkSize);
        const chunks = [];

        for (let i = 0; i < totalChunks; i++) {
          if (!isProcessing || currentTask?.id !== taskId) {
            throw new Error('Task cancelled');
          }

          const start = i * chunkSize;
          const end = Math.min(start + chunkSize, file.size);
          const blob = file.slice(start, end);
          const arrayBuffer = await blob.arrayBuffer();
          chunks.push(arrayBuffer);

          const progress = ((i + 1) / totalChunks) * 30;
          sendProgress(taskId, { 
            stage: 'chunking', 
            progress,
            message: 'Processing chunk ' + (i + 1) + ' of ' + totalChunks
          });

          await new Promise(resolve => setTimeout(resolve, 10));
        }

        return chunks;
      }

      async function simulateTranscription(chunks, settings, taskId) {
        const steps = 50;
        
        for (let i = 0; i < steps; i++) {
          if (!isProcessing || currentTask?.id !== taskId) {
            throw new Error('Task cancelled');
          }

          await new Promise(resolve => setTimeout(resolve, 100));
          
          const progress = 50 + (i / steps) * 50;
          sendProgress(taskId, {
            stage: 'transcribing',
            progress,
            message: 'Transcribing audio... ' + Math.round(progress) + '%'
          });
        }

        return {
          transcribedText: 'Mock transcription from worker for file: ' + (chunks.length > 0 ? 'processed' : 'empty'),
          metadata: {
            processingTime: Date.now(),
            chunks: chunks.length,
            settings: settings
          }
        };
      }

      function handleCancelTask(id) {
        if (currentTask?.id === id) {
          isProcessing = false;
          currentTask = null;
          sendSuccess(id, { cancelled: true });
        }
      }

      function sendSuccess(id, payload) {
        self.postMessage({ id, type: 'success', payload });
      }

      function sendError(id, message) {
        self.postMessage({ id, type: 'error', payload: { message } });
      }

      function sendProgress(id, payload) {
        self.postMessage({ id, type: 'progress', payload });
      }
    `;
  }

  /**
   * Handle messages from workers
   */
  private handleWorkerMessage(worker: Worker, event: MessageEvent): void {
    const { id, type, payload } = event.data;
    const task = this.activeTasks.get(id);

    if (!task) {
      console.warn('Received message for unknown task:', id);
      return;
    }

    switch (type) {
      case 'success':
        task.resolve(payload);
        this.completeTask(worker, id);
        break;

      case 'error':
        task.reject(new Error(payload.message || 'Worker error'));
        this.completeTask(worker, id);
        break;

      case 'progress':
        if (task.onProgress) {
          task.onProgress(payload);
        }
        break;

      default:
        console.warn('Unknown message type from worker:', type);
    }
  }

  /**
   * Handle worker errors
   */
  private handleWorkerError(worker: Worker, error: ErrorEvent): void {
    console.error('Worker error:', error);
    
    // Find and reject any active tasks for this worker
    for (const [taskId, task] of this.activeTasks.entries()) {
      if (this.busyWorkers.has(worker)) {
        task.reject(new Error('Worker error: ' + error.message));
        this.activeTasks.delete(taskId);
      }
    }

    // Remove and recreate the worker
    this.removeWorker(worker);
    this.createWorker();
  }

  /**
   * Process a task using available worker
   */
  async processTask(
    file: File,
    settings: any,
    onProgress?: (progress: any) => void
  ): Promise<any> {
    const taskId = this.generateTaskId();
    
    return new Promise((resolve, reject) => {
      const task: WorkerTask = {
        id: taskId,
        resolve,
        reject,
        onProgress
      };

      this.activeTasks.set(taskId, task);

      // Try to assign to available worker immediately
      const worker = this.getAvailableWorker();
      if (worker) {
        this.assignTaskToWorker(worker, taskId, file, settings);
      } else {
        // Queue the task
        this.taskQueue.push(task);
      }

      // Set timeout for the task
      setTimeout(() => {
        if (this.activeTasks.has(taskId)) {
          this.cancelTask(taskId);
          reject(new Error('Task timeout'));
        }
      }, this.workerTimeout);
    });
  }

  /**
   * Cancel a specific task
   */
  cancelTask(taskId: string): void {
    const task = this.activeTasks.get(taskId);
    if (!task) return;

    // Find worker handling this task and send cancel message
    for (const worker of this.busyWorkers) {
      worker.postMessage({
        id: taskId,
        type: 'cancel',
        payload: {}
      });
    }

    // Remove from active tasks
    this.activeTasks.delete(taskId);
  }

  /**
   * Get an available worker
   */
  private getAvailableWorker(): Worker | null {
    return this.availableWorkers.pop() || null;
  }

  /**
   * Assign task to worker
   */
  private assignTaskToWorker(worker: Worker, taskId: string, file: File, settings: any): void {
    this.busyWorkers.add(worker);
    
    worker.postMessage({
      id: taskId,
      type: 'process',
      payload: { file, settings }
    });
  }

  /**
   * Complete a task and free up the worker
   */
  private completeTask(worker: Worker, taskId: string): void {
    this.activeTasks.delete(taskId);
    this.busyWorkers.delete(worker);
    this.availableWorkers.push(worker);

    // Process next task in queue
    this.processQueue();
  }

  /**
   * Process queued tasks
   */
  private processQueue(): void {
    if (this.taskQueue.length === 0) return;

    const worker = this.getAvailableWorker();
    if (!worker) return;

    const task = this.taskQueue.shift();
    if (!task) return;

    // This would need the original file and settings - 
    // In a real implementation, we'd store these with the task
    console.log('Processing queued task:', task.id);
  }

  /**
   * Remove a worker from the pool
   */
  private removeWorker(worker: Worker): void {
    const workerIndex = this.workers.indexOf(worker);
    if (workerIndex > -1) {
      this.workers.splice(workerIndex, 1);
    }

    const availableIndex = this.availableWorkers.indexOf(worker);
    if (availableIndex > -1) {
      this.availableWorkers.splice(availableIndex, 1);
    }

    this.busyWorkers.delete(worker);
    worker.terminate();
  }

  /**
   * Generate unique task ID
   */
  private generateTaskId(): string {
    return `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get service statistics
   */
  getStats() {
    return {
      totalWorkers: this.workers.length,
      availableWorkers: this.availableWorkers.length,
      busyWorkers: this.busyWorkers.size,
      queuedTasks: this.taskQueue.length,
      activeTasks: this.activeTasks.size
    };
  }

  /**
   * Cleanup all workers
   */
  cleanup(): void {
    // Cancel all active tasks
    for (const taskId of this.activeTasks.keys()) {
      this.cancelTask(taskId);
    }

    // Terminate all workers
    for (const worker of this.workers) {
      worker.terminate();
    }

    this.workers = [];
    this.availableWorkers = [];
    this.busyWorkers.clear();
    this.taskQueue = [];
    this.activeTasks.clear();
  }
}

// Export singleton instance (lazy initialization)
let _workerService: WorkerService | null = null;

export const workerService = {
  getInstance(): WorkerService {
    if (!_workerService) {
      _workerService = WorkerService.getInstance();
    }
    return _workerService;
  },
  
  getStats() {
    return this.getInstance().getStats();
  },
  
  async processTask(file: File, settings: any, onProgress?: (progress: any) => void) {
    return this.getInstance().processTask(file, settings, onProgress);
  },
  
  cancelTask(taskId: string) {
    return this.getInstance().cancelTask(taskId);
  },
  
  cleanup() {
    if (_workerService) {
      _workerService.cleanup();
      _workerService = null;
    }
  }
};

// Export types
export type { WorkerServiceOptions };