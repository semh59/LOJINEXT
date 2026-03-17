import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { adminApi } from '@/services/api/legacy'
import { Save, AlertCircle } from 'lucide-react'
import { useNotify } from '@/context/NotificationContext'

interface ConfigItem {
    anahtar: string
    deger: any
    tip: string
    birim?: string
    min_deger?: number
    max_deger?: number
    grup: string
    aciklama?: string
    yeniden_baslat: boolean
}

export default function KonfigurasyonPage() {
    const [configs, setConfigs] = useState<ConfigItem[]>([])
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState<string | null>(null)
    const [localValues, setLocalValues] = useState<Record<string, any>>({})
    const { notify } = useNotify()

    useEffect(() => {
        loadConfigs()
    }, [])

    const loadConfigs = async () => {
        setLoading(true)
        try {
            const data = await adminApi.getConfigs()
            setConfigs(data)
            
            // Initialize local state
            const initialValues: Record<string, any> = {}
            data.forEach((c: ConfigItem) => {
                initialValues[c.anahtar] = c.deger
            })
            setLocalValues(initialValues)
        } catch (error) {
            console.error('Failed to load configs', error)
            notify('error', 'Konfigürasyonlar yüklenemedi.')
        } finally {
            setLoading(false)
        }
    }

    const handleSave = async (key: string) => {
        setSaving(key)
        try {
            const val = localValues[key]
            await adminApi.updateConfig(key, val, "Admin panel arayüzünden güncellendi.")
            notify('success', 'Ayar başarıyla kaydedildi.')
            loadConfigs() // Refresh
        } catch (error: any) {
            const msg = error.response?.data?.detail || 'Kaydetme başarısız.'
            notify('error', msg)
        } finally {
            setSaving(null)
        }
    }

    const handleChange = (key: string, value: any) => {
        setLocalValues(prev => ({ ...prev, [key]: value }))
    }

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
            </div>
        )
    }

    // Group configurations
    const groupedConfigs = configs.reduce((acc, config) => {
        if (!acc[config.grup]) acc[config.grup] = []
        acc[config.grup].push(config)
        return acc
    }, {} as Record<string, ConfigItem[]>)

    return (
        <div className="max-w-4xl space-y-6">
            <div className="mb-6">
                <h1 className="text-2xl font-bold tracking-tight text-primary">Konfigürasyon Yönetimi</h1>
                <p className="text-secondary mt-1">Platform davranışlarını, ML parametrelerini ve sistem sınırlarını yönetin.</p>
            </div>

            {Object.entries(groupedConfigs).map(([group, items]) => (
                <Card key={group} padding="md">
                    <h2 className="text-lg font-bold text-primary capitalize mb-4 border-b border-border pb-2">
                        {group.replace('_', ' ')} Ayarları
                    </h2>
                    
                    <div className="space-y-6">
                        {items.map(config => (
                            <div key={config.anahtar} className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start p-4 bg-bg-elevated/50 rounded-xl border border-border">
                                <div>
                                    <label className="text-sm font-bold text-primary">{config.anahtar}</label>
                                    {config.aciklama && (
                                        <p className="text-xs text-secondary mt-1">{config.aciklama}</p>
                                    )}
                                    {config.yeniden_baslat && (
                                        <div className="flex items-center gap-1.5 text-warning mt-2 bg-warning/10 px-2 py-1 rounded w-fit">
                                            <AlertCircle className="w-3 h-3" />
                                            <span className="text-[10px] font-bold">Yeniden Başlatma Gerektirir</span>
                                        </div>
                                    )}
                                </div>
                                <div className="md:col-span-2 flex items-start gap-3">
                                    <div className="relative flex-1">
                                        <Input
                                            type={config.tip === 'int' || config.tip === 'float' ? 'number' : 'text'}
                                            value={localValues[config.anahtar] ?? ''}
                                            onChange={(e) => {
                                                const val = e.target.value
                                                handleChange(
                                                    config.anahtar, 
                                                    config.tip === 'int' ? parseInt(val) : 
                                                    config.tip === 'float' ? parseFloat(val) : val
                                                )
                                            }}
                                            className="w-full"
                                        />
                                        {config.birim && (
                                            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-secondary">
                                                {config.birim}
                                            </span>
                                        )}
                                    </div>
                                    
                                    <Button
                                        variant="primary"
                                        onClick={() => handleSave(config.anahtar)}
                                        disabled={saving === config.anahtar || localValues[config.anahtar] === config.deger}
                                        className="shrink-0"
                                    >
                                        {saving === config.anahtar ? (
                                            <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                        ) : (
                                            <>
                                                <Save className="w-4 h-4 mr-2" />
                                                Kaydet
                                            </>
                                        )}
                                    </Button>
                                </div>
                            </div>
                        ))}
                    </div>
                </Card>
            ))}
        </div>
    )
}
