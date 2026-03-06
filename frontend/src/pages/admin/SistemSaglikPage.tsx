import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { adminHealthApi } from '@/services/api/legacy'
import { useNotify } from '@/context/NotificationContext'
import { Activity, Database, Server, RefreshCw, HardDrive } from 'lucide-react'

export default function SistemSaglikPage() {
    const [health, setHealth] = useState<any>(null)
    const [loading, setLoading] = useState(true)
    const { notify } = useNotify()

    useEffect(() => {
        loadHealth()
    }, [])

    const loadHealth = async () => {
        try {
            setLoading(true)
            const data = await adminHealthApi.getHealth()
            setHealth(data)
        } catch (error) {
            console.error('Failed to load system health:', error)
            notify('error', 'Sistem sağlığı verileri yüklenemedi')
        } finally {
            setLoading(false)
        }
    }

    const handleResetCb = async (serviceName: string) => {
        try {
            await adminHealthApi.resetCircuitBreaker(serviceName)
            notify('success', `${serviceName} devre kesici sıfırlandı`)
            loadHealth()
        } catch (error: any) {
            notify('error', error.message || 'Sıfırlama başarısız')
        }
    }

    const handleBackup = async () => {
        try {
            await adminHealthApi.triggerBackup()
            notify('success', 'Veritabanı yedekleme işlemi başlatıldı')
        } catch (error: any) {
            notify('error', error.message || 'Yedekleme başlatılamadı')
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-neutral-900">Sistem Sağlığı</h1>
                    <p className="text-neutral-500 mt-1">Servis durumlarını, veritabanı performansını ve devre kesicileri izleyin.</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={loadHealth} disabled={loading}>
                        <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                        Yenile
                    </Button>
                    <Button variant="glossy-purple" onClick={handleBackup}>
                        <HardDrive className="w-4 h-4 mr-2" />
                        Manuel Yedek Al
                    </Button>
                </div>
            </div>

            {loading && !health ? (
                <div className="flex justify-center items-center h-48">
                     <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                </div>
            ) : health ? (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <Card padding="md" className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center shrink-0">
                                <Activity className="w-6 h-6 text-emerald-500" />
                            </div>
                            <div>
                                <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">Genel Durum</p>
                                <p className="text-xl font-black text-neutral-900 mt-0.5" style={{ color: health.status === 'healthy' ? '#10b981' : '#f59e0b'}}>{health.status || 'OK'}</p>
                            </div>
                        </Card>
                        <Card padding="md" className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center shrink-0">
                                <Database className="w-6 h-6 text-blue-500" />
                            </div>
                            <div>
                                <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">Veritabanı</p>
                                <p className="text-xl font-black text-neutral-900 mt-0.5">{health.components?.database?.status || 'Online'}</p>
                            </div>
                        </Card>
                        <Card padding="md" className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-xl bg-purple-50 flex items-center justify-center shrink-0">
                                <Server className="w-6 h-6 text-purple-500" />
                            </div>
                            <div>
                                <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">Redis/Cache</p>
                                <p className="text-xl font-black text-neutral-900 mt-0.5">{health.components?.redis?.status || 'Online'}</p>
                            </div>
                        </Card>
                    </div>

                    <Card padding="none">
                        <div className="p-4 border-b border-neutral-100 bg-neutral-50/50 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Server className="w-5 h-5 text-neutral-500" />
                                <h2 className="text-base font-bold text-neutral-800">Servis Devre Kesiciler</h2>
                            </div>
                        </div>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Servis Adı</TableHead>
                                    <TableHead>Durum</TableHead>
                                    <TableHead>Hata Sayısı</TableHead>
                                    <TableHead>Detay</TableHead>
                                    <TableHead className="text-right">İşlemler</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {health.circuit_breakers && Object.entries(health.circuit_breakers).map(([key, cb]: [string, any]) => (
                                    <TableRow key={key}>
                                        <TableCell className="font-medium">{key}</TableCell>
                                        <TableCell>
                                            <Badge variant={cb.state === 'closed' ? 'success' : cb.state === 'half-open' ? 'warning' : 'error'}>
                                                {cb.state}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>{cb.failures || 0}</TableCell>
                                        <TableCell className="text-neutral-500 text-sm max-w-xs truncate">{cb.last_error || '-'}</TableCell>
                                        <TableCell className="text-right">
                                            {cb.state !== 'closed' && (
                                                <Button 
                                                    variant="outline" 
                                                    size="sm" 
                                                    className="h-8"
                                                    onClick={() => handleResetCb(key)}
                                                >
                                                    <RefreshCw className="w-4 h-4 mr-2" />
                                                    Sıfırla
                                                </Button>
                                            )}
                                        </TableCell>
                                    </TableRow>
                                ))}
                                {(!health.circuit_breakers || Object.keys(health.circuit_breakers).length === 0) && (
                                    <TableRow>
                                        <TableCell colSpan={5} className="h-32 text-center text-neutral-500">
                                            Devre kesici bilgisi bulunamadı
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </Card>
                </>
            ) : null}
        </div>
    )
}
