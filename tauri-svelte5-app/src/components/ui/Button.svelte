<script lang="ts">
  import Icon from '../icons/Icon.svelte';
  import type { Snippet } from 'svelte';

  interface Props {
    variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'ghost';
    size?: 'sm' | 'md' | 'lg';
    loading?: boolean;
    disabled?: boolean;
    onclick?: (() => void) | undefined;
    title?: string | undefined;
    class?: string;
    children?: Snippet;
    [key: string]: any;
  }

  const {
    variant = 'primary',
    size = 'md',
    loading = false,
    disabled = false,
    onclick = undefined,
    children,
    title = undefined,
    class: className = '',
    ...restProps
  }: Props = $props();

  const buttonClasses = $derived([
    'btn',
    `btn-${variant}`,
    size !== 'md' ? `btn-${size}` : '',
    className
  ].filter(Boolean).join(' '));
</script>

<button
  class={buttonClasses}
  disabled={disabled || loading}
  onclick={onclick}
  title={title}
  {...restProps}
>
  {#if loading}
    <Icon name="loader2" size={16} class="mr-2" />
  {/if}
  {#if children}
    {@render children()}
  {/if}
</button>

<style>
  .btn {
    @apply inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed;
  }

  .btn-primary {
    @apply bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500;
  }

  .btn-secondary {
    @apply bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600;
  }

  .btn-success {
    @apply bg-success-600 text-white hover:bg-success-700 focus:ring-success-500;
  }

  .btn-warning {
    @apply bg-warning-600 text-white hover:bg-warning-700 focus:ring-warning-500;
  }

  .btn-error {
    @apply bg-error-600 text-white hover:bg-error-700 focus:ring-error-500;
  }

  .btn-ghost {
    @apply bg-transparent text-gray-700 hover:bg-gray-100 focus:ring-gray-500 dark:text-gray-300 dark:hover:bg-gray-800;
  }

  .btn-sm {
    @apply px-3 py-1.5 text-xs;
  }

  .btn-lg {
    @apply px-6 py-3 text-base;
  }

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