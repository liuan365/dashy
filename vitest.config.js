import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    // Use happy-dom for faster DOM simulation
    environment: 'happy-dom',

    // Make test functions available globally (describe, it, expect, etc.)
    globals: true,

    // Setup file for global test configuration
    setupFiles: ['./tests/setup.js'],

    // Include patterns
    include: ['tests/**/*.{test,spec}.{js,ts}', 'src/**/*.{test,spec}.{js,ts}'],

    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'tests/',
        '*.config.js',
        'dist/',
        '.github/',
        'docs/',
      ],
    },
  },

  resolve: {
    // Match the alias configuration from vue.config.js
    alias: {
      '@': path.resolve(__dirname, './src'),
      'vue': 'vue/dist/vue.esm.js', // Use the full build for tests
    },
  },
});
