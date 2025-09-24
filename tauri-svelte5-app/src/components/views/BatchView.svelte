<script lang="ts">
  interface Props {
    files?: any[];
    processingJob?: any;
    onRemoveFile?: () => void;
    onReorderFiles?: () => void;
    onStartBatch?: () => void;
    onRetryFailed?: () => void;
    onClearAll?: () => void;
  }

  const {
    files = [],
    processingJob = null,
    onRemoveFile = () => {},
    onReorderFiles = () => {},
    onStartBatch = () => {},
    onRetryFailed = () => {},
    onClearAll = () => {}
  }: Props = $props();
</script>

<div class="flex-1 p-8">
  <div class="max-w-4xl mx-auto">
    <div class="text-center mb-8">
      <h2 class="text-2xl font-semibold text-gray-800 dark:text-gray-200 mb-2">
        Batch Processing
      </h2>
      <p class="text-gray-600 dark:text-gray-400">
        Process multiple audio files simultaneously
      </p>
    </div>

    {#if files.length === 0}
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-soft border border-gray-200 dark:border-gray-700 p-12 text-center">
        <div class="text-6xl text-gray-400 mb-4">📂</div>
        <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200 mb-2">
          No files selected
        </h3>
        <p class="text-gray-500 dark:text-gray-400 mb-4">
          Add multiple audio files to start batch processing
        </p>
        <button class="btn btn-primary">
          Add Files
        </button>
      </div>
    {:else}
      <div class="space-y-6">
        <!-- File List -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-soft border border-gray-200 dark:border-gray-700">
          <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200">
                Files ({files.length})
              </h3>
              <div class="space-x-2">
                <button class="btn btn-secondary btn-sm" onclick={onClearAll}>
                  Clear All
                </button>
                <button class="btn btn-primary" onclick={onStartBatch}>
                  Start Batch Processing
                </button>
              </div>
            </div>
          </div>

          <div class="p-6">
            <div class="space-y-3">
              {#each files as file, index (file.id || index)}
                <div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div class="flex items-center space-x-3">
                    <div class="text-lg">🎵</div>
                    <div>
                      <div class="font-medium text-gray-800 dark:text-gray-200">
                        {file.name || `File ${index + 1}`}
                      </div>
                      <div class="text-sm text-gray-500 dark:text-gray-400">
                        Audio file
                      </div>
                    </div>
                  </div>

                  <div class="flex items-center space-x-2">
                    <div class="text-sm text-gray-500 dark:text-gray-400">
                      Ready
                    </div>
                    <button
                      class="text-gray-400 hover:text-red-500 transition-colors"
                      onclick={() => onRemoveFile(file.id || index)}
                    >
                      ❌
                    </button>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        </div>

        <!-- Processing Status -->
        {#if processingJob}
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-soft border border-gray-200 dark:border-gray-700 p-6">
            <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200 mb-4">
              Processing Status
            </h3>
            <div class="text-center py-8">
              <div class="text-4xl mb-4">⚙️</div>
              <p class="text-gray-600 dark:text-gray-400">
                Batch processing is running...
              </p>
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .shadow-soft {
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  }

  .btn {
    @apply inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed;
  }

  .btn-primary {
    @apply bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500;
  }

  .btn-secondary {
    @apply bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600;
  }

  .btn-sm {
    @apply px-3 py-1.5 text-xs;
  }
</style>