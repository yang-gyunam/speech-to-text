/**
 * Web Worker for background audio processing tasks
 */

interface WorkerMessage {
  id: string;
  type: 'process' | 'cancel' | 'progress';
  payload: any;
}

interface WorkerResponse {
  id: string;
  type: 'success' | 'error' | 'progress';
  payload: any;
}

interface ProcessingTask {
  id: string;
  file: File;
  settings: any;
  chunks?: ArrayBuffer[];
}

// Worker state
let currentTask: ProcessingTask | null = null;
let isProcessing = false;

// Message handler
self.onmessage = async (event: MessageEvent<WorkerMessage>) => {
  const { id, type, payload } = event.data;

  try {
    switch (type) {
      case 'process':
        await handleProcessingTask(id, payload);
        break;
      
      case 'cancel':
        handleCancelTask(id);
        break;
      
      case 'progress':
        // Handle progress requests
        sendProgress(id, getCurrentProgress());
        break;
      
      default:
        sendError(id, `Unknown message type: ${type}`);
    }
  } catch (error) {
    sendError(id, error instanceof Error ? error.message : 'Unknown error');
  }
};

/**
 * Handle audio processing task
 */
async function handleProcessingTask(id: string, payload: any): Promise<void> {
  if (isProcessing) {
    sendError(id, 'Worker is already processing a task');
    return;
  }

  isProcessing = true;
  currentTask = {
    id,
    file: payload.file,
    settings: payload.settings
  };

  try {
    // Send initial progress
    sendProgress(id, { stage: 'initializing', progress: 0 });

    // Process file in chunks for memory efficiency
    const chunks = await processFileInChunks(payload.file, id);
    currentTask.chunks = chunks;

    // Send processing progress
    sendProgress(id, { stage: 'processing', progress: 50 });

    // Simulate processing (in real implementation, this would call Tauri commands)
    const result = await simulateProcessing(chunks, payload.settings, id);

    // Send completion
    sendSuccess(id, result);
  } catch (error) {
    sendError(id, error instanceof Error ? error.message : 'Processing failed');
  } finally {
    isProcessing = false;
    currentTask = null;
  }
}

/**
 * Process file in chunks to manage memory
 */
async function processFileInChunks(file: File, taskId: string): Promise<ArrayBuffer[]> {
  const chunkSize = 1024 * 1024 * 2; // 2MB chunks
  const chunks: ArrayBuffer[] = [];
  const totalChunks = Math.ceil(file.size / chunkSize);

  for (let i = 0; i < totalChunks; i++) {
    // Check if task was cancelled
    if (!isProcessing || currentTask?.id !== taskId) {
      throw new Error('Task cancelled');
    }

    const start = i * chunkSize;
    const end = Math.min(start + chunkSize, file.size);
    const blob = file.slice(start, end);
    const arrayBuffer = await blob.arrayBuffer();
    
    chunks.push(arrayBuffer);

    // Send progress update
    const progress = ((i + 1) / totalChunks) * 30; // 30% for chunking
    sendProgress(taskId, { 
      stage: 'chunking', 
      progress,
      message: `Processing chunk ${i + 1} of ${totalChunks}`
    });

    // Yield control to prevent blocking
    await new Promise(resolve => setTimeout(resolve, 0));
  }

  return chunks;
}

/**
 * Simulate audio processing (replace with actual Tauri calls)
 */
async function simulateProcessing(
  chunks: ArrayBuffer[], 
  settings: any, 
  taskId: string
): Promise<any> {
  const totalSteps = 100;
  
  for (let step = 0; step < totalSteps; step++) {
    // Check if task was cancelled
    if (!isProcessing || currentTask?.id !== taskId) {
      throw new Error('Task cancelled');
    }

    // Simulate processing work
    await new Promise(resolve => setTimeout(resolve, 50));

    // Send progress update
    const progress = 50 + (step / totalSteps) * 50; // 50-100%
    sendProgress(taskId, {
      stage: 'transcribing',
      progress,
      message: `Processing step ${step + 1} of ${totalSteps}`
    });
  }

  // Return mock result
  return {
    transcribedText: 'Mock transcription result from worker',
    metadata: {
      processingTime: Date.now(),
      chunks: chunks.length,
      settings
    }
  };
}

/**
 * Handle task cancellation
 */
function handleCancelTask(id: string): void {
  if (currentTask?.id === id) {
    isProcessing = false;
    currentTask = null;
    sendSuccess(id, { cancelled: true });
  }
}

/**
 * Get current processing progress
 */
function getCurrentProgress(): any {
  if (!currentTask) {
    return { stage: 'idle', progress: 0 };
  }

  return {
    stage: 'processing',
    progress: 50, // Mock progress
    taskId: currentTask.id
  };
}

/**
 * Send success response
 */
function sendSuccess(id: string, payload: any): void {
  const response: WorkerResponse = {
    id,
    type: 'success',
    payload
  };
  self.postMessage(response);
}

/**
 * Send error response
 */
function sendError(id: string, message: string): void {
  const response: WorkerResponse = {
    id,
    type: 'error',
    payload: { message }
  };
  self.postMessage(response);
}

/**
 * Send progress update
 */
function sendProgress(id: string, payload: any): void {
  const response: WorkerResponse = {
    id,
    type: 'progress',
    payload
  };
  self.postMessage(response);
}

// Export for TypeScript (won't be used in worker context)
export {};