import { motion, AnimatePresence } from 'framer-motion'
import { Bell, Search, Menu, ChevronDown, LogOut, User as UserIcon } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

interface HeaderProps {
    onMenuClick: () => void
    title?: string
    breadcrumb?: string
}

export function Header({ onMenuClick, title = 'LojiNext AI', breadcrumb = 'Pages / Dashboard' }: HeaderProps) {
    const { user, logout } = useAuth()

    return (
        <header className="h-24 px-4 md:px-10 flex items-center justify-between bg-transparent shrink-0 z-30">
            {/* Left: Title & Breadcrumb */}
            <div className="flex items-center gap-6">
                <button
                    onClick={onMenuClick}
                    className="lg:hidden p-3 text-neutral-500 glass hover:bg-white rounded-2xl transition-all active:scale-95 shadow-soft"
                >
                    <Menu className="w-6 h-6" />
                </button>

                <div className="flex flex-col">
                    <motion.h2
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="text-[11px] font-bold text-neutral-400 mb-0.5 tracking-wider uppercase"
                    >
                        {breadcrumb}
                    </motion.h2>
                    <motion.h1
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.1 }}
                        className="text-2xl md:text-3xl font-black text-brand-dark tracking-tight"
                    >
                        {title}
                    </motion.h1>
                </div>
            </div>

            {/* Right: Actions Container */}
            <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 md:gap-3 glass p-2 rounded-[24px] border-white/40 shadow-xl"
            >
                {/* Search */}
                <div className="relative hidden md:block group">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-400 group-focus-within:text-primary transition-colors">
                        <Search className="w-4 h-4" />
                    </span>
                    <input
                        type="text"
                        placeholder="İçerik ara..."
                        className="bg-neutral-100/50 border-none rounded-2xl py-2.5 pl-11 pr-4 text-sm w-48 focus:w-64 focus:ring-2 focus:ring-primary/20 placeholder-neutral-400 outline-none transition-all duration-300"
                    />
                </div>

                {/* Notification */}
                <button className="relative w-11 h-11 flex items-center justify-center text-neutral-500 hover:text-brand-600 transition-all rounded-2xl hover:bg-white active:scale-90">
                    <Bell className="w-5 h-5" />
                    <span className="absolute top-3 right-3 w-2 h-2 bg-danger border-2 border-white rounded-full"></span>
                </button>

                {/* Profile Dropdown */}
                <div className="flex items-center gap-3 pl-2 pr-1 cursor-pointer group relative">
                    <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-primary/10 to-brand/10 hover:from-primary/20 flex items-center justify-center text-primary font-black border border-white/50 shadow-sm overflow-hidden transition-all duration-300 group-hover:shadow-md">
                        {user?.username?.[0]?.toUpperCase() || 'A'}
                    </div>

                    <div className="hidden sm:flex flex-col items-start mr-1">
                        <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-tighter">İşlem</span>
                        <span className="text-sm font-black text-brand-dark leading-none flex items-center gap-1">
                            {user?.username || 'Admin'}
                            <ChevronDown className="w-4 h-4 text-neutral-400 group-hover:rotate-180 transition-transform duration-300" />
                        </span>
                    </div>

                    <AnimatePresence>
                        <div className="absolute right-0 top-full mt-3 w-56 glass rounded-[24px] py-2 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 z-50 transform translate-y-4 group-hover:translate-y-0 border-white/40 shadow-floating">
                            <div className="px-4 py-2 border-b border-neutral-100/50 mb-1">
                                <p className="text-xs font-bold text-neutral-400 uppercase">Hesap</p>
                            </div>
                            <button className="w-full text-left px-4 py-3 text-sm text-neutral-600 hover:bg-primary/5 font-bold flex items-center gap-3 transition-colors">
                                <UserIcon className="w-4 h-4" /> Profil Ayarları
                            </button>
                            <button
                                onClick={logout}
                                className="w-full text-left px-4 py-3 text-sm text-danger hover:bg-danger/5 font-bold flex items-center gap-3 transition-colors"
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
