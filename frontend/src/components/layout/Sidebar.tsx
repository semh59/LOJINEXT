import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
    LayoutDashboard,
    Truck,
    Users,
    Route as RouteIcon,
    Fuel,
    FileBarChart,
    MapPin,
    Settings,
    X,
    ChevronRight,
    Zap
} from 'lucide-react'
import { cn } from '../../lib/utils'

interface SidebarProps {
    isOpen: boolean
    onClose: () => void
}

const NAV_ITEMS = [
    { icon: LayoutDashboard, label: 'Panel', path: '/dashboard' },
    { icon: MapPin, label: 'Güzergahlar', path: '/locations' },
    { icon: RouteIcon, label: 'Seferler', path: '/trips' },
    { icon: Fuel, label: 'Yakıt Kayıtları', path: '/fuel' },
    { icon: Truck, label: 'Araçlar', path: '/vehicles' },
    { icon: Users, label: 'Şoförler', path: '/drivers' },
    { icon: FileBarChart, label: 'Raporlar', path: '/reports' },
    { icon: Settings, label: 'Ayarlar', path: '/settings' },
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
                    "fixed top-0 left-0 z-50 h-full w-72 glass flex flex-col transition-transform duration-500 ease-in-out lg:translate-x-0 lg:static border-r border-white/20",
                    isOpen ? "translate-x-0" : "-translate-x-full"
                )}
            >
                {/* Logo Area */}
                <div className="h-24 flex items-center justify-between px-8">
                    <div className="flex items-center gap-3 group cursor-pointer">
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary to-brand flex items-center justify-center text-white shadow-lg shadow-primary/30 group-hover:scale-110 transition-transform duration-300">
                            <Zap className="w-7 h-7 fill-white/20" />
                        </div>
                        <div className="flex flex-col">
                            <span className="text-xl font-black tracking-tight text-brand-dark leading-none">
                                LojiNext
                            </span>
                            <span className="text-[10px] font-bold tracking-[0.2em] uppercase text-primary bg-primary/10 px-1.5 py-0.5 mt-1 rounded">
                                AI Platform
                            </span>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="lg:hidden p-2 rounded-xl bg-white/50 hover:bg-white text-gray-500 transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-4 py-8 space-y-2 overflow-y-auto custom-scrollbar">
                    {NAV_ITEMS.map((item) => {
                        const isActive = location.pathname === item.path
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={cn(
                                    "flex items-center justify-between px-4 py-3.5 rounded-2xl transition-all duration-300 group relative overflow-hidden",
                                    isActive
                                        ? "bg-white text-primary shadow-premium font-bold"
                                        : "text-neutral-500 hover:text-brand-dark hover:bg-white/50"
                                )}
                            >
                                <div className="flex items-center gap-4 z-10">
                                    <item.icon
                                        className={cn(
                                            "w-5 h-5 transition-transform duration-300",
                                            isActive
                                                ? "text-primary scale-110"
                                                : "text-neutral-400 group-hover:text-primary group-hover:rotate-6"
                                        )}
                                    />
                                    <span className="tracking-tight">{item.label}</span>
                                </div>

                                {isActive && (
                                    <motion.div
                                        layoutId="activeTab"
                                        className="absolute inset-0 bg-white z-0"
                                        transition={{ type: "spring", bounce: 0.25, duration: 0.5 }}
                                    />
                                )}

                                <ChevronRight className={cn(
                                    "w-4 h-4 transition-all duration-300 z-10 opacity-0 group-hover:opacity-100",
                                    isActive ? "translate-x-0 opacity-40 text-primary" : "translate-x-[-10px]"
                                )} />
                            </Link>
                        )
                    })}
                </nav>

                {/* Account / Support Card */}
                <div className="p-4">
                    <div className="p-4 rounded-2xl bg-gradient-to-br from-brand-dark to-slate-800 text-white shadow-lg overflow-hidden relative">
                        <div className="relative z-10">
                            <p className="text-xs font-semibold text-brand-gray/80 mb-1">Elite Plan</p>
                            <p className="text-sm font-bold truncate">Premium Destek Aktif</p>
                        </div>
                        <div className="absolute -right-4 -bottom-4 w-16 h-16 bg-white/10 rounded-full blur-xl" />
                    </div>
                </div>
            </aside>
        </>
    )
}
