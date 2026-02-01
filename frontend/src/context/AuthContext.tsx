import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authApi, tokenStorage } from '../services/api'
import { User } from '../types'

interface AuthContextType {
    user: User | null
    isAuthenticated: boolean
    isLoading: boolean
    login: (username: string, password: string) => Promise<void>
    logout: () => void
    error: string | null
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
                        username: userData.kullanici_adi,
                        full_name: userData.ad_soyad,
                        role: userData.rol,
                        is_active: userData.aktif
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
            tokenStorage.set(response.access_token)

            // Login sonrası kullanıcı detaylarını çek
            const userData = await authApi.getMe()
            setUser({
                id: userData.id,
                username: userData.kullanici_adi,
                full_name: userData.ad_soyad,
                role: userData.rol,
                is_active: userData.aktif
            })
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Giriş yapılamadı'
            setError(message)
            throw err
        } finally {
            setIsLoading(false)
        }
    }

    const logout = () => {
        tokenStorage.remove()
        setUser(null)
        // Opsiyonel: Backend logout endpoint varsa çağrılabilir
    }

    return (
        <AuthContext.Provider
            value={{
                user,
                isAuthenticated: !!user,
                isLoading,
                login,
                logout,
                error
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
