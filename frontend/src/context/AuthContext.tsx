import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authApi, tokenStorage } from '../services/api'
import { User } from '../types'

interface AuthContextType {
    user: User | null
    isAuthenticated: boolean
    isLoading: boolean
    login: (username: string, password: string) => Promise<void>
    logout: () => Promise<void>
    error: string | null
    hasPermission: (permission: string) => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Token kontrolü ve kullanıcı bilgilerini getirme
    useEffect(() => {
        async function initAuth() {
            const token = tokenStorage.get()
            if (token) {
                try {
                    const userData = await authApi.getMe()
                    setUser({
                        id: userData.id,
                        username: userData.kullanici_adi || userData.username,
                        full_name: userData.ad_soyad || userData.full_name,
                        role: userData.rol?.ad || userData.rol || userData.role,
                        is_active: userData.aktif || userData.is_active
                    })
                } catch (err) {
                    console.error('Session restoration failed', err)
                    tokenStorage.remove()
                    setUser(null)
                }
            }
            setIsLoading(false)
        }
        initAuth()
    }, [])

    const login = async (username: string, password: string) => {
        setError(null)
        setIsLoading(true)

        try {
            const response = await authApi.login(username, password)
            tokenStorage.set(response.access_token, response.refresh_token)

            // Login sonrası kullanıcı detaylarını çek
            const userData = await authApi.getMe()
            setUser({
                id: userData.id,
                username: userData.kullanici_adi || userData.username,
                full_name: userData.ad_soyad || userData.full_name,
                role: userData.rol?.ad || userData.rol || userData.role,
                is_active: userData.aktif || userData.is_active
            })
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Giriş yapılamadı'
            setError(message)
            throw err
        } finally {
            setIsLoading(false)
        }
    }

    const logout = async () => {
        try {
            await authApi.logout()
        } catch (e) {
            console.error('Backend logout failed', e)
        } finally {
            tokenStorage.remove()
            setUser(null)
            // Redirect will be handled by components utilizing this context or use window.location if necessary.
        }
    }

    const hasPermission = (permission: string): boolean => {
        if (!user) return false
        
        const role = user.role?.toString() || ''
        const isAdmin = role === 'SuperAdmin' || role === 'Admin' || role === 'super_admin' || role === 'admin'
        
        // Super/Admin her şeye yetkilidir (Sistem dışı)
        if (isAdmin) {
            if (permission.startsWith('system:')) return false
            return true
        }
        
        // Driver yetkileri
        if (role === 'Driver' || role === 'driver') {
            const allowed = ['sefer:read', 'arac:read']
            return allowed.includes(permission)
        }
        
        return false
    }

    return (
        <AuthContext.Provider
            value={{
                user,
                isAuthenticated: !!user,
                isLoading,
                login,
                logout,
                error,
                hasPermission
            }}
        >
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}
