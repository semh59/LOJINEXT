import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useAuth } from '../context/AuthContext'
import { Eye, EyeOff, Loader2, ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { LojiNextLogo } from '../components/common/LojiNextLogo'
import { Input } from '../components/ui/Input'
import { Button } from '../components/ui/Button'

// Validation Schema
const loginSchema = z.object({
    username: z.string().min(1, 'Lütfen kullanıcı adı veya e-posta girin.'),
    password: z.string().min(1, 'Lütfen şifrenizi girin.'),
})

type LoginFormValues = z.infer<typeof loginSchema>

export default function LoginPage() {
    const navigate = useNavigate()
    const { login, isAuthenticated } = useAuth()
    const [showPassword, setShowPassword] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [failedAttempts, setFailedAttempts] = useState(0)
    const [lockoutTime, setLockoutTime] = useState<number | null>(null)
    const [remainingSeconds, setRemainingSeconds] = useState(0)

    const {
        register,
        handleSubmit,
        formState: { errors, isSubmitting },
    } = useForm<LoginFormValues>({
        resolver: zodResolver(loginSchema),
    })

    // Auto-redirect if already logged in (UX/Edge Case Fix)
    useEffect(() => {
        if (isAuthenticated) {
            navigate('/trips', { replace: true })
        }
    }, [isAuthenticated, navigate])

    // Rate Limiting Timer
    useEffect(() => {
        if (lockoutTime) {
            const timer = setInterval(() => {
                const now = Date.now()
                if (now >= lockoutTime) {
                    setLockoutTime(null)
                    setFailedAttempts(0)
                    setError(null)
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
            navigate('/trips')
        } catch (err: any) {
            const newAttempts = failedAttempts + 1
            setFailedAttempts(newAttempts)

            if (err.response?.status === 429 || err.message?.includes('429')) {
                const waitTime = 30 * 1000
                setLockoutTime(Date.now() + waitTime)
                setError('Çok fazla başarısız deneme. Lütfen bir süre bekleyin.')
            } else {
                setError(err.message || 'Kullanıcı adı veya şifre hatalı.')
            }
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-bg-base relative overflow-hidden font-sans">
            <div className="w-full max-w-md px-6 relative z-10 animate-slide-up">
                
                <div className="flex flex-col items-center mb-12">
                    <LojiNextLogo iconSize={44} textSize="text-2xl" />
                </div>

                {/* Main Glass/Surface Card */}
                <div className="bg-surface p-10 sm:p-12 rounded-[24px] border border-border shadow-lg">
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
                        
                        {/* Email / Username */}
                        <div className="space-y-1.5 relative">
                            <label htmlFor="username" className="block text-xs font-black text-secondary uppercase tracking-widest pl-1">
                                E-Posta / Kullanıcı Adı
                            </label>
                            <Input
                                id="username"
                                type="text"
                                {...register('username')}
                                disabled={isSubmitting || !!lockoutTime}
                                error={!!errors.username}
                                placeholder="E-posta adresinizi girin"
                                autoComplete="username"
                            />
                            {errors.username && (
                                <p className="text-danger text-xs font-semibold animate-fade-in pl-1">
                                    {errors.username.message}
                                </p>
                            )}
                        </div>

                        {/* Password */}
                        <div className="space-y-1.5 relative">
                            <label htmlFor="password" className="block text-xs font-black text-secondary uppercase tracking-widest pl-1">
                                Şifre
                            </label>
                            
                            <div className="relative">
                                <Input
                                    id="password"
                                    type={showPassword ? 'text' : 'password'}
                                    {...register('password')}
                                    disabled={isSubmitting || !!lockoutTime}
                                    error={!!errors.password}
                                    className={cn("pr-12", !showPassword && "tracking-widest")}
                                    placeholder="••••••••"
                                    autoComplete="current-password"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    disabled={isSubmitting || !!lockoutTime}
                                    aria-label={showPassword ? "Şifreyi gizle" : "Şifreyi göster"}
                                    className="absolute right-1.5 top-1/2 -translate-y-1/2 w-7 h-7 flex items-center justify-center text-secondary hover:text-primary hover:bg-bg-elevated rounded transition-colors focus:outline-none focus:ring-2 focus:ring-accent/5"
                                >
                                    {showPassword ? <EyeOff strokeWidth={1.5} className="w-4 h-4" /> : <Eye strokeWidth={1.5} className="w-4 h-4" />}
                                </button>
                            </div>
                            {errors.password && (
                                <p className="text-danger text-xs font-semibold animate-fade-in pl-1">
                                    {errors.password.message}
                                </p>
                            )}
                        </div>

                        {/* Rate Limiting & Error Banner */}
                        <AnimatePresence mode="popLayout">
                            {error && (
                                <motion.div
                                    initial={{ opacity: 0, y: -10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, scale: 0.95 }}
                                    className="p-4 rounded-xl text-sm font-medium bg-danger/10 text-danger border border-danger/20 animate-shake"
                                >
                                    {lockoutTime ? (
                                        <div className="flex flex-col items-center text-center gap-1.5 pt-1">
                                            <span className="font-bold text-danger">Güvenlik Kilidi</span>
                                            Lütfen tekrar denemek için <span className="font-black underline tabular-nums">{remainingSeconds}</span> saniye bekleyin.
                                        </div>
                                    ) : (
                                        <p className="flex items-center justify-center text-center">{error}</p>
                                    )}
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Submit Button */}
                        <div className="pt-4">
                            <Button
                                type="submit"
                                variant="primary"
                                disabled={isSubmitting || !!lockoutTime}
                                className="w-full h-11 text-[15px] font-bold group"
                            >
                                {isSubmitting ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin-slow" strokeWidth={2.5} />
                                        <span>Giriş Yapılıyor...</span>
                                    </>
                                ) : (
                                    <>
                                        <span>Sisteme Giriş Yap</span>
                                        <ArrowRight className="w-4 h-4 text-bg-base group-hover:translate-x-1 transition-transform ml-2" strokeWidth={2.5} />
                                    </>
                                )}
                            </Button>
                        </div>
                    </form>
                </div>
            </div>

        </div>
    )
}
