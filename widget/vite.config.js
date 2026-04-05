import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    lib: {
      entry: 'src/index.js',
      name: 'AvatarWidget',
      fileName: 'widget',
      formats: ['iife']
    },
    rollupOptions: {
      output: { inlineDynamicImports: true }
    }
  }
})
