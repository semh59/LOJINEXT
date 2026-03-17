export default {
    test: {
        globals: true,
        environment: 'jsdom',
        setupFiles: ['./frontend/src/test/setup.ts'],
        css: true,
        include: ['frontend/src/**/*.{test,spec}.{ts,tsx}'],
        pool: 'forks',
    },
}
