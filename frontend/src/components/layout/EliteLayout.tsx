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
import { LojiNextLogo } from '../common/LojiNextLogo'

const NAV_ITEMS = [
    { icon: RouteIcon, label: 'Seferler', path: '/trips' },
    { icon: Fuel, label: 'Yakıt Kayıtları', path: '/fuel' },
    { icon: Truck, label: 'Filo Yönetimi', path: '/fleet' },
    { icon: BarChart2, label: 'Raporlar', path: '/reports' },
    { icon: MapPin, label: 'Güzergahlar', path: '/locations' },
]

export function EliteLayout({ children, title }: { children: React.ReactNode, title?: string }) {
    const location = useLocation()
    const { user, logout } = useAuth()
    const [isSidebarOpen, setIsSidebarOpen] = useState(false)

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

            {/* Elite Sidebar */}
            <aside className={cn(
                "fixed lg:static top-0 left-0 h-full w-[260px] flex flex-col bg-surface border-r border-border flex-shrink-0 z-50 transition-transform duration-300",
                isSidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
            )}>
                <div className="p-7 flex flex-col h-full">
                    {/* Brand Section */}
                    <Link to="/trips" className="mb-10 block">
                        <LojiNextLogo iconSize={36} textSize="text-[19px]" />
                    </Link>

                    {/* Navigation */}
                    <nav className="flex flex-col gap-1.5 flex-1">
                        {NAV_ITEMS.map((item) => {
                            const isActive = location.pathname.startsWith(item.path)
                            return (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    className={cn(
                                        "flex items-center gap-3.5 px-3 py-3 rounded-xl transition-all group relative",
                                        isActive 
                                            ? "bg-accent/5 text-accent font-bold shadow-[0_1px_2px_rgb(0,0,0,0.02)]" 
                                            : "text-secondary font-medium hover:bg-bg-elevated/50 hover:text-primary"
                                    )}
                                >
                                    <item.icon className={cn("w-[20px] h-[20px]", isActive ? "text-accent" : "text-secondary group-hover:text-primary")} />
                                    <span className="text-[14px]">{item.label}</span>
                                    {isActive && (
                                        <motion.div 
                                            layoutId="eliteActiveTab" 
                                            className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 bg-accent rounded-r-full" 
                                        />
                                    )}
                                </Link>
                            )
                        })}
                    </nav>

                    {/* Bottom Actions */}
                    <div className="mt-auto pt-6 border-t border-border space-y-1.5">
                        <Link to="/settings" className={cn(
                            "flex items-center gap-3.5 px-3 py-3 rounded-xl transition-all group",
                            location.pathname.startsWith('/settings') ? "bg-accent/5 text-accent font-bold" : "text-secondary font-medium hover:bg-bg-elevated/50 hover:text-primary"
                        )}>
                            <Settings className="w-[20px] h-[20px] text-secondary group-hover:text-primary" />
                            <span className="text-[14px]">Ayarlar</span>
                        </Link>
                        <button 
                            onClick={logout} 
                            className="w-full flex items-center gap-3.5 px-3 py-3 text-secondary font-medium hover:text-danger hover:bg-danger/5 rounded-xl transition-all group"
                        >
                            <LogOut className="w-[20px] h-[20px] text-secondary group-hover:text-danger" />
                            <span className="text-[14px]">Çıkış Yap</span>
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col h-full min-w-0 overflow-hidden relative bg-bg-base">
                {/* Elite Header */}
                <header className="h-20 border-b border-border bg-surface/70 backdrop-blur-xl px-6 lg:px-10 flex items-center justify-between shrink-0 z-30 sticky top-0 shadow-[0_1px_2px_rgb(0,0,0,0.01)]">
                    <div className="flex items-center gap-6">
                        <button className="lg:hidden p-2 text-secondary hover:text-primary transition-colors" onClick={() => setIsSidebarOpen(true)}>
                            <Menu className="w-6 h-6" />
                        </button>
                        <h2 className="text-primary text-[22px] font-extrabold tracking-tight hidden sm:block">{title}</h2>
                        
                        <div className="relative hidden md:block group ml-4">
                            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary group-focus-within:text-accent transition-colors" />
                            <input 
                                type="text" 
                                placeholder="Küresel arama..." 
                                className="w-72 bg-bg-elevated/50 border border-border rounded-xl py-2.5 pl-10 pr-4 text-sm text-primary focus:outline-none focus:border-accent/40 focus:bg-surface focus:ring-4 focus:ring-accent/5 transition-all placeholder:text-secondary font-medium"
                            />
                        </div>
                    </div>
                    
                    <div className="flex items-center gap-5">
                        <button className="relative p-2.5 text-secondary hover:text-primary transition-all rounded-xl hover:bg-bg-elevated group border border-transparent hover:border-border">
                            <Bell className="w-5 h-5 group-hover:scale-110 transition-transform" />
                            <span className="absolute top-2 right-2 size-2 bg-accent rounded-full ring-2 ring-surface"></span>
                        </button>
                        
                        <div className="h-8 w-[1px] bg-border mx-1"></div>
                        
                        <div className="flex items-center gap-3.5 pl-2 cursor-pointer group">
                            <div className="flex flex-col text-right lg:flex">
                                <span className="lg:flex text-sm font-bold text-primary tracking-tight leading-none mb-1 group-hover:text-accent transition-colors">{user?.username || 'Yönetici'}</span>
                                <span className="text-[10px] font-extrabold text-secondary uppercase tracking-widest">{user?.role || 'Elite User'}</span>
                            </div>
                            <div className="bg-surface border border-border shadow-sm text-accent font-bold rounded-xl size-11 flex items-center justify-center group-hover:border-accent/20 group-hover:shadow-md transition-all">
                                <User className="w-5 h-5" strokeWidth={2.5} />
                            </div>
                            <ChevronDown className="w-4 h-4 text-secondary group-hover:text-primary transition-transform" />
                        </div>
                    </div>
                </header>

                {/* Page Viewport Area */}
                <div className="flex-1 overflow-auto p-6 lg:p-10 custom-scrollbar relative">
                    {/* Subtle Zen Gradient Glow */}
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[500px] pointer-events-none opacity-[0.03] overflow-hidden">
                        <div className="absolute -top-[20%] left-[10%] w-[60%] h-[60%] bg-accent rounded-full filter blur-[120px]" />
                        <div className="absolute -top-[10%] right-[10%] w-[50%] h-[50%] bg-accent rounded-full filter blur-[120px]" />
                    </div>

                    <div className="relative z-10">
                        <ErrorBoundary>
                            {children}
                        </ErrorBoundary>
                    </div>
                </div>
            </main>
            <ChatAssistant />
        </div>
    )
}
