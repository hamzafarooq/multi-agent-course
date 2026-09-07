import js from '@eslint/js';
import ts from 'typescript-eslint';

export default [
  { ignores: ['**/dist/**', '**/node_modules/**', 'runs/**', 'reports/**', 'eval/gold/corpus/**'] },
  js.configs.recommended,
  ...ts.configs.recommended,
  {
    files: ['**/*.{ts,tsx}'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }]
    }
  },
  {
    files: ['**/*.mjs', 'scripts/**/*.mjs', 'benchmark/**/*.mjs', 'eval/**/*.mjs', 'quality/**/*.mjs'],
    languageOptions: { ecmaVersion: 2023, sourceType: 'module', globals: {
        process: 'readonly',
        console: 'readonly',
        Buffer: 'readonly',
        fetch: 'readonly',
        Response: 'readonly',
        FormData: 'readonly',
        Blob: 'readonly',
        URL: 'readonly',
        TextDecoder: 'readonly',
        TextEncoder: 'readonly',
        AbortController: 'readonly',
        AbortSignal: 'readonly',
        performance: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly'
      } }
  }
];
