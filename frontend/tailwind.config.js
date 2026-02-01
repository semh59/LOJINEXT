/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
            colors: {
                // Design System Colors
                primary: {
                    DEFAULT: '#2563EB', // Primary
                    dark: '#1D4ED8',    // Primary Dark
                    light: '#DBEAFE',   // Primary Light
                    900: '#1E3A8A',     // Deep Blue for headers
                },
                secondary: '#64748B',   // Secondary Text
                accent: '#10B981',      // Accent Green

                // Dashboard Brand Colors
                brand: {
                    DEFAULT: '#4318FF', // Brand Blue (Dashboard Accent)
                    dark: '#2B3674',    // Dark Navy (Dashboard Headers)
                    gray: '#A3AED0',    // Muted Text
                },

                // Semantics
                success: {
                    DEFAULT: '#10B981', // Border/Icon
                    bg: '#D1FAE5',      // Background
                    text: '#059669',    // Text
                    light: '#D1FAE5',   // Alias for bg
                    dark: '#059669',    // Alias for text
                },
                warning: {
                    DEFAULT: '#F59E0B',
                    bg: '#FEF3C7',
                    text: '#D97706',
                    light: '#FEF3C7',
                    dark: '#D97706',
                },
                danger: {
                    DEFAULT: '#EF4444',
                    bg: '#FEE2E2',
                    text: '#DC2626',
                    light: '#FEE2E2',
                    dark: '#B91C1C',
                },
                info: {
                    DEFAULT: '#3B82F6',
                    bg: '#DBEAFE',
                    text: '#1D4ED8',
                    light: '#DBEAFE',
                    dark: '#1D4ED8',
                },

                // Neutrals
                neutral: {
                    50: '#F8FAFC', // Page BG (Design System) -> Dashboard BG (#F4F7FE) is very close, creating alias below
                    100: '#F1F5F9',
                    200: '#E2E8F0', // Border
                    300: '#CBD5E1',
                    400: '#94A3B8', // Placeholder
                    500: '#64748B', // Secondary Text
                    600: '#475569',
                    700: '#334155',
                    800: '#1E293B', // Main Text
                    900: '#0F172A',
                },

                // Dashboard Specific Aliases
                dashboard: {
                    bg: '#F4F7FE',
                    card: '#FFFFFF',
                }
            },
            boxShadow: {
                'card': '0 1px 3px rgba(0,0,0,0.08)',
                'card-hover': '0 10px 20px rgba(0,0,0,0.06)',
                'dashboard-card': '0px 20px 50px rgba(112, 144, 176, 0.15)',
                'soft': '0px 3px 10px rgba(0, 0, 0, 0.05)',
                'modal': '0 25px 50px rgba(0,0,0,0.25)',
                'premium': '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
                'floating': '0 30px 60px -12px rgba(50, 50, 93, 0.25), 0 18px 36px -18px rgba(0, 0, 0, 0.3)',
            },
            animation: {
                'fade-in': 'fadeIn 0.3s ease-out',
                'slide-up': 'slideUp 0.3s ease-out',
                'shake': 'shake 0.3s ease',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { opacity: '0', transform: 'translateY(20px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                shake: {
                    '0%, 100%': { transform: 'translateX(0)' },
                    '25%': { transform: 'translateX(-5px)' },
                    '75%': { transform: 'translateX(5px)' },
                }
            }
        },
    },
    plugins: [],
}
