import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Truck,
    Route as RouteIcon,
    Fuel,
    FileBarChart as BarChart2,
    MapPin,
    X,
    ChevronRight,
    Settings,
} from 'lucide-react'
import { cn } from '../../lib/utils'

interface SidebarProps {
    isOpen: boolean
    onClose: () => void
}

const NAV_ITEMS = [
    { icon: RouteIcon, label: 'Seferler', path: '/trips' },
    { icon: Fuel, label: 'Yakıt Kayıtları', path: '/fuel' },
    { icon: Truck, label: 'Filo Yönetimi', path: '/fleet' },
    { icon: BarChart2, label: 'Raporlar', path: '/reports' },
    { icon: MapPin, label: 'Güzergahlar', path: '/locations' },
    { icon: Settings, label: 'Ayarlar', path: '/admin' },
]

export function Sidebar({ isOpen, onClose }: SidebarProps) {
    const location = useLocation()

    return (
        <>
            {/* Mobile Overlay */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-40 bg-brand-dark/20 backdrop-blur-sm lg:hidden"
                        onClick={onClose}
                    />
                )}
            </AnimatePresence>

            {/* Sidebar Content */}
            <aside
                className={cn(
                    "fixed top-0 left-0 z-50 h-full w-72 glass-panel flex flex-col transition-transform duration-500 ease-in-out lg:translate-x-0 lg:static",
                    isOpen ? "translate-x-0" : "-translate-x-full"
                )}
            >
                {/* Logo Area */}
                <div className="h-24 flex items-center justify-between px-8 border-b border-white/5">
                    <div className="flex items-center gap-3 group cursor-pointer" onClick={() => (window.location.href = '/trips')}>
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#25d1f4] to-[#d006f9] flex items-center justify-center text-white shadow-lg shadow-[#25d1f4]/30 group-hover:scale-110 transition-transform duration-300">
                            <Truck className="w-7 h-7 fill-white/20" />
                        </div>
                        <div className="flex flex-col">
                            <span className="text-xl font-black tracking-tight text-white leading-none">
                                LojiNext
                            </span>
                            <span className="text-[10px] font-bold tracking-[0.2em] uppercase text-[#25d1f4] bg-[#25d1f4]/10 px-1.5 py-0.5 mt-1 rounded">
                                AI Platform
                            </span>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="lg:hidden p-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-400 transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-4 py-8 space-y-2 overflow-y-auto custom-scrollbar">
                    {NAV_ITEMS.map((item) => {
                        const isActive = item.path.includes('?') 
                            ? location.pathname + location.search === item.path 
                            : location.pathname === item.path
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={cn(
                                    "flex items-center justify-between px-4 py-3.5 rounded-2xl transition-all duration-300 group relative overflow-hidden",
                                    isActive
                                        ? "text-[#25d1f4] font-bold"
                                        : "text-slate-400 hover:text-white hover:bg-white/5"
                                )}
                            >
                                <div className="flex items-center gap-4 z-10">
                                    <item.icon
                                        className={cn(
                                            "w-5 h-5 transition-all duration-300",
                                            isActive
                                                ? "text-[#25d1f4] scale-110 shadow-[0_0_10px_rgba(37,209,244,0.3)]"
                                                : "text-slate-500 group-hover:text-white group-hover:rotate-6"
                                        )}
                                    />
                                    <span className="tracking-tight">{item.label}</span>
                                </div>

                                {isActive && (
                                    <motion.div
                                        layoutId="activeTab"
                                        className="absolute inset-0 bg-white/5 z-0"
                                        transition={{ type: "spring", bounce: 0.25, duration: 0.5 }}
                                    />
                                )}

                                <ChevronRight className={cn(
                                    "w-4 h-4 transition-all duration-300 z-10 opacity-0 group-hover:opacity-100",
                                    isActive ? "translate-x-0 opacity-40 text-[#25d1f4]" : "translate-x-[-10px]"
                                )} />
                            </Link>
                        )
                    })}
                </nav>
            </aside>
        </>
    )
}
