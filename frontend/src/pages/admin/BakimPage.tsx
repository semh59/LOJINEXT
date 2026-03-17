import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { adminMaintenanceApi } from '@/services/api/legacy'
import { useNotify } from '@/context/NotificationContext'
import { Wrench, CheckCircle } from 'lucide-react'

export default function BakimPage() {
    const [alerts, setAlerts] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const { notify } = useNotify()

    useEffect(() => {
        loadAlerts()
    }, [])

    const loadAlerts = async () => {
        try {
            setLoading(true)
            const data = await adminMaintenanceApi.getAlerts()
            setAlerts(data)
        } catch (error) {
            console.error('Failed to load maintenance alerts:', error)
            notify('error', 'Bakım uyarıları yüklenemedi')
        } finally {
            setLoading(false)
        }
    }

    const handleComplete = async (id: number) => {
        try {
            await adminMaintenanceApi.markComplete(id)
            notify('success', 'Bakım tamamlandı olarak işaretlendi')
            loadAlerts()
        } catch (error: any) {
            notify('error', error.message || 'İşlem başarısız')
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-primary">Bakım ve Onarım Merkezi</h1>
                    <p className="text-secondary mt-1">Araçların yaklaşan ve gecikmiş bakım görevlerini yönetin.</p>
                </div>
            </div>

            <Card padding="none">
                <div className="p-4 border-b border-border bg-bg-elevated/50 flex items-center gap-2">
                    <Wrench className="w-5 h-5 text-secondary" />
                    <h2 className="text-base font-bold text-primary">Acil & Yaklaşan Bakımlar</h2>
                </div>
                {loading ? (
                    <div className="flex justify-center items-center h-48">
                         <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : (
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Araç ID</TableHead>
                                <TableHead>Bakım Tipi</TableHead>
                                <TableHead>Planlanan Tarih / KM</TableHead>
                                <TableHead>Durum</TableHead>
                                <TableHead className="text-right">İşlemler</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {alerts.map((alert) => (
                                <TableRow key={alert.id}>
                                    <TableCell className="font-medium">Araç #{alert.arac_id}</TableCell>
                                    <TableCell className="uppercase text-xs font-bold text-secondary">{alert.bakim_tipi}</TableCell>
                                    <TableCell className="text-sm">
                                        {alert.bakim_tarihi ? new Date(alert.bakim_tarihi).toLocaleDateString('tr-TR') : '-'}  
                                        {alert.km_bilgisi ? ` / ${alert.km_bilgisi} KM` : ''}
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant={
                                            alert.durum === 'gecikmis' ? 'danger' : 
                                            alert.durum === 'yaklasiyor' ? 'warning' : 'default'
                                        }>
                                            {alert.durum || 'Bilinmiyor'}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <Button 
                                            variant="outline" 
                                            size="sm" 
                                            className="h-8 text-success hover:text-success/80 hover:bg-success/5 border-success/20"
                                            onClick={() => handleComplete(alert.id)}
                                        >
                                            <CheckCircle className="w-3 h-3 mr-2" />
                                            Tamamlandı
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                            {alerts.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={5} className="h-32 text-center text-secondary">
                                        Acil bakım uyarısı bulunmamaktadır
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                )}
            </Card>
        </div>
    )
}
