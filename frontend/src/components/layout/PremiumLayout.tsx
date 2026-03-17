import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Truck,
    Route as RouteIcon,
    Fuel,
    FileBarChart as BarChart2,
    MapPin,
    Settings,
    LogOut,
    Menu,
    Bell,
    Search,
    ChevronDown,
    User
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { cn } from '../../lib/utils'
import { ChatAssistant } from '../ai/ChatAssistant'
import ErrorBoundary from '../common/ErrorBoundary'

const NAV_ITEMS = [
    { icon: RouteIcon, label: 'Seferler', path: '/trips' },
    { icon: Fuel, label: 'Yakıt Kayıtları', path: '/fuel' },
    { icon: Truck, label: 'Filo Yönetimi', path: '/fleet' },
    { icon: BarChart2, label: 'Raporlar', path: '/reports' },
    { icon: MapPin, label: 'Güzergahlar', path: '/locations' },
]

export function PremiumLayout({ children, title }: { children: React.ReactNode, title?: string }) {
    const location = useLocation()
    const { user, logout } = useAuth()
    const [isSidebarOpen, setIsSidebarOpen] = useState(false)
    const [isCollapsed, setIsCollapsed] = useState(false)

    return (
        <div className="font-sans antialiased overflow-hidden h-screen flex text-primary bg-bg-base">
            
            {/* Mobile Sidebar Overlay */}
            <AnimatePresence>
                {isSidebarOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setIsSidebarOpen(false)}
                        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 lg:hidden"
                    />
                )}
            </AnimatePresence>

            {/* v2.0 Sidebar integration inside PremiumLayout */}
            <aside className={cn(
                "fixed lg:static top-0 left-0 h-full bg-surface border-r border-border flex flex-col shrink-0 z-50 transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] lg:translate-x-0",
                isCollapsed ? "w-[64px]" : "w-[240px]",
                isSidebarOpen ? "translate-x-0" : "-translate-x-full"
            )}>
                {/* Logo Area */}
                <div className="h-[72px] flex items-center justify-between px-[16px] border-b border-border shrink-0">
                    <Link 
                        to="/trips"
                        className={cn("flex items-center gap-[12px] group cursor-pointer overflow-hidden", isCollapsed && "justify-center w-full")} 
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
                    </Link>
                    
                    {/* Desktop Collapse Toggle */}
                    {!isCollapsed && (
                        <button
                            onClick={() => setIsCollapsed(true)}
                            className="hidden lg:flex p-[8px] rounded-[8px] hover:bg-bg-elevated text-secondary transition-colors shrink-0 outline-none focus-visible:ring-2 focus-visible:ring-accent"
                        >
                            <Menu className="w-[18px] h-[18px]" />
                        </button>
                    )}
                </div>

                {isCollapsed && (
                    <button
                        onClick={() => setIsCollapsed(false)}
                        className="hidden lg:flex p-[12px] mx-auto mt-[16px] rounded-[8px] hover:bg-bg-elevated text-secondary transition-colors outline-none focus-visible:ring-2 focus-visible:ring-accent"
                    >
                        <Menu className="w-[20px] h-[20px]" />
                    </button>
                )}

                {/* Navigation */}
                <nav className="flex-1 px-[12px] py-[24px] space-y-[4px] overflow-y-auto custom-scrollbar overflow-x-hidden">
                    {NAV_ITEMS.map((item) => {
                        const isActive = location.pathname.startsWith(item.path)
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
                                {isActive && (
                                    <motion.div
                                        layoutId="premiumLayoutNavBorder"
                                        className="absolute left-0 top-[10%] bottom-[10%] w-[3px] rounded-r-full bg-accent"
                                        transition={{ duration: 0.2 }}
                                    />
                                )}

                                <div className="flex items-center gap-[12px] z-10 w-full">
                                    <item.icon
                                        className={cn(
                                            "w-[20px] h-[20px] shrink-0 transition-all duration-200",
                                            isActive
                                                ? "text-accent fill-accent/10"
                                                : "text-secondary group-hover:text-primary"
                                        )}
                                    />
                                    {!isCollapsed && <span className="tracking-tight text-[14px] flex-1 truncate">{item.label}</span>}
                                </div>
                            </Link>
                        )
                    })}
                </nav>

                {/* Bottom Actions */}
                <div className="mt-auto p-[12px] border-t border-border space-y-[4px]">
                    <Link to="/settings" className={cn(
                        "flex items-center px-[12px] py-[10px] rounded-[8px] transition-all duration-200 group relative",
                        location.pathname.startsWith('/settings') ? "text-accent bg-accent/5 font-semibold" : "text-secondary hover:text-primary hover:bg-bg-elevated",
                        isCollapsed && "justify-center px-0 py-[12px]"
                    )}>
                        <div className="flex items-center gap-[12px] z-10 w-full">
                            <Settings className="w-[20px] h-[20px] shrink-0 text-secondary group-hover:text-primary transition-colors" />
                            {!isCollapsed && <span className="text-[14px] flex-1 truncate">Ayarlar</span>}
                        </div>
                    </Link>
                    <button onClick={logout} className={cn(
                        "w-full flex items-center px-[12px] py-[10px] rounded-[8px] transition-all duration-200 group relative text-secondary hover:text-danger hover:bg-danger/10",
                        isCollapsed && "justify-center px-0 py-[12px]"
                    )}>
                        <div className="flex items-center gap-[12px] z-10 w-full">
                            <LogOut className="w-[20px] h-[20px] shrink-0 text-secondary group-hover:text-danger transition-colors" />
                            {!isCollapsed && <span className="text-[14px] flex-1 text-left truncate">Çıkış Yap</span>}
                        </div>
                    </button>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col h-full min-w-0 overflow-hidden relative bg-bg-base">
                {/* Header */}
                <header className="h-[72px] border-b border-border bg-surface/80 backdrop-blur-md px-[24px] lg:px-[40px] flex items-center justify-between shrink-0 z-30 sticky top-0">
                    <div className="flex items-center gap-[24px]">
                        <button className="lg:hidden p-[8px] text-secondary hover:text-primary rounded-[8px] hover:bg-bg-elevated transition-colors" onClick={() => setIsSidebarOpen(true)}>
                            <Menu className="w-[20px] h-[20px]" />
                        </button>
                        <h2 className="text-primary text-[20px] font-bold tracking-tight hidden sm:block">{title}</h2>
                        
                        <div className="relative hidden md:block group ml-[16px]">
                            <Search className="absolute left-[12px] top-1/2 -translate-y-1/2 w-[16px] h-[16px] text-secondary group-focus-within:text-accent transition-colors" />
                            <input 
                                type="text" 
                                placeholder="Ara..." 
                                className="w-[280px] bg-bg-elevated/50 border border-border rounded-[8px] py-[8px] pl-[36px] pr-[16px] text-[14px] text-primary focus:outline-none focus:border-accent focus:bg-surface focus:ring-2 focus:ring-accent/5 transition-all placeholder:text-secondary font-medium"
                            />
                        </div>
                    </div>
                    
                    <div className="flex items-center gap-[20px]">
                        <button className="relative p-[8px] text-secondary hover:text-primary transition-all rounded-[8px] hover:bg-bg-elevated group border border-transparent">
                            <Bell className="w-[20px] h-[20px] group-hover:scale-110 transition-transform" />
                            <span className="absolute top-[8px] right-[8px] w-[8px] h-[8px] bg-danger rounded-full ring-2 ring-surface"></span>
                        </button>
                        <div className="h-[24px] w-[1px] bg-border mx-[4px]"></div>
                        <div className="flex items-center gap-[12px] pl-[8px] cursor-pointer group">
                            <div className="hidden lg:flex flex-col text-right">
                                <span className="text-[13px] font-bold text-primary tracking-tight leading-none mb-[4px] group-hover:text-accent transition-colors">{user?.username || 'Admin'}</span>
                                <span className="text-[10px] font-bold text-secondary uppercase tracking-widest">{user?.role || 'Manager'}</span>
                            </div>
                            <div className="bg-surface border border-border shadow-sm text-secondary font-bold rounded-[10px] w-[36px] h-[36px] flex items-center justify-center group-hover:border-secondary transition-all">
                                <User className="w-[18px] h-[18px]" strokeWidth={2.5} />
                            </div>
                            <ChevronDown className="w-[16px] h-[16px] text-secondary group-hover:text-primary transition-transform" />
                        </div>
                    </div>
                </header>

                {/* Page Content Viewport - Max width wrapper */}
                <div className="flex-1 overflow-auto custom-scrollbar relative px-[24px] py-[32px] lg:px-[40px]">
                    <div className="mx-auto w-full max-w-[1280px] relative z-10 min-h-full">
                        <ErrorBoundary>
                            {/* Page Transitions (fade + translateY 6px) */}
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={location.pathname}
                                    initial={{ opacity: 0, y: 6 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -6 }}
                                    transition={{ duration: 0.22, ease: "easeOut" }}
                                    className="h-full"
                                >
                                    {children}
                                </motion.div>
                            </AnimatePresence>
                        </ErrorBoundary>
                    </div>
                </div>
            </main>
            <ChatAssistant />
        </div>
    )
}
