import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
  preprocess: vitePreprocess(),
  compilerOptions: {
    runes: true, // Enable runes for Svelte 5
    compatibility: {
      componentApi: 5 // Use Svelte 5 component API
    }
  }
};