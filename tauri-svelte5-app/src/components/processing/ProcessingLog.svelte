<script lang="ts">
  import { onMount, tick } from 'svelte';
  import Icon from '../icons/Icon.svelte';
  import Button from '../ui/Button.svelte';

  interface LogEntry {
    id: string;
    timestamp: Date;
    level: 'info' | 'warning' | 'error' | 'success';
    message: string;
    details?: string;
  }

  interface Props {
    entries?: LogEntry[];
    isProcessing?: boolean;
    maxHeight?: string;
  }

  const {
    entries = [],
    isProcessing = false,
    maxHeight = 'max-h-96'
  }: Props = $props();

  let isExpanded = $state(true);
  let autoScroll = $state(true);
  let logContainer = $state<HTMLDivElement>();
  let endOfLogRef = $state<HTMLDivElement>();

  // Auto-scroll to bottom when new entries are added
  $effect(async () => {
    if (autoScroll && endOfLogRef && entries.length > 0) {
      await tick(); // Wait for DOM update
      endOfLogRef.scrollIntoView({ behavior: 'smooth' });
    }
  });

  function handleScroll() {
    if (!logContainer) return;

    const { scrollTop, scrollHeight, clientHeight } = logContainer;
    const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;
    autoScroll = isAtBottom;
  }

  function formatTime(date: Date): string {
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }

  function getLevelIcon(level: LogEntry['level']): string {
    switch (level) {
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      default: return 'ℹ️';
    }
  }

  function getLevelClasses(level: LogEntry['level']): string {
    switch (level) {
      case 'success': return 'text-success-600 dark:text-success-400';
      case 'warning': return 'text-warning-600 dark:text-warning-400';
      case 'error': return 'text-error-600 dark:text-error-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  }

  async function copyLogToClipboard() {
    const logText = entries
      .map(entry => `[${formatTime(entry.timestamp)}] ${entry.level.toUpperCase()}: ${entry.message}`)
      .join('\n');

    try {
      await navigator.clipboard.writeText(logText);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  }

  function downloadLog() {
    const logText = entries
      .map(entry => `[${formatTime(entry.timestamp)}] ${entry.level.toUpperCase()}: ${entry.message}`)
      .join('\n');

    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `processing-log-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  async function scrollToBottom() {
    autoScroll = true;
    await tick();
    if (endOfLogRef) {
      endOfLogRef.scrollIntoView({ behavior: 'smooth' });
    }
  }
</script>

<div class="bg-white dark:bg-gray-800 rounded-xl shadow-soft border border-gray-200 dark:border-gray-700">
  <!-- Header -->
  <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Icon name="terminal" size={20} class="text-gray-500" />
        <h3 class="text-sm font-medium text-gray-800 dark:text-gray-200">
          Processing Log
        </h3>
        {#if isProcessing}
          <div class="flex items-center gap-1">
            <div class="w-2 h-2 bg-primary-500 rounded-full animate-pulse"></div>
            <span class="text-xs text-primary-600 dark:text-primary-400">Live</span>
          </div>
        {/if}
      </div>

      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onclick={copyLogToClipboard}
          title="Copy log to clipboard"
        >
          <Icon name="copy" size={16} class="mr-1" />
          Copy
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onclick={downloadLog}
          title="Download log file"
        >
          <Icon name="download" size={16} class="mr-1" />
          Download
        </Button>

        <button
          onclick={() => isExpanded = !isExpanded}
          class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
        >
          {#if isExpanded}
            <Icon name="chevron-up" size={16} class="text-gray-500" />
          {:else}
            <Icon name="chevron-down" size={16} class="text-gray-500" />
          {/if}
        </button>
      </div>
    </div>
  </div>

  <!-- Log Content -->
  {#if isExpanded}
    <div class="relative">
      <div
        bind:this={logContainer}
        onscroll={handleScroll}
        class="overflow-y-auto scrollbar-thin p-4 space-y-2 {maxHeight}"
      >
        {#if entries.length === 0}
          <div class="text-center py-8 text-gray-500 dark:text-gray-400">
            <Icon name="terminal" size={32} class="mx-auto mb-2 opacity-50" />
            <p class="text-sm">No log entries yet</p>
          </div>
        {:else}
          {#each entries as entry (entry.id)}
            <div class="flex items-start gap-3 text-sm font-mono hover:bg-gray-50 dark:hover:bg-gray-700 p-2 rounded transition-colors">
              <span class="text-xs text-gray-400 dark:text-gray-500 mt-0.5 flex-shrink-0">
                {formatTime(entry.timestamp)}
              </span>

              <span class="flex-shrink-0 mt-0.5">
                {getLevelIcon(entry.level)}
              </span>

              <div class="flex-1 min-w-0">
                <span class="{getLevelClasses(entry.level)}">
                  {entry.message}
                </span>
                {#if entry.details}
                  <div class="text-xs text-gray-500 dark:text-gray-400 mt-1 pl-2 border-l-2 border-gray-200 dark:border-gray-600">
                    {entry.details}
                  </div>
                {/if}
              </div>
            </div>
          {/each}
        {/if}
        <div bind:this={endOfLogRef}></div>
      </div>

      <!-- Auto-scroll indicator -->
      {#if !autoScroll && entries.length > 0}
        <div class="absolute bottom-4 right-4">
          <button
            onclick={scrollToBottom}
            class="bg-primary-500 text-white px-3 py-1 rounded-full text-xs hover:bg-primary-600 transition-colors shadow-lg"
          >
            Scroll to bottom
          </button>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .shadow-soft {
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  }

  .animate-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }

  .scrollbar-thin {
    scrollbar-width: thin;
    scrollbar-color: rgba(156, 163, 175, 0.5) transparent;
  }

  .scrollbar-thin::-webkit-scrollbar {
    width: 6px;
  }

  .scrollbar-thin::-webkit-scrollbar-track {
    background: transparent;
  }

  .scrollbar-thin::-webkit-scrollbar-thumb {
    background-color: rgba(156, 163, 175, 0.5);
    border-radius: 3px;
  }

  .scrollbar-thin::-webkit-scrollbar-thumb:hover {
    background-color: rgba(156, 163, 175, 0.7);
  }
</style>