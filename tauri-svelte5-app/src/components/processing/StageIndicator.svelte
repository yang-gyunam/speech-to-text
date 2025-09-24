<script lang="ts">
  import Icon from '../icons/Icon.svelte';

  type ProcessingStage = 'initializing' | 'loading_model' | 'preprocessing' | 'transcribing' | 'postprocessing' | 'saving';

  interface Props {
    currentStage: ProcessingStage;
    progress: number;
  }

  const { currentStage, progress }: Props = $props();

  interface StageInfo {
    id: ProcessingStage;
    label: string;
    description: string;
    icon: string;
    estimatedDuration: number;
  }

  const stages: StageInfo[] = [
    {
      id: 'initializing',
      label: 'Initializing',
      description: 'Preparing for processing',
      icon: 'clock',
      estimatedDuration: 2,
    },
    {
      id: 'loading_model',
      label: 'Loading Model',
      description: 'Loading Whisper AI model',
      icon: 'brain',
      estimatedDuration: 15,
    },
    {
      id: 'preprocessing',
      label: 'Preprocessing',
      description: 'Analyzing audio file',
      icon: 'audio-waveform',
      estimatedDuration: 5,
    },
    {
      id: 'transcribing',
      label: 'Transcribing',
      description: 'Converting speech to text',
      icon: 'cpu',
      estimatedDuration: 60,
    },
    {
      id: 'postprocessing',
      label: 'Post-processing',
      description: 'Formatting results',
      icon: 'file-text',
      estimatedDuration: 3,
    },
    {
      id: 'saving',
      label: 'Saving',
      description: 'Saving transcription',
      icon: 'save',
      estimatedDuration: 2,
    },
  ];

  const currentStageIndex = $derived(stages.findIndex(stage => stage.id === currentStage));

  function getStageStatus(index: number) {
    if (index < currentStageIndex) return 'completed';
    if (index === currentStageIndex) return 'active';
    return 'pending';
  }

  function getStageClasses(status: string) {
    const baseClasses = 'flex items-center gap-4 p-4 rounded-lg transition-all duration-300';

    switch (status) {
      case 'completed':
        return `${baseClasses} bg-success-50 dark:bg-success-900 dark:bg-opacity-20 border border-success-200 dark:border-success-800`;
      case 'active':
        return `${baseClasses} bg-primary-50 dark:bg-primary-900 dark:bg-opacity-20 border border-primary-200 dark:border-primary-800 shadow-md`;
      default:
        return `${baseClasses} bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700`;
    }
  }
</script>

<div class="bg-white dark:bg-gray-800 rounded-xl shadow-soft border border-gray-200 dark:border-gray-700 p-6">
  <div class="flex items-center justify-between mb-6">
    <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200">
      Processing Stages
    </h3>
    <div class="text-sm text-gray-500 dark:text-gray-400">
      Stage {currentStageIndex + 1} of {stages.length}
    </div>
  </div>

  <div class="space-y-3">
    {#each stages as stage, index (stage.id)}
    {@const status = getStageStatus(index)}
    {@const isActive = status === 'active'}

    <div class={getStageClasses(status)}>
      <div class="flex-shrink-0">
        {#if status === 'completed'}
          <Icon name="check-circle" size={20} class="text-success-500" />
        {:else if status === 'active'}
          <Icon name="loader2" size={20} class="text-primary-500" />
        {:else}
          <Icon name={stage.icon} size={20} class="text-gray-400" />
        {/if}
      </div>

      <div class="flex-1 min-w-0">
        <div class="flex items-center justify-between mb-1">
          <h4 class="text-sm font-medium {
            status === 'completed'
              ? 'text-success-800 dark:text-success-200'
              : status === 'active'
                ? 'text-primary-800 dark:text-primary-200'
                : 'text-gray-600 dark:text-gray-400'
          }">
            {stage.label}
          </h4>

          {#if status === 'active'}
            <span class="text-xs text-primary-600 dark:text-primary-400 font-medium">
              {Math.round(progress)}%
            </span>
          {/if}

          {#if status === 'completed'}
            <span class="text-xs text-success-600 dark:text-success-400 font-medium">
              ✓ Complete
            </span>
          {/if}
        </div>

        <p class="text-xs {
          status === 'completed'
            ? 'text-success-600 dark:text-success-400'
            : status === 'active'
              ? 'text-primary-600 dark:text-primary-400'
              : 'text-gray-500 dark:text-gray-500'
        }">
          {stage.description}
        </p>

        {#if isActive}
          <div class="mt-2">
            <div class="w-full bg-primary-100 dark:bg-primary-900 rounded-full h-1.5">
              <div
                class="bg-primary-500 h-1.5 rounded-full transition-all duration-300 ease-out"
                style="width: {progress}%"
              ></div>
            </div>
          </div>
        {/if}
      </div>

      <div class="flex-shrink-0 text-xs text-gray-400 dark:text-gray-500">
        ~{stage.estimatedDuration}s
      </div>
    </div>
    {/each}
  </div>
</div>

<style>
  .animate-spin {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
</style>