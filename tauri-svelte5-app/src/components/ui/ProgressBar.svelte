<script lang="ts">
  interface Props {
    value: number; // 0-100
    size?: 'sm' | 'md' | 'lg';
    color?: 'primary' | 'success' | 'warning' | 'error';
    showLabel?: boolean;
    label?: string;
    class?: string;
    [key: string]: any;
  }

  const {
    value,
    size = 'md',
    color = 'primary',
    showLabel = false,
    label = undefined,
    class: className = '',
    ...restProps
  }: Props = $props();

  const sizeClasses = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4',
  };

  const colorClasses = {
    primary: 'bg-primary-600',
    success: 'bg-success-600',
    warning: 'bg-warning-600',
    error: 'bg-error-600',
  };

  const clampedValue = $derived(Math.max(0, Math.min(100, value)));
</script>

<div class="space-y-2 {className}" {...restProps}>
  {#if showLabel || label}
    <div class="flex justify-between items-center text-sm">
      <span class="text-gray-700 dark:text-gray-300">
        {label || 'Progress'}
      </span>
      {#if showLabel}
        <span class="text-gray-500 dark:text-gray-400">
          {Math.round(clampedValue)}%
        </span>
      {/if}
    </div>
  {/if}
  <div class="progress-bar {sizeClasses[size]}">
    <div
      class="progress-fill {colorClasses[color]}"
      style="width: {clampedValue}%"
    ></div>
  </div>
</div>

<style>
  .progress-bar {
    @apply w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden;
  }

  .progress-fill {
    @apply h-full transition-all duration-300 ease-out rounded-full;
  }
</style>