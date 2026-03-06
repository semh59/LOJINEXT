import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useAuth } from '../context/AuthContext'
import { Eye, EyeOff, Truck, Lock, User, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

import { Button } from '../components/ui/Button'

// Validation Schema
const loginSchema = z.object({
    username: z.string().min(1, 'Kullanıcı adı gerekli'),
    password: z.string().min(1, 'Şifre gerekli'),
})

type LoginFormValues = z.infer<typeof loginSchema>

// Circular Progress for Rate Limit
function CircularProgress({ value, max }: { value: number; max: number }) {
    const radius = 18
    const circumference = 2 * Math.PI * radius
    const progress = ((max - value) / max) * circumference

    return (
        <svg className="w-10 h-10 -rotate-90" viewBox="0 0 44 44">
            <circle
                cx="22"
                cy="22"
                r={radius}
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                className="text-slate-200"
            />
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
                className="text-primary transition-all duration-1000"
            />
        </svg>
    )
}

export default function LoginPage() {
    const navigate = useNavigate()
    const { login, isLoading } = useAuth()
    const [showPassword, setShowPassword] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [failedAttempts, setFailedAttempts] = useState(0)
    const [lockoutTime, setLockoutTime] = useState<number | null>(null)
    const [remainingSeconds, setRemainingSeconds] = useState(0)

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<LoginFormValues>({
        resolver: zodResolver(loginSchema),
    })

    // Handle Rate Limiting
    useEffect(() => {
        if (lockoutTime) {
            const timer = setInterval(() => {
                const now = Date.now()
                if (now >= lockoutTime) {
                    setLockoutTime(null)
                    setFailedAttempts(0)
                } else {
                    setRemainingSeconds(Math.ceil((lockoutTime - now) / 1000))
                }
            }, 1000)
            return () => clearInterval(timer)
        }
    }, [lockoutTime])

    const onSubmit = async (data: LoginFormValues) => {
        setError(null)
        try {
            await login(data.username, data.password)
            navigate('/dashboard')
        } catch (err: any) {
            const newAttempts = failedAttempts + 1
            setFailedAttempts(newAttempts)

            if (err.response?.status === 429) {
                const waitTime = 30 * 1000
                setLockoutTime(Date.now() + waitTime)
                setError('Çok fazla başarısız deneme. Lütfen bekleyin.')
            } else {
                setError('Kullanıcı adı veya şifre hatalı')
            }
        }
    }

    return (
        <div className="font-sans min-h-screen flex items-center justify-center overflow-hidden bg-[var(--bg-dark)] text-slate-100">
            <div className="relative w-full min-h-screen flex flex-col lg:flex-row">
                {/* Left Section: High-tech Visual */}
                <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-[var(--bg-surface)] border-r border-white/5">
                    {/* Abstract background image */}
                    <div 
                        className="absolute inset-0 bg-cover bg-center opacity-80 z-0" 
                        style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuCOAdPgRI1zO2loGtOPll5_3hxJ61EgmcWWrLLpNTg_rQWHpjlO-aZRrpBbcUIAGGHLjv5gVqhD6tMyJAovbEuklVFOGFW2TXDyYBebtN_blUX8u6bJ4nvd652-yrLJVUkcFnuUlSLRF0hBYv7V7Pp19WAjWdr3VGb6lzzooBMK3n63AT0Z7_Q5uDDJDIp1w24mS5p929vF8exlNF_gVnQGChXxRo8hVbh2eY-g_Ulv7WlKZNph0OITPTph19DfP7L3JHRV4wsmsKo')" }}
                    />
                    
                    {/* Overlay Gradients for Depth */}
                    <div className="absolute inset-0 bg-gradient-to-t from-[var(--bg-dark)] via-transparent to-transparent z-10"></div>
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[var(--bg-dark)]/50 to-[var(--bg-dark)] z-10"></div>
                    
                    {/* Branding Text Overlay */}
                    <div className="relative z-20 flex flex-col justify-end p-16 h-full text-slate-100">
                        <div className="mb-0">
                            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/30 text-[var(--color-primary)] text-xs font-black tracking-widest uppercase mb-6 backdrop-blur-md shadow-[0_0_15px_var(--glass-glow-cyan)]">
                                <Truck className="w-4 h-4" />
                                Next Gen Logistics
                            </span>
                            <h2 className="text-5xl font-bold leading-tight mb-4 tracking-tighter">Autonomous Fleet<br/>Intelligence</h2>
                            <p className="text-slate-400 text-lg max-w-md font-sans">
                                Real-time tracking, AI-powered route optimization, and predictive maintenance for the modern supply chain.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Right Section: Login Form */}
                <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12 relative bg-[var(--bg-dark)]">
                    {/* Decorative background glow */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-[var(--color-primary)]/5 rounded-full blur-[100px] pointer-events-none"></div>
                    
                    <div className="w-full max-w-[480px] z-10">
                        {/* Glassmorphic Container */}
                        <div className="relative glass-card shadow-2xl p-8 sm:p-10 overflow-hidden border border-white/5">
                            {/* Decorative top line */}
                            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[var(--color-primary)] to-transparent opacity-50"></div>

                             {/* Header */}
                            <div className="mb-10 mt-4">
                                <div className="flex items-center gap-3 mb-2">
                                    <div className="w-12 h-12 bg-white/5 rounded-xl flex items-center justify-center border border-[var(--color-primary)]/30 shadow-[0_0_15px_var(--glass-glow-cyan)]">
                                          <Truck className="w-7 h-7 text-[var(--color-primary)]" />
                                    </div>
                                    <h1 className="text-white text-4xl font-black tracking-tighter">LojiNext</h1>
                                </div>
                                <p className="text-slate-500 text-sm font-bold uppercase tracking-widest mt-4">Kurumsal Yönetim Paneli</p>
                            </div>

                            {/* Form */}
                            <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-6">
                                {/* Email Field */}
                                <div className="space-y-2 group">
                                    <label className="text-slate-300 text-sm font-semibold flex items-center gap-2">
                                        <User className="w-5 h-5 text-slate-500 group-focus-within:text-[var(--color-primary)] transition-colors" />
                                        Kullanıcı Adı veya E-Posta
                                    </label>
                                    <div className="relative">
                                        <input 
                                            {...register('username')}
                                            className={cn(
                                                "w-full bg-black/40 border border-white/10 text-slate-100 rounded-xl px-5 py-4 focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)]/30 placeholder:text-slate-600 transition-all font-bold text-sm shadow-inner",
                                                errors.username && "border-red-500 focus:border-red-500 focus:ring-red-500/50"
                                            )} 
                                            placeholder="Kullanıcı Adı" 
                                            type="text" 
                                        />
                                        {errors.username && (
                                            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-red-500 text-xs font-semibold">Gerekli</span>
                                        )}
                                    </div>
                                </div>

                                {/* Password Field */}
                                <div className="space-y-2 group">
                                    <div className="flex justify-between items-center">
                                        <label className="text-slate-300 text-sm font-semibold flex items-center gap-2">
                                            <Lock className="w-5 h-5 text-slate-500 group-focus-within:text-[var(--color-primary)] transition-colors" />
                                            Şifre
                                        </label>
                                    </div>
                                     <div className="relative">
                                        <input 
                                            {...register('password')}
                                            className={cn(
                                               "w-full bg-black/40 border border-white/10 text-slate-100 rounded-xl pl-5 pr-12 py-4 focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)]/30 placeholder:text-slate-600 transition-all font-bold text-sm tracking-[0.3em] shadow-inner",
                                               errors.password && "border-red-500 focus:border-red-500 focus:ring-red-500/50"
                                            )} 
                                            placeholder="••••••••" 
                                            type={showPassword ? 'text' : 'password'}
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowPassword(!showPassword)}
                                            className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                                        >
                                            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                        </button>
                                    </div>
                                </div>
                                
                                {/* Error Message */}
                                <AnimatePresence>
                                    {error && (
                                        <motion.div
                                            initial={{ opacity: 0, height: 0 }}
                                            animate={{ opacity: 1, height: 'auto' }}
                                            exit={{ opacity: 0, height: 0 }}
                                            className="bg-red-500/10 text-red-400 p-3 rounded-lg border border-red-500/20 flex items-center justify-center gap-2"
                                        >
                                            <AlertCircle className="w-4 h-4" />
                                            <span className="text-xs font-semibold">{error}</span>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                                
                                {/* Rate Limit Countdown */}
                                <AnimatePresence>
                                    {lockoutTime && (
                                        <motion.div
                                            initial={{ opacity: 0, scale: 0.9 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            exit={{ opacity: 0, scale: 0.9 }}
                                            className="flex flex-col items-center py-2 gap-2"
                                        >
                                            <div className="relative">
                                                <CircularProgress value={remainingSeconds} max={30} />
                                                <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-[#0df2df]">
                                                    {remainingSeconds}
                                                </span>
                                            </div>
                                            <span className="text-xs text-neutral-500 font-medium tracking-tight">Kilitlendiniz, lütfen bekleyin...</span>
                                        </motion.div>
                                    )}
                                </AnimatePresence>

                                {/* Actions */}
                                <div className="flex flex-col gap-4 mt-2">
                                    <Button
                                        type="submit"
                                        variant="glossy-cyan"
                                        isLoading={isLoading}
                                        className="w-full h-14 text-lg"
                                    >
                                        Sisteme Giriş Yap
                                    </Button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
