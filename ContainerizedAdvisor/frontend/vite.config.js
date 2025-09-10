import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'motion-utils-fix',
      resolveId(id, importer) {
        if (id === './globalThis-config.mjs' && importer?.includes('motion-utils')) {
          return path.resolve(importer, '../global-config.mjs')
        }
      }
    }
  ],
  build: {
    rollupOptions: {
      external: (id) => {
        // Don't externalize anything, let Vite handle it
        return false
      }
    }
  },
  optimizeDeps: {
    include: ['motion-utils', 'framer-motion']
  },
  define: {
    global: 'globalThis'
  },
  envPrefix: 'VITE_',
  resolve: {
    alias: {
      'motion-utils': path.resolve(__dirname, 'node_modules/motion-utils/dist/es/index.mjs')
    }
  }
})