import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, AlertTriangle, Info, Clock } from 'lucide-react';
import { notificationService, Notification } from '../../services/api/notification-service';
import { formatDistanceToNow } from 'date-fns';
import { tr } from 'date-fns/locale';
import { useNotify } from '../../context/NotificationContext';

export function NotificationDropdown() {
    const [isOpen, setIsOpen] = useState(false);
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [loading, setLoading] = useState(false);
    const { lastLiveNotification } = useNotify();

    const unreadCount = notifications.filter(n => !n.okundu).length;

    const fetchNotifications = useCallback(async () => {
        try {
            setLoading(true);
            const data = await notificationService.getMyNotifications();
            setNotifications(data);
        } catch (error) {
            console.error('Bildirimler yüklenemedi:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchNotifications();
        // 30 saniyede bir güncelle (Fallback polling)
        const interval = setInterval(fetchNotifications, 60000);
        return () => clearInterval(interval);
    }, [fetchNotifications]);

    // WebSocket üzerinden yeni bildirim geldiğinde listeyi yenile
    useEffect(() => {
        if (lastLiveNotification) {
            fetchNotifications();
        }
    }, [lastLiveNotification, fetchNotifications]);

    const handleMarkAsRead = async (id: number) => {
        try {
            await notificationService.markAsRead(id);
            setNotifications(prev => prev.map(n => n.id === id ? { ...n, okundu: true } : n));
        } catch (error) {
            console.error('Hata:', error);
        }
    };

    const handleMarkAllAsRead = async () => {
        try {
            await notificationService.markAllAsRead();
            setNotifications(prev => prev.map(n => ({ ...n, okundu: true })));
        } catch (error) {
            console.error('Hata:', error);
        }
    };

    const getIcon = (type: string) => {
        switch (type) {
            case 'SLA_VIOLATION':
            case 'sla_delay':
                return <AlertTriangle className="w-4 h-4 text-red-400" />;
            case 'ANOMALY_DETECTED':
            case 'anomaly_detected':
                return <AlertTriangle className="w-4 h-4 text-amber-400" />;
            default:
                return <Info className="w-4 h-4 text-[#25d1f4]" />;
        }
    };

    return (
        <div className="relative">
            <button 
                onClick={() => setIsOpen(!isOpen)}
                className="relative w-10 h-10 flex items-center justify-center text-slate-400 hover:text-white transition-all rounded-xl hover:bg-white/5 active:scale-90"
            >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                    <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-red-500 border-2 border-[#0a1114] rounded-full animate-pulse shadow-[0_0_10px_rgba(239,68,68,0.5)]"></span>
                )}
            </button>

            <AnimatePresence>
                {isOpen && (
                    <>
                        <div 
                            className="fixed inset-0 z-40" 
                            onClick={() => setIsOpen(false)}
                        ></div>
                        <motion.div
                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 10, scale: 0.95 }}
                            className="absolute right-0 mt-4 w-80 md:w-96 glass-card rounded-2xl border border-white/10 shadow-2xl z-50 overflow-hidden"
                        >
                            <div className="p-4 border-b border-white/5 flex items-center justify-between bg-white/5">
                                <h3 className="font-bold text-white flex items-center gap-2">
                                    Bildirimler
                                    {unreadCount > 0 && (
                                        <span className="bg-red-500/20 text-red-500 text-[10px] px-2 py-0.5 rounded-full border border-red-500/30">
                                            {unreadCount} Yeni
                                        </span>
                                    )}
                                </h3>
                                {unreadCount > 0 && (
                                    <button 
                                        onClick={handleMarkAllAsRead}
                                        className="text-[10px] font-bold text-[#25d1f4] hover:underline uppercase tracking-wider"
                                    >
                                        Tümünü Oku
                                    </button>
                                )}
                            </div>

                            <div className="max-h-[400px] overflow-y-auto custom-scrollbar">
                                {loading && notifications.length === 0 ? (
                                    <div className="p-10 text-center">
                                        <div className="w-8 h-8 border-2 border-[#25d1f4]/30 border-t-[#25d1f4] rounded-full animate-spin mx-auto mb-3"></div>
                                        <p className="text-sm text-slate-500">Yükleniyor...</p>
                                    </div>
                                ) : notifications.length === 0 ? (
                                    <div className="p-10 text-center">
                                        <div className="w-12 h-12 bg-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-600">
                                            <Bell className="w-6 h-6 outline-none" />
                                        </div>
                                        <p className="font-bold text-slate-300">Bildirim Yok</p>
                                        <p className="text-xs text-slate-500 mt-1">Henüz bir bildirim almadınız.</p>
                                    </div>
                                ) : (
                                    <div className="divide-y divide-white/5">
                                        {notifications.map((notif) => (
                                            <div 
                                                key={notif.id}
                                                className={`p-4 hover:bg-white/5 transition-colors cursor-pointer relative group ${!notif.okundu ? 'bg-[#25d1f4]/5' : ''}`}
                                                onClick={() => !notif.okundu && handleMarkAsRead(notif.id)}
                                            >
                                                {!notif.okundu && (
                                                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#25d1f4]"></div>
                                                )}
                                                <div className="flex gap-3">
                                                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                                                        notif.okundu ? 'bg-slate-800' : 'bg-[#25d1f4]/20'
                                                    }`}>
                                                        {getIcon(notif.olay_tipi)}
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <div className="flex items-center justify-between gap-2 mb-1">
                                                            <p className={`text-sm font-bold truncate ${notif.okundu ? 'text-slate-300' : 'text-white'}`}>
                                                                {notif.baslik}
                                                            </p>
                                                            <span className="text-[10px] text-slate-500 whitespace-nowrap flex items-center gap-1">
                                                                <Clock className="w-3 h-3" />
                                                                {formatDistanceToNow(new Date(notif.olusturma_tarihi), { addSuffix: true, locale: tr })}
                                                            </span>
                                                        </div>
                                                        <p className={`text-xs leading-relaxed line-clamp-2 ${notif.okundu ? 'text-slate-500' : 'text-slate-300'}`}>
                                                            {notif.icerik}
                                                        </p>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            <div className="p-3 border-t border-white/5 text-center bg-black/20">
                                <button 
                                    className="text-xs font-bold text-slate-500 hover:text-white transition-colors"
                                    onClick={() => setIsOpen(false)}
                                >
                                    Kapat
                                </button>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
}
