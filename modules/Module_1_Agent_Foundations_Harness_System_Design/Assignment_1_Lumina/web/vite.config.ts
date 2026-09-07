import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The UI talks to the gateway and nothing else. In dev, VITE_API_URL points at :8787;
// in production it points at your deployed gateway. No key is ever read here: only
// VITE_* variables reach the browser, and none of them is a secret.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true },
  build: { outDir: 'dist', sourcemap: true }
});
