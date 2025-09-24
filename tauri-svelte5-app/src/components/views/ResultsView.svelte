<script lang="ts">
  interface Props {
    result?: any;
    onProcessAnother?: () => void;
    cancelled?: boolean;
  }

  const {
    result = null,
    onProcessAnother = () => {},
    cancelled = false
  }: Props = $props();
</script>

<div class="flex-1 flex items-center justify-center p-8">
  <div class="text-center max-w-2xl mx-auto">
    <div class="text-6xl mb-4">
      {#if cancelled}
        <span class="text-orange-500">⚠️</span>
      {:else}
        <span class="text-green-500">✅</span>
      {/if}
    </div>
    <h2 class="text-2xl font-semibold text-gray-800 dark:text-gray-200 mb-4">
      {#if cancelled}
        Processing Cancelled
      {:else}
        Transcription Complete!
      {/if}
    </h2>

    {#if result}
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-soft border border-gray-200 dark:border-gray-700 p-6 mb-6 text-left">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200">
            Transcription Result
          </h3>
          {#if result.outputPath || result.output_path}
            <div class="text-sm text-gray-500 dark:text-gray-400">
              📁 Saved to: <span class="font-mono text-xs">{result.outputPath || result.output_path}</span>
            </div>
          {/if}
        </div>

        {#if result.outputPath || result.output_path}
          <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 mb-4">
            <div class="flex items-center gap-2 text-sm text-blue-700 dark:text-blue-300">
              <span>📁</span>
              <span class="font-medium">File saved to:</span>
            </div>
            <div class="text-sm text-blue-600 dark:text-blue-400 font-mono mt-1 break-all">
              {result.outputPath || result.output_path}
            </div>
          </div>
        {/if}

        <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
          {result.transcribed_text || result.text || 'No transcription text available'}
        </div>
      </div>
    {/if}

    <div class="space-y-4">
      <button
        onclick={onProcessAnother}
        class="btn btn-primary"
      >
        Process Another File
      </button>

      <!-- Export buttons hidden for now -->
      <!-- {#if !cancelled && result}
        <div class="flex justify-center space-x-4">
          <button class="btn btn-secondary">
            Export as TXT
          </button>
          <button class="btn btn-secondary">
            Export as DOCX
          </button>
          <button class="btn btn-secondary">
            Export as PDF
          </button>
        </div>
      {/if} -->
    </div>
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

</style>