import path from 'path'
import { fileURLToPath } from 'url'
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
    server: {
        host: true, // Listen on all addresses
        strictPort: true,
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8080',
                changeOrigin: true,
                secure: false,
            }
        },
        watch: {
            usePolling: true,
        },
    },
    build: {
        rollupOptions: {
            output: {
                manualChunks: {
                    'vendor-react': ['react', 'react-dom', 'react-router-dom'],
                    'vendor-ui': ['framer-motion', 'lucide-react', '@radix-ui/react-toggle', 'class-variance-authority', 'clsx', 'tailwind-merge'],
                    'vendor-data': ['@tanstack/react-query', '@tanstack/react-virtual', 'recharts', 'axios', 'zustand'],
                    'vendor-utils': ['date-fns', 'zod', 'sonner', 'react-countup', 'react-hook-form', '@hookform/resolvers'],
                },
            },
        },
        chunkSizeWarningLimit: 600,
    },
    test: {
        globals: true,
        environment: 'jsdom',
        setupFiles: './src/test/setup.ts',
        css: true,
    }
})
