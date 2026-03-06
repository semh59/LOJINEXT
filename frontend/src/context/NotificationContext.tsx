import { createContext, useContext, useState, useCallback, useEffect, ReactNode, useRef } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Toast, ToastType } from '../components/ui/Toast';
import { tokenStorage } from '../services/api';

interface NotificationToast {
    id: string;
    type: ToastType;
    title: string;
    message?: string;
}

interface NotificationContextType {
    notify: (type: ToastType, title: string, message?: string) => void;
    lastLiveNotification: any | null;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function NotificationProvider({ children }: { children: ReactNode }) {
    const [notifications, setNotifications] = useState<NotificationToast[]>([]);
    const [lastLiveNotification, setLastLiveNotification] = useState<any | null>(null);
    const wsRef = useRef<WebSocket | null>(null);

    const removeNotification = useCallback((id: string) => {
        setNotifications((prev) => prev.filter((n) => n.id !== id));
    }, []);

    const notify = useCallback((type: ToastType, title: string, message?: string) => {
        const id = Math.random().toString(36).substring(2, 9);
        setNotifications((prev) => [...prev, { id, type, title, message }]);

        // Auto remove after 5 seconds
        setTimeout(() => {
            removeNotification(id);
        }, 5000);
    }, [removeNotification]);

    // WebSocket Connection for Real-time Notifications
    useEffect(() => {
        const token = tokenStorage.get();
        if (!token) return;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host === 'localhost:3000' ? 'localhost:8000' : window.location.host;
        const wsUrl = `${protocol}//${host}/api/v1/admin/ws/live?token=${token}`;

        const connect = () => {
            console.log('Connecting to Notification WS...');
            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    if (message.type === 'notification') {
                        const payload = message.data;
                        setLastLiveNotification(payload);
                        
                        // Show toast
                        let toastType: ToastType = 'info';
                        if (payload.olay_tipi?.includes('DELAY') || payload.olay_tipi?.includes('ERROR')) {
                            toastType = 'warning';
                        } else if (payload.olay_tipi?.includes('ANOMALY')) {
                            toastType = 'error';
                        }
                        
                        notify(toastType, payload.baslik, payload.icerik);
                    }
                } catch (err) {
                    console.error('WS Message parsing error:', err);
                }
            };

            ws.onclose = () => {
                console.log('Notification WS closed. Reconnecting in 5s...');
                setTimeout(connect, 5000);
            };

            ws.onerror = (err) => {
                console.error('Notification WS error:', err);
                ws.close();
            };
        };

        connect();

        return () => {
            if (wsRef.current) {
                wsRef.current.onclose = null;
                wsRef.current.close();
            }
        };
    }, [notify]);

    return (
        <NotificationContext.Provider value={{ notify, lastLiveNotification }}>
            {children}

            {/* Portal-like Notification Container */}
            <div className="fixed bottom-6 right-6 z-[100] flex flex-col w-full max-w-sm gap-3 pointer-events-none">
                <AnimatePresence mode="popLayout">
                    {notifications.map((n) => (
                        <Toast
                            key={n.id}
                            {...n}
                            onClose={removeNotification}
                        />
                    ))}
                </AnimatePresence>
            </div>
        </NotificationContext.Provider>
    );
}

export function useNotify() {
    const context = useContext(NotificationContext);
    if (context === undefined) {
        throw new Error('useNotify must be used within a NotificationProvider');
    }
    return context;
}



