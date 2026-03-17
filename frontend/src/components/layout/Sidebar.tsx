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
    LogOut,
    Menu
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { useState } from 'react'

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
    const [isCollapsed, setIsCollapsed] = useState(false)

    return (
        <>
            {/* Mobile Overlay */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
                        onClick={onClose}
                    />
                )}
            </AnimatePresence>

            {/* Sidebar Content */}
            {/* LojiNext v2.0 Sidebar Rules: 240px wide, or 64px collapsed */}
            <aside
                className={cn(
                    "fixed top-0 left-0 z-50 h-full bg-surface border-r border-border flex flex-col transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] lg:translate-x-0 lg:static",
                    isCollapsed ? "w-[64px]" : "w-[240px]",
                    isOpen ? "translate-x-0" : "-translate-x-full"
                )}
            >
                {/* Logo Area */}
                <div className="h-[72px] flex items-center justify-between px-[16px] border-b border-border shrink-0">
                    <div 
                        className={cn("flex items-center gap-[12px] group cursor-pointer overflow-hidden", isCollapsed && "justify-center w-full")} 
                        onClick={() => (window.location.href = '/trips')}
                    >
                        <div className="w-[32px] h-[32px] shrink-0 rounded-[8px] bg-accent flex items-center justify-center text-bg-base shadow-sm transition-transform duration-300 group-hover:scale-105">
                            <Truck className="w-[18px] h-[18px] text-bg-base" />
                        </div>
                        
                        {!isCollapsed && (
                            <motion.div 
                                initial={{ opacity: 0, width: 0 }}
                                animate={{ opacity: 1, width: "auto" }}
                                exit={{ opacity: 0, width: 0 }}
                                className="flex flex-col whitespace-nowrap"
                            >
                                <span className="text-[16px] font-bold tracking-tight text-primary leading-tight">
                                    LojiNext
                                </span>
                            </motion.div>
                        )}
                    </div>
                    
                    <button
                        onClick={onClose}
                        className="lg:hidden p-[8px] rounded-[8px] hover:bg-bg-elevated text-secondary transition-colors"
                    >
                        <X className="w-[20px] h-[20px]" />
                    </button>
                    
                    {/* Desktop Collapse Toggle */}
                    {!isCollapsed && (
                        <button
                            onClick={() => setIsCollapsed(true)}
                            className="hidden lg:flex p-[8px] rounded-[8px] hover:bg-bg-elevated text-secondary transition-colors shrink-0"
                        >
                            <Menu className="w-[18px] h-[18px]" />
                        </button>
                    )}
                </div>

                {isCollapsed && (
                    <button
                        onClick={() => setIsCollapsed(false)}
                        className="hidden lg:flex p-[12px] mx-auto mt-[16px] rounded-[8px] hover:bg-bg-elevated text-secondary transition-colors"
                    >
                        <Menu className="w-[20px] h-[20px]" />
                    </button>
                )}

                {/* Navigation */}
                <nav className="flex-1 px-[12px] py-[24px] space-y-[4px] overflow-y-auto custom-scrollbar overflow-x-hidden">
                    {NAV_ITEMS.map((item) => {
                        const isActive = item.path.includes('?') 
                            ? location.pathname + location.search === item.path 
                            : location.pathname.startsWith(item.path)

                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                title={isCollapsed ? item.label : undefined}
                                className={cn(
                                    "flex items-center px-[12px] py-[10px] rounded-[8px] transition-all duration-200 group relative",
                                    isActive
                                        ? "text-accent bg-accent/5 font-semibold"
                                        : "text-secondary hover:text-primary hover:bg-bg-elevated",
                                    isCollapsed && "justify-center px-0 py-[12px]"
                                )}
                            >
                                {/* Active indicator: Left border slide in (200ms) */}
                                {isActive && (
                                    <motion.div
                                        layoutId="activeNavBorder"
                                        className="absolute left-0 top-[10%] bottom-[10%] w-[3px] rounded-r-full bg-accent"
                                        transition={{ duration: 0.2 }}
                                    />
                                )}

                                <div className="flex items-center gap-[12px] z-10 w-full">
                                    <item.icon
                                        className={cn(
                                            "w-[20px] h-[20px] shrink-0 transition-all duration-200",
                                            isActive
                                                ? "text-accent fill-accent/20"
                                                : "text-secondary group-hover:text-primary"
                                        )}
                                    />
                                    
                                    {!isCollapsed && (
                                        <span className="tracking-tight text-[14px] flex-1 truncate">{item.label}</span>
                                    )}
                                    
                                    {!isCollapsed && <ChevronRight className={cn(
                                        "w-[14px] h-[14px] transition-all duration-200 opacity-0 group-hover:opacity-100 shrink-0",
                                        isActive ? "opacity-100 text-accent translate-x-0" : "-translate-x-[4px]"
                                    )} />}
                                </div>
                            </Link>
                        )
                    })}
                </nav>

                {/* User Area - Bottom */}
                <div className={cn(
                    "p-[16px] border-t border-border bg-bg-base/30",
                    isCollapsed ? "flex justify-center" : "flex items-center justify-between"
                )}>
                    {!isCollapsed ? (
                        <div className="flex items-center gap-[12px] overflow-hidden">
                            <div className="w-[36px] h-[36px] rounded-full bg-accent/10 flex items-center justify-center shrink-0 border border-accent/20">
                                <span className="text-[14px] font-bold text-accent">AD</span>
                            </div>
                            <div className="flex flex-col truncate">
                                <span className="text-[13px] font-bold text-primary truncate">Admin User</span>
                                <span className="text-[11px] text-secondary truncate">admin@lojinext.com</span>
                            </div>
                        </div>
                    ) : (
                        <div className="w-[32px] h-[32px] rounded-full bg-accent/10 flex items-center justify-center shrink-0 border border-accent/20 cursor-pointer" title="Admin User">
                            <span className="text-[12px] font-bold text-accent">AD</span>
                        </div>
                    )}

                    {!isCollapsed && (
                        <button className="p-[6px] text-secondary hover:text-danger hover:bg-danger/10 rounded-[6px] transition-colors shrink-0">
                            <LogOut className="w-[16px] h-[16px]" />
                        </button>
                    )}
                </div>
            </aside>
        </>
    )
}
