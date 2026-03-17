import { motion, AnimatePresence } from 'framer-motion'
import { Search, Menu, ChevronDown, LogOut, User as UserIcon } from 'lucide-react'
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
        <header className="h-20 px-4 md:px-10 flex items-center justify-between border-b border-border bg-surface/50 backdrop-blur-md shrink-0 z-30 sticky top-0">
            {/* Left: Title & Breadcrumb */}
            <div className="flex items-center gap-6">
                <button
                    onClick={onMenuClick}
                    className="lg:hidden p-2 text-secondary bg-bg-elevated hover:bg-surface rounded-xl transition-all active:scale-95 shadow-sm border border-border"
                >
                    <Menu className="w-6 h-6" />
                </button>

                <div className="flex flex-col">
                    <motion.h2
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="text-[10px] font-bold text-secondary mb-0.5 tracking-widest uppercase"
                    >
                        {breadcrumb}
                    </motion.h2>
                    <motion.h1
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.1 }}
                        className="text-xl md:text-2xl font-black text-primary tracking-tight"
                    >
                        {title}
                    </motion.h1>
                </div>
            </div>

            {/* Right: Actions Container */}
            <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 md:gap-4 bg-bg-elevated/50 p-1.5 px-3 rounded-2xl border border-border shadow-lg"
            >
                {/* Search */}
                <div className="relative hidden md:block group">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary group-focus-within:text-accent transition-colors">
                        <Search className="w-3.5 h-3.5" />
                    </span>
                    <input
                        type="text"
                        placeholder="İçerik ara..."
                        className="bg-surface/50 border border-border rounded-xl py-2 pl-10 pr-4 text-sm w-44 focus:w-60 focus:ring-1 focus:ring-accent/30 placeholder-secondary/50 outline-none transition-all duration-300 text-primary"
                    />
                </div>

                {/* Notification */}
                <NotificationDropdown />

                {/* Profile Dropdown */}
                <div className="flex items-center gap-3 pl-2 pr-1 cursor-pointer group relative">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent/20 to-accent/5 hover:from-accent/30 flex items-center justify-center text-accent font-black border border-accent/20 shadow-sm overflow-hidden transition-all duration-300 group-hover:shadow-accent/20 group-hover:shadow-lg">
                        {user?.username?.[0]?.toUpperCase() || 'A'}
                    </div>

                    <div className="hidden sm:flex flex-col items-start">
                        <span className="text-[10px] font-bold text-secondary uppercase tracking-tighter">İşlem</span>
                        <span className="text-sm font-bold text-primary leading-none flex items-center gap-1">
                            {user?.username || 'Admin'}
                            <ChevronDown className="w-4 h-4 text-secondary group-hover:rotate-180 transition-transform duration-300" />
                        </span>
                    </div>

                    <AnimatePresence>
                        <div className="absolute right-0 top-full mt-2 w-56 bg-bg-elevated border border-border rounded-2xl py-2 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 z-50 transform translate-y-4 group-hover:translate-y-0 shadow-2xl">
                            <div className="px-4 py-2 border-b border-border mb-1">
                                <p className="text-[10px] font-bold text-secondary uppercase">Hesap</p>
                            </div>
                            <button className="w-full text-left px-4 py-3 text-sm text-primary hover:bg-surface/50 font-medium flex items-center gap-3 transition-colors">
                                <UserIcon className="w-4 h-4 text-accent" /> Profil Ayarları
                            </button>
                            <button
                                onClick={logout}
                                className="w-full text-left px-4 py-3 text-sm text-danger hover:bg-danger/5 font-medium flex items-center gap-3 transition-colors"
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
