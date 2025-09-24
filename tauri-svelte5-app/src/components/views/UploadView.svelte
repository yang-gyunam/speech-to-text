<script lang="ts">
  import { tauriService } from '../../services/tauriService';
  import Icon from '../icons/Icon.svelte';

  interface Props {
    selectedFiles?: any[];
    onFilesSelected?: (files: any[]) => void;
    onFilePathsSelected?: (filePaths: string[]) => void;
    onStartProcessing?: () => void;
    onRemoveFile?: (fileId: string) => void;
    modelSize?: 'tiny' | 'base' | 'small' | 'medium' | 'large';
    onModelSizeChange?: (modelSize: 'tiny' | 'base' | 'small' | 'medium' | 'large') => void;
  }

  const {
    selectedFiles = [],
    onFilesSelected = () => {},
    onFilePathsSelected = () => {},
    onStartProcessing = () => {},
    onRemoveFile = () => {},
    modelSize = 'base',
    onModelSizeChange = () => {}
  }: Props = $props();

  async function handleSelectFiles() {
    try {
      const filePaths = await tauriService.selectFiles();
      if (filePaths && filePaths.length > 0) {
        console.log('🔥 Selected file paths:', filePaths);
        onFilePathsSelected(filePaths);
      }
    } catch (error) {
      console.error('Failed to select files:', error);
    }
  }
</script>

<div class="flex-1 flex items-center justify-center p-8">
  <div class="text-center">
    <h2 class="text-2xl font-semibold text-gray-800 dark:text-gray-200 mb-4">
      Upload Audio Files
    </h2>
    <p class="text-gray-600 dark:text-gray-400 mb-8">
      Select audio files to transcribe with Whisper AI
    </p>

    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-soft border-2 border-dashed border-gray-300 dark:border-gray-600 p-12">
      <div class="space-y-4">
        <div class="text-6xl text-gray-400 mb-4">📁</div>
        <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200">
          Choose audio files
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Supports .m4a, .wav, .mp3, .aac, .flac files
        </p>

        <div class="space-y-4">
          {#if selectedFiles.length === 0}
            <button
              onclick={handleSelectFiles}
              class="btn btn-primary"
            >
              <Icon name="folder-open" size={16} class="mr-2" />
              Select Files
            </button>
          {/if}

          <!-- Quality Selection -->
          <div class="w-full max-w-xs mx-auto">
            <label for="model-size-select" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Transcription Quality
            </label>
            <select
              id="model-size-select"
              value={modelSize}
              onchange={(e) => onModelSizeChange((e.target as HTMLSelectElement).value as any)}
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="tiny">Tiny (Fastest, Lower Quality)</option>
              <option value="base">Base (Balanced)</option>
              <option value="small">Small (Good Quality)</option>
              <option value="medium">Medium (Better Quality)</option>
              <option value="large">Large (Best Quality, Slowest)</option>
            </select>
            <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Higher quality models provide better accuracy but take longer to process
            </p>
          </div>

          {#if selectedFiles.length > 0}
            <button
              onclick={onStartProcessing}
              class="btn btn-success"
            >
              <Icon name="play" size={16} class="mr-2" />
              Start Processing
            </button>
          {/if}
        </div>
      </div>
    </div>

    {#if selectedFiles.length > 0}
      <div class="mt-6">
        <div class="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <h4 class="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3">
            Selected Files ({selectedFiles.length})
          </h4>
          <div class="space-y-2">
            {#each selectedFiles as file}
              <div class="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
                <div class="flex items-center gap-2">
                  <Icon name="file-audio" size={16} class="text-primary-500" />
                  <span class="text-sm text-gray-700 dark:text-gray-300">{file.name}</span>
                </div>
                <button
                  onclick={() => onRemoveFile(file.id)}
                  class="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                  title="Remove file"
                >
                  <Icon name="x" size={14} class="text-gray-500" />
                </button>
              </div>
            {/each}
          </div>
        </div>
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

  .btn-success {
    @apply bg-success-600 text-white hover:bg-success-700 focus:ring-success-500;
  }
</style>