import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

function remToPxPlugin() {
  return {
    name: 'rem-to-px',
    enforce: 'post',
    // For 'npm run dev' (transforming served CSS)
    transform(code, id) {
      if (id.endsWith('.css')) {
        return code.replace(/([0-9.]+)rem/g, (match, p1) => `${parseFloat(p1) * 16}px`);
      }
    },
    // For 'npm run build' (transforming generated CSS bundle)
    generateBundle(options, bundle) {
      for (const fileName in bundle) {
        if (fileName.endsWith('.css')) {
          const chunk = bundle[fileName];
          if (chunk.type === 'asset' && typeof chunk.source === 'string') {
            chunk.source = chunk.source.replace(/([0-9.]+)rem/g, (match, p1) => `${parseFloat(p1) * 16}px`);
          } else if (chunk.type === 'asset' && chunk.source instanceof Uint8Array) {
            const decoder = new TextDecoder();
            const encoder = new TextEncoder();
            let sourceString = decoder.decode(chunk.source);
            sourceString = sourceString.replace(/([0-9.]+)rem/g, (match, p1) => `${parseFloat(p1) * 16}px`);
            chunk.source = encoder.encode(sourceString);
          }
        }
      }
    }
  };
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss(), remToPxPlugin()],
  build: {
    target: 'esnext',
    // Emit static file names so manifest.json doesn't need updating every build
    rollupOptions: {
      input: {
        content: 'src/main.jsx'
      },
      output: {
        entryFileNames: 'content.js',
        assetFileNames: 'content.css',
      },
    },
  },
});
