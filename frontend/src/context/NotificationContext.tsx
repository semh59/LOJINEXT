import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Toast, ToastType } from '../components/ui/Toast';

interface Notification {
    id: string;
    type: ToastType;
    title: string;
    message?: string;
}

interface NotificationContextType {
    notify: (type: ToastType, title: string, message?: string) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function NotificationProvider({ children }: { children: ReactNode }) {
    const [notifications, setNotifications] = useState<Notification[]>([]);

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

    return (
        <NotificationContext.Provider value={{ notify }}>
            {children}

            {/* Portal-like Notification Container */}
            <div className="fixed bottom-6 right-6 z-[100] flex flex-col w-full max-w-sm pointer-events-none">
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



