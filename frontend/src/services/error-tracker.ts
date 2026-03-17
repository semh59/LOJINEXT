/**
 * B-006: Lightweight Frontend Error Tracker
 * 
 * Yakalanmamış JS hatalarını ve promised rejection'ları izler.
 * Sentry benzeri bir altyapı olmadan temel hata raporlaması sağlar.
 * Backend'e POST /api/v1/system/error-report ile raporlanır.
 */

import axiosInstance from './api/axios-instance';

interface ErrorReport {
    message: string;
    stack?: string;
    componentStack?: string;
    url: string;
    userAgent: string;
    timestamp: string;
    severity: 'error' | 'warning' | 'fatal';
}

class ErrorTracker {
    private reportedErrors = new Map<string, number>();
    private readonly MAX_REPORTS_PER_KEY = 3;
    private readonly COOLDOWN_MS = 60_000; // 1 dakika

    /**
     * Hata yakala ve backend'e raporla (rate limited).
     */
    capture(error: Error, extra?: { componentStack?: string; severity?: ErrorReport['severity'] }): void {
        const key = `${error.message}:${error.stack?.slice(0, 200) || ''}`;
        const now = Date.now();
        const lastReport = this.reportedErrors.get(key) || 0;

        // Rate limiting: Aynı hata 1 dakikada max 3 kez
        if (now - lastReport < this.COOLDOWN_MS) {
            return;
        }

        // Count check
        const countKey = `count:${key}`;
        const count = this.reportedErrors.get(countKey) || 0;
        if (count >= this.MAX_REPORTS_PER_KEY) {
            return;
        }

        this.reportedErrors.set(key, now);
        this.reportedErrors.set(countKey, count + 1);

        const report: ErrorReport = {
            message: error.message,
            stack: error.stack,
            componentStack: extra?.componentStack,
            url: window.location.href,
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString(),
            severity: extra?.severity || 'error',
        };

        this.sendReport(report);
    }

    /**
     * Global olay dinleyicilerini kur (window.onerror, unhandledrejection).
     */
    install(): void {
        window.addEventListener('error', (event) => {
            if (event.error) {
                this.capture(event.error, { severity: 'error' });
            }
        });

        window.addEventListener('unhandledrejection', (event) => {
            const error = event.reason instanceof Error
                ? event.reason
                : new Error(String(event.reason));
            this.capture(error, { severity: 'warning' });
        });
    }

    private async sendReport(report: ErrorReport): Promise<void> {
        // In development, we keep the console clear unless it's fatal
        if (import.meta.env.DEV && report.severity === 'fatal') {
            console.group(`🚨 [ErrorTracker] ${report.severity.toUpperCase()}`);
            console.error(report.message);
            console.groupEnd();
        }

        try {
            await axiosInstance.post('/system/error-report', report);
        } catch (err) {
            // If the sink itself fails, we must at least warn the developer
            if (import.meta.env.DEV) {
                console.warn('[ErrorTracker] Sink unreachable:', report.message);
            }
        }
    }

    /**
     * Sayaçları sıfırla (test amaçlı).
     */
    reset(): void {
        this.reportedErrors.clear();
    }
}

export const errorTracker = new ErrorTracker();
