<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Icon from '../icons/Icon.svelte';

  interface Props {
    startTime: number;
    currentProgress: number;
    estimatedTotal?: number;
    realElapsed?: number;
    realRemaining?: number;
  }

  const {
    startTime,
    currentProgress,
    estimatedTotal = undefined,
    realElapsed = undefined,
    realRemaining = undefined
  }: Props = $props();

  interface TimeStats {
    elapsed: number;
    remaining: number;
    total: number;
    speed: number;
  }

  let timeStats = $state<TimeStats>({
    elapsed: 0,
    remaining: 0,
    total: 0,
    speed: 0,
  });

  let intervalId: NodeJS.Timeout | null = null;

  function updateStats() {
    const now = Date.now();
    const calculatedElapsed = Math.floor((now - startTime) / 1000);

    // Use real time info if available, otherwise calculate
    let elapsed, remaining;
    
    if (realElapsed !== undefined && realRemaining !== undefined) {
      // Use real time data from Whisper
      elapsed = realElapsed;
      remaining = realRemaining;
      console.log('🕒 Using real time data:', { elapsed, remaining });
    } else if (realElapsed !== undefined) {
      // Use real elapsed, calculate remaining
      elapsed = realElapsed;
      const speed = elapsed > 0 ? currentProgress / elapsed : 0;
      const remainingProgress = 100 - currentProgress;
      remaining = speed > 0 ? Math.ceil(remainingProgress / speed) : 0;
      console.log('🕒 Using real elapsed, calculated remaining:', { elapsed, remaining });
    } else if (realRemaining !== undefined) {
      // Use calculated elapsed, real remaining
      elapsed = calculatedElapsed;
      remaining = realRemaining;
      console.log('🕒 Using calculated elapsed, real remaining:', { elapsed, remaining });
    } else {
      // Calculate both from scratch
      elapsed = calculatedElapsed;
      const speed = elapsed > 0 ? currentProgress / elapsed : 0;
      const remainingProgress = 100 - currentProgress;
      remaining = speed > 0 ? Math.ceil(remainingProgress / speed) : 0;
      console.log('🕒 Using calculated times:', { elapsed, remaining });
    }

    // Calculate processing speed (progress per second)
    const speed = elapsed > 0 ? currentProgress / elapsed : 0;

    // Use provided estimate or calculated total
    const total = estimatedTotal || (elapsed + remaining);

    timeStats = {
      elapsed,
      remaining,
      total,
      speed,
    };
  }

  function formatTime(seconds: number): string {
    if (seconds < 60) {
      return `${seconds}s`;
    } else if (seconds < 3600) {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins}m ${secs}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const mins = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${mins}m`;
    }
  }

  function getSpeedLabel(speed: number): string {
    if (speed > 2) return 'Very Fast';
    if (speed > 1) return 'Fast';
    if (speed > 0.5) return 'Normal';
    if (speed > 0.1) return 'Slow';
    return 'Very Slow';
  }

  function getSpeedColor(speed: number): string {
    if (speed > 2) return 'text-success-600';
    if (speed > 1) return 'text-primary-600';
    if (speed > 0.5) return 'text-warning-600';
    return 'text-error-600';
  }

  function getProgressRate(): string {
    return `${timeStats.speed.toFixed(2)}%/s`;
  }

  onMount(() => {
    updateStats();
    intervalId = setInterval(updateStats, 1000);
  });

  onDestroy(() => {
    if (intervalId) {
      clearInterval(intervalId);
    }
  });

  // Reactive updates when props change
  $effect(() => {
    updateStats();
  });
</script>

<div class="bg-white dark:bg-gray-800 rounded-xl shadow-soft border border-gray-200 dark:border-gray-700 p-6">
  <div class="flex items-center gap-2 mb-4">
    <Icon name="timer" size={20} class="text-primary-500" />
    <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200">
      Time Estimation
    </h3>
  </div>

  <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
    <!-- Elapsed Time -->
    <div class="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
      <div class="flex items-center justify-center gap-2 mb-2">
        <Icon name="clock" size={16} class="text-gray-500" />
        <span class="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">
          Elapsed
        </span>
      </div>
      <div class="text-2xl font-bold text-gray-800 dark:text-gray-200">
        {formatTime(timeStats.elapsed)}
      </div>
    </div>

    <!-- Remaining Time -->
    <div class="text-center p-4 bg-primary-50 dark:bg-primary-900 dark:bg-opacity-20 rounded-lg">
      <div class="flex items-center justify-center gap-2 mb-2">
        <Icon name="timer" size={16} class="text-primary-500" />
        <span class="text-xs font-medium text-primary-600 dark:text-primary-400 uppercase tracking-wide">
          Remaining
        </span>
      </div>
      <div class="text-2xl font-bold text-primary-800 dark:text-primary-200">
        {timeStats.remaining > 0 ? formatTime(timeStats.remaining) : '--'}
      </div>
    </div>

    <!-- Total Estimated -->
    <div class="text-center p-4 bg-secondary-50 dark:bg-secondary-900 dark:bg-opacity-20 rounded-lg">
      <div class="flex items-center justify-center gap-2 mb-2">
        <Icon name="clock" size={16} class="text-secondary-500" />
        <span class="text-xs font-medium text-secondary-600 dark:text-secondary-400 uppercase tracking-wide">
          Total Est.
        </span>
      </div>
      <div class="text-2xl font-bold text-secondary-800 dark:text-secondary-200">
        {formatTime(timeStats.total)}
      </div>
    </div>

    <!-- Processing Speed -->
    <div class="text-center p-4 bg-success-50 dark:bg-success-900 dark:bg-opacity-20 rounded-lg">
      <div class="flex items-center justify-center gap-2 mb-2">
        <Icon name="zap" size={16} class="text-success-500" />
        <span class="text-xs font-medium text-success-600 dark:text-success-400 uppercase tracking-wide">
          Speed
        </span>
      </div>
      <div class="text-lg font-bold text-success-800 dark:text-success-200">
        {getProgressRate()}
      </div>
      <div class="text-xs font-medium {getSpeedColor(timeStats.speed)}">
        {getSpeedLabel(timeStats.speed)}
      </div>
    </div>
  </div>

  <!-- Progress Visualization -->
  <div class="mt-6">
    <div class="flex items-center justify-between mb-2">
      <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
        Overall Progress
      </span>
      <span class="text-sm text-gray-500 dark:text-gray-400">
        {currentProgress.toFixed(1)}%
      </span>
    </div>

    <div class="relative">
      <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
        <div
          class="bg-gradient-to-r from-primary-500 to-primary-600 h-3 rounded-full transition-all duration-500 ease-out relative overflow-hidden"
          style="width: {currentProgress}%"
        >
          <!-- Animated shine effect -->
          <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-pulse"></div>
        </div>
      </div>

      <!-- Progress markers -->
      <div class="flex justify-between mt-1 text-xs text-gray-400">
        <span>0%</span>
        <span>25%</span>
        <span>50%</span>
        <span>75%</span>
        <span>100%</span>
      </div>
    </div>
  </div>

  <!-- ETA Display -->
  {#if timeStats.remaining > 0}
    <div class="mt-4 p-3 bg-primary-50 dark:bg-primary-900 dark:bg-opacity-20 rounded-lg border border-primary-200 dark:border-primary-800">
      <div class="flex items-center gap-2">
        <Icon name="trending-up" size={16} class="text-primary-500" />
        <span class="text-sm font-medium text-primary-800 dark:text-primary-200">
          Estimated completion: {new Date(Date.now() + timeStats.remaining * 1000).toLocaleTimeString()}
        </span>
      </div>
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
</style>