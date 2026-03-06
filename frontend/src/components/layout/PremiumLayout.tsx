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
    ChevronDown
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { cn } from '../../lib/utils'
import { ChatAssistant } from '../ai/ChatAssistant'

const NAV_ITEMS = [
    { icon: RouteIcon, label: 'Seferler', path: '/trips' },
    { icon: Fuel, label: 'Yakıt Kayıtları', path: '/fuel' },
    { icon: Truck, label: 'Filo Yönetimi', path: '/fleet' },
    { icon: BarChart2, label: 'Raporlar', path: '/reports' },
    { icon: MapPin, label: 'Güzergahlar', path: '/locations' },
]

export function PremiumLayout({ children, title, primaryColor = '#0df2df' }: { children: React.ReactNode, title?: string, primaryColor?: string }) {
    const location = useLocation()
    const { user, logout } = useAuth()
    const [isSidebarOpen, setIsSidebarOpen] = useState(false)

    return (
        <div className="font-sans antialiased overflow-hidden h-screen flex text-slate-100 bg-[#050b0e]" style={{ "--theme-primary": primaryColor } as React.CSSProperties}>
            
            {/* Mobile Sidebar Overlay */}
            <AnimatePresence>
                {isSidebarOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setIsSidebarOpen(false)}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
                    />
                )}
            </AnimatePresence>

            {/* Sidebar */}
            <aside className={cn(
                "fixed lg:static top-0 left-0 h-full w-64 flex flex-col glass-panel flex-shrink-0 z-50 transition-transform duration-300",
                isSidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
            )}>
                <div className="p-6 flex flex-col gap-6 h-full">
                    {/* Brand */}
                    <div className="flex gap-3 items-center cursor-pointer" onClick={() => window.location.href = '/trips'}>
                        <div className="bg-[#25d1f4] rounded-lg size-10 shadow-[0_0_15px_rgba(37,209,244,0.3)] flex items-center justify-center">
                            <Truck className="w-6 h-6 text-[#050b0e]" />
                        </div>
                        <div className="flex flex-col">
                            <h1 className="text-white text-lg font-bold leading-tight tracking-tight">LojiNext</h1>
                            <p className="text-slate-500 text-xs font-normal">AI Fleet Manager</p>
                        </div>
                    </div>

                    {/* Navigation */}
                    <nav className="flex flex-col gap-2 flex-1 mt-4">
                        {NAV_ITEMS.map((item) => {
                            const isActive = location.pathname.startsWith(item.path)
                            return (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    className={cn(
                                        "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group relative",
                                        isActive ? "bg-white/5 text-white" : "text-slate-400 hover:text-white hover:bg-white/5"
                                    )}
                                >
                                    <item.icon className={cn("w-5 h-5", isActive ? "text-[#25d1f4]" : "text-slate-400 group-hover:text-white")} style={isActive ? { color: primaryColor } : {}} />
                                    <span className="text-sm font-medium">{item.label}</span>
                                    {isActive && (
                                        <motion.div layoutId="premiumActiveTab" className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-full" style={{ backgroundColor: primaryColor }} />
                                    )}
                                </Link>
                            )
                        })}
                    </nav>

                    {/* Bottom Actions */}
                    <div className="mt-auto pt-6 border-t border-white/5 space-y-2">
                        <Link to="/settings" className={cn(
                            "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors group",
                            location.pathname.startsWith('/settings') ? "bg-white/5 text-white" : "text-slate-400 hover:text-white hover:bg-white/5"
                        )}>
                            <Settings className="w-5 h-5 text-slate-400 group-hover:text-white" />
                            <span className="text-sm">Ayarlar</span>
                        </Link>
                        <button onClick={logout} className="w-full flex items-center gap-3 px-3 py-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
                            <LogOut className="w-5 h-5" />
                            <span className="text-sm">Çıkış Yap</span>
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col h-full min-w-0 overflow-hidden relative bg-[#050b0e]">
                {/* Header */}
                <header className="h-16 border-b border-white/5 bg-[#0a1114]/80 backdrop-blur-md px-4 lg:px-6 flex items-center justify-between shrink-0 z-30 sticky top-0">
                    <div className="flex items-center gap-4 lg:gap-6">
                        <button className="lg:hidden p-2 text-slate-400 hover:text-white" onClick={() => setIsSidebarOpen(true)}>
                            <Menu className="w-6 h-6" />
                        </button>
                        <h2 className="text-white text-xl font-bold tracking-tight hidden sm:block">{title}</h2>
                        
                        <div className="relative hidden md:block group">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-[#25d1f4] transition-colors" />
                            <input 
                                type="text" 
                                placeholder="Ara..." 
                                className="w-64 bg-[#050b0e] border border-white/5 rounded-lg py-2 pl-9 pr-3 text-sm text-white focus:outline-none focus:border-white/20 transition-all placeholder:text-slate-600"
                            />
                        </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                        <button className="relative p-2 text-slate-400 hover:text-white transition-colors rounded-full hover:bg-white/5">
                            <Bell className="w-5 h-5" />
                            <span className="absolute top-2 right-2 size-2 bg-red-500 rounded-full ring-2 ring-[#0a1114]"></span>
                        </button>
                        <div className="h-8 w-[1px] bg-white/10 mx-1"></div>
                        <div className="flex items-center gap-3 cursor-pointer group">
                            <div className="bg-gradient-to-br from-[#25d1f4]/20 to-[#25d1f4]/5 text-[#25d1f4] font-bold rounded-full size-9 flex items-center justify-center ring-1 ring-[#25d1f4]/30 group-hover:ring-[#25d1f4] transition-all">
                                {user?.username?.[0]?.toUpperCase() || 'A'}
                            </div>
                            <span className="hidden sm:flex text-sm font-medium text-slate-300 group-hover:text-white transition-colors items-center gap-1">
                                {user?.username || 'Admin'}
                                <ChevronDown className="w-4 h-4 text-slate-500 group-hover:text-white transition-transform" />
                            </span>
                        </div>
                    </div>
                </header>

                {/* Page Content */}
                <div className="flex-1 overflow-auto bg-[#050b0e]">
                    {children}
                </div>
            </main>
            <ChatAssistant />
        </div>
    )
}
