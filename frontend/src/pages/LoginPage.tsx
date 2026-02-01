import { useState, FormEvent, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { Eye, EyeOff, Truck, Lock, User, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { cn } from '@/lib/utils'

// Circular Progress Component - Rate Limit Countdown için
function CircularProgress({ value, max }: { value: number; max: number }) {
    const radius = 18
    const circumference = 2 * Math.PI * radius
    const progress = ((max - value) / max) * circumference

    return (
        <svg className="w-10 h-10 -rotate-90" viewBox="0 0 44 44">
            {/* Arka plan dairesi */}
            <circle
                cx="22"
                cy="22"
                r={radius}
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                className="text-slate-200"
            />
            {/* Progress dairesi */}
            <circle
                cx="22"
                cy="22"
                r={radius}
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={progress}
                className="text-red-500 transition-all duration-1000"
            />
        </svg>
    )
}

export default function LoginPage() {
    const navigate = useNavigate()
    const { login, isLoading } = useAuth()

    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [showPassword, setShowPassword] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [showErrorGlow, setShowErrorGlow] = useState(false)
    const [failedAttempts, setFailedAttempts] = useState(0)
    const [lockoutTime, setLockoutTime] = useState<number | null>(null)
    const [remainingSeconds, setRemainingSeconds] = useState(0)

    // Rate Limiting Logic via Local State
    useEffect(() => {
        if (lockoutTime) {
            const timer = setInterval(() => {
                const remaining = Math.ceil((lockoutTime - Date.now()) / 1000)
                setRemainingSeconds(Math.max(0, remaining))
                if (remaining <= 0) {
                    setLockoutTime(null)
                    setFailedAttempts(0)
                    setError(null)
                }
            }, 100) // Daha smooth countdown için 100ms
            return () => clearInterval(timer)
        }
    }, [lockoutTime])

    // Error glow efekti için timer (2 saniye)
    useEffect(() => {
        if (error && !lockoutTime) {
            setShowErrorGlow(true)
            const timer = setTimeout(() => setShowErrorGlow(false), 2000)
            return () => clearTimeout(timer)
        }
    }, [error, lockoutTime])

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault()
        if (lockoutTime) return

        setError(null)

        if (!username || !password) {
            setError('Lütfen tüm alanları doldurun')
            return
        }

        try {
            await login(username, password)
            navigate('/dashboard')
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Giriş yapılamadı'
            setError(message)

            // Increment failed attempts
            const newAttempts = failedAttempts + 1
            setFailedAttempts(newAttempts)

            if (newAttempts >= 3) {
                setLockoutTime(Date.now() + 30000) // 30 seconds
                setRemainingSeconds(30)
                setError('Çok fazla başarısız deneme. Lütfen bekleyin.')
            }
        }
    }

    return (
        <div className="min-h-screen bg-[#F1F5F9] flex items-center justify-center p-6 relative overflow-hidden font-sans">
            {/* Abstract Geometric Premium Pattern Background */}
            <div className="absolute inset-0 z-0">
                <div className="absolute top-[-10%] left-[-10%] w-[60%] h-[60%] bg-gradient-to-br from-blue-400/20 to-indigo-400/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] bg-gradient-to-tl from-indigo-400/20 to-purple-400/10 rounded-full blur-[120px]" />
                {/* Subtle grid pattern overlay */}
                <div className="absolute inset-0 opacity-[0.02]" style={{
                    backgroundImage: `
                        linear-gradient(to right, #0F172A 1px, transparent 1px),
                        linear-gradient(to bottom, #0F172A 1px, transparent 1px)
                    `,
                    backgroundSize: '40px 40px'
                }} />
            </div>

            <motion.div
                initial={{ opacity: 0, y: 30, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
                className="w-full max-w-[400px] relative z-10"
            >
                {/* Card with Glassmorphism & Error Glow */}
                <motion.div
                    animate={error ? { x: [-8, 8, -6, 6, -4, 4, 0] } : {}}
                    transition={{ duration: 0.4, ease: "easeOut" }}
                    className={cn(
                        "rounded-[32px] border backdrop-blur-xl p-12 transition-all duration-300",
                        "bg-white/75 shadow-[0_20px_50px_-12px_rgba(0,0,0,0.08)]",
                        showErrorGlow
                            ? "border-red-400/60 shadow-[0_0_40px_-5px_rgba(239,68,68,0.25)]"
                            : "border-white/50"
                    )}
                >
                    {/* Logo Area */}
                    <div className="flex flex-col items-center mb-8">
                        <motion.div
                            initial={{ scale: 0, rotate: -180 }}
                            animate={{ scale: 1, rotate: 0 }}
                            transition={{ delay: 0.2, type: "spring", stiffness: 200, damping: 15 }}
                            className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-700 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/30 mb-4"
                        >
                            <Truck className="text-white w-8 h-8" />
                        </motion.div>
                        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">LojiNext AI</h1>
                        <p className="text-sm text-slate-500 mt-1">TIR Yakıt Takip Sistemi</p>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="flex flex-col gap-5" role="form" aria-label="Giriş formu">
                        <div className="space-y-1.5">
                            <label htmlFor="username" className="text-sm font-medium text-slate-700 ml-1">
                                Kullanıcı Adı
                            </label>
                            <div className="relative group">
                                <Input
                                    id="username"
                                    autoComplete="username"
                                    className={cn(
                                        "h-12 rounded-[14px] bg-white/60 border-transparent pl-11 pr-4",
                                        "focus:bg-white focus:border-blue-500/50 focus:ring-4 focus:ring-blue-500/10",
                                        "transition-all duration-200",
                                        error && !lockoutTime && "border-red-400"
                                    )}
                                    placeholder="Kullanıcı adınızı girin"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    disabled={isLoading || !!lockoutTime}
                                    aria-describedby={error ? "error-message" : undefined}
                                />
                                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <label htmlFor="password" className="text-sm font-medium text-slate-700 ml-1">
                                Şifre
                            </label>
                            <div className="relative group">
                                <Input
                                    id="password"
                                    type={showPassword ? "text" : "password"}
                                    autoComplete="current-password"
                                    className={cn(
                                        "h-12 rounded-[14px] bg-white/60 border-transparent pl-11 pr-12",
                                        "focus:bg-white focus:border-blue-500/50 focus:ring-4 focus:ring-blue-500/10",
                                        "transition-all duration-200",
                                        error && !lockoutTime && "border-red-400"
                                    )}
                                    placeholder="Şifrenizi girin"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    disabled={isLoading || !!lockoutTime}
                                    aria-describedby={error ? "error-message" : undefined}
                                />
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className={cn(
                                        "absolute right-4 top-1/2 -translate-y-1/2 p-1 rounded-md",
                                        "text-slate-400 hover:text-blue-600 hover:bg-blue-50",
                                        "transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                                    )}
                                    disabled={isLoading || !!lockoutTime}
                                    aria-label={showPassword ? "Şifreyi gizle" : "Şifreyi göster"}
                                >
                                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                </button>
                            </div>
                        </div>

                        {/* Error Message */}
                        <AnimatePresence mode="wait">
                            {error && (
                                <motion.div
                                    id="error-message"
                                    role="alert"
                                    initial={{ opacity: 0, y: -10, height: 0 }}
                                    animate={{ opacity: 1, y: 0, height: 'auto' }}
                                    exit={{ opacity: 0, y: -10, height: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="flex items-center gap-2 px-3 py-2.5 rounded-xl bg-red-50 border border-red-100"
                                >
                                    <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                                    <span className="text-xs text-red-600 font-medium">{error}</span>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Rate Limit Countdown UI */}
                        <AnimatePresence>
                            {lockoutTime && (
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.9 }}
                                    className="flex flex-col items-center py-3 gap-2"
                                >
                                    <div className="relative">
                                        <CircularProgress value={remainingSeconds} max={30} />
                                        <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-red-600">
                                            {remainingSeconds}
                                        </span>
                                    </div>
                                    <span className="text-xs text-slate-500">saniye bekleyin</span>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Submit Button */}
                        <Button
                            type="submit"
                            className={cn(
                                "w-full h-12 mt-1 rounded-xl text-base font-semibold",
                                "shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40",
                                "transition-all duration-200",
                                lockoutTime && "opacity-50 cursor-not-allowed"
                            )}
                            isLoading={isLoading}
                            disabled={!!lockoutTime || isLoading}
                        >
                            {isLoading ? 'Giriş yapılıyor...' : 'Giriş Yap'}
                        </Button>
                    </form>

                    {/* Footer hint */}
                    <p className="text-xs text-slate-400 text-center mt-6">
                        Güvenli bağlantı ile korunmaktadır
                    </p>
                </motion.div>
            </motion.div>
        </div>
    )
}
