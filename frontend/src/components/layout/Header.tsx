import { motion, AnimatePresence } from 'framer-motion'
import { Bell, Search, Menu, ChevronDown, LogOut, User as UserIcon } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { NotificationDropdown } from './NotificationDropdown'

interface HeaderProps {
    onMenuClick: () => void
    title?: string
    breadcrumb?: string
}

export function Header({ onMenuClick, title = 'LojiNext AI', breadcrumb = 'Pages / Dashboard' }: HeaderProps) {
    const { user, logout } = useAuth()

    return (
        <header className="h-20 px-4 md:px-10 flex items-center justify-between border-b border-white/5 bg-[#0a1114]/50 backdrop-blur-md shrink-0 z-30 sticky top-0">
            {/* Left: Title & Breadcrumb */}
            <div className="flex items-center gap-6">
                <button
                    onClick={onMenuClick}
                    className="lg:hidden p-2 text-slate-400 glass-card hover:bg-white/5 rounded-xl transition-all active:scale-95 shadow-soft"
                >
                    <Menu className="w-6 h-6" />
                </button>

                <div className="flex flex-col">
                    <motion.h2
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="text-[10px] font-bold text-slate-500 mb-0.5 tracking-widest uppercase"
                    >
                        {breadcrumb}
                    </motion.h2>
                    <motion.h1
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.1 }}
                        className="text-xl md:text-2xl font-black text-white tracking-tight"
                    >
                        {title}
                    </motion.h1>
                </div>
            </div>

            {/* Right: Actions Container */}
            <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 md:gap-4 glass-card p-1.5 px-3 rounded-2xl border-white/10 shadow-xl"
            >
                {/* Search */}
                <div className="relative hidden md:block group">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-[#25d1f4] transition-colors">
                        <Search className="w-3.5 h-3.5" />
                    </span>
                    <input
                        type="text"
                        placeholder="İçerik ara..."
                        className="bg-black/20 border border-white/5 border-none rounded-xl py-2 pl-10 pr-4 text-sm w-44 focus:w-60 focus:ring-1 focus:ring-[#25d1f4]/30 placeholder-slate-600 outline-none transition-all duration-300 text-white"
                    />
                </div>

                {/* Notification */}
                <NotificationDropdown />

                {/* Profile Dropdown */}
                <div className="flex items-center gap-3 pl-2 pr-1 cursor-pointer group relative">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#25d1f4]/20 to-[#25d1f4]/5 hover:from-[#25d1f4]/30 flex items-center justify-center text-[#25d1f4] font-black border border-[#25d1f4]/20 shadow-sm overflow-hidden transition-all duration-300 group-hover:shadow-[#25d1f4]/20 group-hover:shadow-lg">
                        {user?.username?.[0]?.toUpperCase() || 'A'}
                    </div>

                    <div className="hidden sm:flex flex-col items-start">
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">İşlem</span>
                        <span className="text-sm font-bold text-slate-100 leading-none flex items-center gap-1">
                            {user?.username || 'Admin'}
                            <ChevronDown className="w-4 h-4 text-slate-500 group-hover:rotate-180 transition-transform duration-300" />
                        </span>
                    </div>

                    <AnimatePresence>
                        <div className="absolute right-0 top-full mt-4 w-56 glass-card rounded-2xl py-2 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 z-50 transform translate-y-4 group-hover:translate-y-0 border-white/10 shadow-2xl">
                            <div className="px-4 py-2 border-b border-white/5 mb-1">
                                <p className="text-[10px] font-bold text-slate-500 uppercase">Hesap</p>
                            </div>
                            <button className="w-full text-left px-4 py-3 text-sm text-slate-300 hover:bg-white/5 font-medium flex items-center gap-3 transition-colors">
                                <UserIcon className="w-4 h-4 text-[#25d1f4]" /> Profil Ayarları
                            </button>
                            <button
                                onClick={logout}
                                className="w-full text-left px-4 py-3 text-sm text-red-400 hover:bg-red-500/5 font-medium flex items-center gap-3 transition-colors"
                            >
                                <LogOut className="w-4 h-4" /> Güvenli Çıkış
                            </button>
                        </div>
                    </AnimatePresence>
                </div>
            </motion.div>
        </header>
    )
}
