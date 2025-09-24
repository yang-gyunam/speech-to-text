<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import {
    getCurrentView,
    getFiles,
    getCurrentProcessing,
    getResults,
    getProcessingProgress,
    getError,
    getSettings,
    actions
  } from './store/runeStore.svelte.ts';
  import Icon from './components/icons/Icon.svelte';
  import { workflowService, batchWorkflowService, MacOSIntegrationService } from './services';
  import { performanceMonitor } from './utils/performanceMonitor';
  import { memoryManager } from './utils/memoryManager';

  // Lazy load components
  import UploadView from './components/views/UploadView.svelte';
  import ProcessingView from './components/views/ProcessingView.svelte';
  import ResultsView from './components/views/ResultsView.svelte';
  import BatchView from './components/views/BatchView.svelte';

  // Theme state - simplified for now
  let theme = $state('system');

  // Local state
  let isProcessingFiles = $state(false);
  let listenerSetupRef = $state(false);
  let processingCancelled = $state(false);
  let showSuccessToast = $state(false);
  let successMessage = $state('');

  // Theme functions
  function getThemeIconName() {
    switch (theme) {
      case 'light': return 'sun';
      case 'dark': return 'moon';
      case 'system': return 'monitor';
      default: return 'monitor';
    }
  }

  function cycleTheme() {
    const themes = ['light', 'dark', 'system'];
    const currentIndex = themes.indexOf(theme);
    const nextIndex = (currentIndex + 1) % themes.length;
    theme = themes[nextIndex];
  }

  // File handling functions
  async function handleFilesSelected(newFiles) {
    try {
      actions.clearError();
      await workflowService.handleFileSelection(newFiles, settings);
    } catch (err) {
      actions.setError({
        type: 'file',
        message: 'Failed to process file selection',
        details: err instanceof Error ? err.message : 'Unknown error',
        recoverable: true
      });
    }
  }

  let lastProcessedFiles = { paths: [], timestamp: 0 };

  async function handleFilePathsSelected(filePaths) {
    const currentTime = Date.now();
    const pathsString = JSON.stringify(filePaths.sort());
    const lastProcessed = lastProcessedFiles;

    if (currentTime - lastProcessed.timestamp < 3000 &&
        JSON.stringify(lastProcessed.paths.sort()) === pathsString) {
      console.log('🟡 Duplicate file processing detected, skipping');
      return;
    }

    if (isProcessingFiles) {
      console.log('🟡 File processing already in progress, skipping');
      return;
    }

    lastProcessedFiles = {
      paths: filePaths,
      timestamp: currentTime
    };

    isProcessingFiles = true;
    console.log('🟢 Processing file paths:', filePaths);

    try {
      actions.clearError();

      const audioFiles = [];
      for (const filePath of filePaths) {
        try {
          const audioFile = await workflowService.validateSingleFile(filePath);
          audioFiles.push(audioFile);
        } catch (error) {
          console.error('File validation failed:', filePath, error);
        }
      }

      if (audioFiles.length > 0) {
        const existingPaths = files.map(file => file.path);
        const newAudioFiles = audioFiles.filter(file => !existingPaths.includes(file.path));

        if (newAudioFiles.length > 0) {
          actions.addFiles(newAudioFiles);
        }
      } else {
        actions.setError({
          type: 'file',
          message: 'No valid audio files found',
          details: 'Please select supported audio files (.m4a, .wav, .mp3, .aac, .flac)',
          recoverable: true
        });
      }
    } catch (err) {
      actions.setError({
        type: 'file',
        message: 'Failed to process file selection',
        details: err instanceof Error ? err.message : 'Unknown error',
        recoverable: true
      });
    } finally {
      isProcessingFiles = false;
    }
  }

  async function handleStartProcessing() {
    try {
      actions.clearError();

      if (files.length === 1) {
        // Use the original file path from lastProcessedFiles as a workaround
        const originalFilePath = lastProcessedFiles.paths.length > 0 ? lastProcessedFiles.paths[0] : undefined;
        console.log('🔥 Using originalFilePath:', originalFilePath);
        await workflowService.startSingleFileProcessing(files[0], settings, originalFilePath);
      } else if (files.length > 1) {
        actions.setCurrentView('batch');
      }
    } catch (err) {
      console.error('🔥 Error in handleStartProcessing:', err);
      actions.setError({
        type: 'processing',
        message: 'Failed to start processing',
        details: err instanceof Error ? err.message : 'Unknown error',
        recoverable: true
      });
    }
  }

  function handleRemoveFile(fileId) {
    actions.removeFile(fileId);
  }

  async function handleStartBatch(filesToProcess) {
    try {
      actions.clearError();

      batchWorkflowService.initialize({
        onProgress: (progress) => {
          actions.updateProgress({
            stage: 'transcribing',
            progress: progress.overallProgress,
            timestamp: new Date(),
            currentFile: progress.currentFile,
            message: `Processing ${progress.currentFileIndex + 1} of ${progress.totalFiles}`,
            fileIndex: progress.currentFileIndex,
            totalFiles: progress.totalFiles,
            canCancel: true,
          });
        },
        onFileComplete: (fileStatus) => {
          if (fileStatus.result) {
            actions.addResult(fileStatus.result);
          }
        },
        onComplete: (results) => {
          actions.completeProcessing();
          const successful = results.filter(r => r.status === 'completed').length;
          const failed = results.filter(r => r.status === 'error').length;
          console.log(`Batch complete: ${successful} successful, ${failed} failed`);
        },
        onError: (error) => {
          actions.setError(error);
        }
      });

      await batchWorkflowService.startBatchProcessing(filesToProcess, settings);
    } catch (err) {
      actions.setError({
        type: 'processing',
        message: 'Failed to start batch processing',
        details: err instanceof Error ? err.message : 'Unknown error',
        recoverable: true
      });
    }
  }

  async function handleCancelProcessing() {
    try {
      processingCancelled = true;
      if (currentView === 'batch' && batchWorkflowService.isProcessing()) {
        await batchWorkflowService.cancelBatchProcessing();
      } else {
        await workflowService.cancelProcessing();
      }
    } catch (err) {
      actions.setError({
        type: 'system',
        message: 'Failed to cancel processing',
        details: err instanceof Error ? err.message : 'Unknown error',
        recoverable: false
      });
    }
  }

  function handleProcessAnother() {
    processingCancelled = false; // Reset cancelled state
    actions.clearFiles();
    workflowService.resetWorkflow();
  }

  function showSuccess(message: string) {
    successMessage = message;
    showSuccessToast = true;
    setTimeout(() => {
      showSuccessToast = false;
    }, 4000); // Hide after 4 seconds
  }

  // Navigation helpers
  function getViewTitle() {
    switch (currentView) {
      case 'upload': return 'Upload Files';
      case 'processing': return 'Processing';
      case 'results': return 'Results';
      case 'batch': return 'Batch Processing';
      default: return 'Speech to Text';
    }
  }

  const currentView = $derived(getCurrentView());
  const files = $derived(getFiles());
  const currentProcessing = $derived(getCurrentProcessing());
  const results = $derived(getResults());
  const processingProgress = $derived(getProcessingProgress());
  const error = $derived(getError());
  const settings = $derived(getSettings());

  const canGoBack = $derived(currentView !== 'upload');

  // Initialization
  onMount(() => {
    if (listenerSetupRef) {
      console.log('🟡 Listener already set up, skipping...');
      return;
    }
    listenerSetupRef = true;
    console.log('🔥 First time setup, continuing...');

    performanceMonitor.startMeasure('app-initialization');

    const memoryUnsubscribe = memoryManager.onMemoryUsageChange((usage) => {
      if (usage.percentage > 80) {
        console.warn('High memory usage detected:', usage);
      }
    });

    MacOSIntegrationService.initialize();

    console.log('🔥 About to call workflowService.initialize');
    workflowService.initialize({
      onViewChange: (view) => {
        console.log('🔥 App.svelte onViewChange called with:', view);
        actions.setCurrentView(view);
        console.log('🔥 setCurrentView called with:', view);
      },
      onFilesAdded: (audioFiles) => {
        actions.addFiles(audioFiles);
      },
      onProcessingStart: () => {
        // Processing start is handled by the workflow service
      },
      onProgress: (progress) => {
        actions.updateProgress(progress);
      },
      onComplete: (result) => {
        actions.addResult(result);
        actions.completeProcessing();

        // Show success message
        showSuccess('✅ Transcription completed successfully!');
      },
      onError: (errorState) => {
        actions.setError(errorState);
      },
      onCancel: () => {
        actions.completeProcessing();
      }
    });

    performanceMonitor.endMeasure('app-initialization');

    return () => {
      listenerSetupRef = false;
      workflowService.cleanup();
      MacOSIntegrationService.cleanup();
      memoryUnsubscribe();
      performanceMonitor.cleanup();
    };
  });
</script>

<div class="min-h-screen bg-gray-100 dark:bg-gray-900 flex flex-col transition-colors responsive-text">
  <!-- Skip Links -->
  <a href="#main-content" class="skip-link">
    Skip to main content
  </a>
  <a href="#navigation" class="skip-link">
    Skip to navigation
  </a>

  <!-- Header -->
  <header
    class="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700"
  >
    <div class="flex items-center justify-between px-6 py-4">
      <div class="flex items-center gap-4">
        {#if canGoBack}
          <button
            onclick={() => actions.setCurrentView('upload')}
            class="p-2 hover:bg-gray-100 rounded-md transition-colors"
          >
            <Icon name="x" size={20} />
          </button>
        {/if}
        <div class="flex items-center gap-2">
          <Icon name="menu" size={24} class="text-primary-500" />
          <h1 class="text-xl font-semibold text-gray-800 dark:text-gray-200">
            Speech to Text - {getViewTitle()}
          </h1>
        </div>
      </div>

      <!-- Navigation icons hidden for cleaner UI -->
      <!-- <nav
        id="navigation"
        class="flex items-center gap-2"
        role="navigation"
        aria-label="Main navigation"
      >
        <button
          onclick={cycleTheme}
          class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
          title="Current theme: {theme}"
        >
          <Icon name={getThemeIconName()} size={20} class="text-gray-600 dark:text-gray-400" />
        </button>
        <button
          class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
          aria-label="Open settings"
        >
          <Icon name="settings" size={20} class="text-gray-600 dark:text-gray-400" />
        </button>
      </nav> -->
    </div>
  </header>

  <!-- Error Display -->
  {#if error}
    <div class="bg-error-50 dark:bg-error-900 border-l-4 border-error-400 p-4 mx-6 mt-4 rounded animate-slide-down">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-medium text-error-800 dark:text-error-200">
            {error.type.charAt(0).toUpperCase() + error.type.slice(1)} Error
          </h3>
          <p class="text-sm text-error-700 dark:text-error-300">{error.message}</p>
          {#if error.details}
            <details class="mt-2">
              <summary class="text-xs text-error-600 dark:text-error-400 cursor-pointer">Details</summary>
              <p class="text-xs text-error-600 dark:text-error-400 mt-1">{error.details}</p>
            </details>
          {/if}
        </div>
        <button
          onclick={() => actions.clearError()}
          class="text-error-400 hover:text-error-600 dark:text-error-500 dark:hover:text-error-400 transition-colors"
        >
          <Icon name="x" size={16} />
        </button>
      </div>
    </div>
  {/if}

  <!-- Success Toast -->
  {#if showSuccessToast}
    <div class="bg-success-50 dark:bg-success-900 border-l-4 border-success-400 p-4 mx-6 mt-4 rounded animate-slide-down">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-medium text-success-800 dark:text-success-200">
            Success
          </h3>
          <p class="text-sm text-success-700 dark:text-success-300">{successMessage}</p>
        </div>
        <button
          onclick={() => showSuccessToast = false}
          class="text-success-400 hover:text-success-600 dark:text-success-500 dark:hover:text-success-400 transition-colors"
        >
          <Icon name="x" size={16} />
        </button>
      </div>
    </div>
  {/if}

  <!-- Main Content -->
  <main
    id="main-content"
    class="flex-1 flex flex-col"
    aria-label="Main content area"
  >
    {#if currentView === 'upload'}
      <UploadView
        selectedFiles={files}
        onFilesSelected={handleFilesSelected}
        onFilePathsSelected={handleFilePathsSelected}
        onStartProcessing={handleStartProcessing}
        onRemoveFile={handleRemoveFile}
        modelSize={settings.modelSize}
        onModelSizeChange={(newModelSize) => actions.updateSettings({ modelSize: newModelSize })}
      />
    {:else if currentView === 'processing'}
      <ProcessingView
        progress={processingProgress}
        currentFile={currentProcessing?.files[currentProcessing.currentFileIndex]?.name}
        onCancel={handleCancelProcessing}
      />
    {:else if currentView === 'results'}
      <ResultsView
        result={results[results.length - 1] || null}
        onProcessAnother={handleProcessAnother}
        cancelled={processingCancelled}
      />
    {:else if currentView === 'batch'}
      <BatchView
        {files}
        processingJob={currentProcessing}
        onRemoveFile={(fileId: string) => actions.removeFile(fileId)}
        onReorderFiles={(reorderedFiles: any[]) => {
          console.log('Reordered files:', reorderedFiles);
        }}
        onStartBatch={() => {
          const filesToProcess = files.map(f => new File([], f.name));
          handleStartBatch(filesToProcess);
        }}
        onRetryFailed={async () => {
          try {
            await batchWorkflowService.retryFailedFiles(settings);
          } catch (err) {
            actions.setError({
              id: `error-${Date.now()}`,
              type: 'processing',
              severity: 'medium',
              message: 'Failed to retry failed files',
              details: err instanceof Error ? err.message : 'Unknown error',
              recoverable: true,
              timestamp: new Date()
            });
          }
        }}
        onClearAll={actions.clearFiles}
      />
    {/if}
  </main>
</div>

<style>
  .skip-link {
    position: absolute;
    top: -40px;
    left: 6px;
    background: white;
    color: black;
    padding: 8px;
    text-decoration: none;
    z-index: 1000;
  }

  .skip-link:focus {
    top: 6px;
  }

  @keyframes slide-down {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .animate-slide-down {
    animation: slide-down 0.3s ease-out;
  }
</style>