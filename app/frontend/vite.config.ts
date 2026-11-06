import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    rollupOptions: {
      onwarn(warning, warn) {
        // This is a client-only SPA; React server-component directives do not apply.
        if (warning.code === 'MODULE_LEVEL_DIRECTIVE' && warning.message.includes('use client')) return;
        warn(warning);
      },
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) return id.includes('/antd/') || id.includes('/@ant-design/') || id.includes('/@rc-component/') ? 'antd' : 'vendor';
        },
      },
    },
  },
  server: {
    host: '127.0.0.1', port: 5173, strictPort: true,
    proxy: { '/api': 'http://127.0.0.1:8765' },
  },
  preview: { host: '127.0.0.1', port: 4173, strictPort: true },
});
