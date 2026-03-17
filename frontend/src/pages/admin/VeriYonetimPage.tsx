import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { adminImportsApi } from '@/services/api/legacy'
import { useNotify } from '@/context/NotificationContext'
import { Database, RotateCcw } from 'lucide-react'

export default function VeriYonetimPage() {
    const [history, setHistory] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [rollingBack, setRollingBack] = useState<number | null>(null)
    const { notify } = useNotify()

    useEffect(() => {
        loadHistory()
    }, [])

    const loadHistory = async () => {
        try {
            setLoading(true)
            const data = await adminImportsApi.getHistory(50)
            setHistory(data)
        } catch (error) {
            console.error('Failed to load imports history:', error)
            notify('error', 'Aktarım geçmişi yüklenemedi')
        } finally {
            setLoading(false)
        }
    }

    const handleRollback = async (jobId: number) => {
        if (!window.confirm('Bu aktarımı geri almak istediğinize emin misiniz? Bu işlem kalıcıdır ve ilgili verileri silecektir.')) {
            return
        }

        try {
            setRollingBack(jobId)
            await adminImportsApi.rollback(jobId)
            notify('success', 'İşlem başarıyla geri alındı')
            loadHistory()
        } catch (error: any) {
            notify('error', error.message || 'Geri alma başarısız')
        } finally {
            setRollingBack(null)
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-primary">Veri İçe Aktarım ve Rollback</h1>
                    <p className="text-secondary mt-1">Geçmiş Excel/CSV aktarımlarını görüntüleyin ve gerekirse geri alın.</p>
                </div>
            </div>

            <Card padding="none">
                <div className="p-4 border-b border-border bg-bg-elevated/50 flex items-center gap-2">
                    <Database className="w-5 h-5 text-secondary" />
                    <h2 className="text-base font-bold text-primary">Aktarım Geçmişi</h2>
                </div>
                {loading ? (
                    <div className="flex justify-center items-center h-48">
                         <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : (
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Dosya Adı</TableHead>
                                <TableHead>Tip</TableHead>
                                <TableHead>Tarih</TableHead>
                                <TableHead>Durum</TableHead>
                                <TableHead>Kayıt (B/H/T)</TableHead>
                                <TableHead className="text-right">İşlemler</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {history.map((job) => (
                                <TableRow key={job.id}>
                                    <TableCell className="font-medium">{job.dosya_adi}</TableCell>
                                    <TableCell className="uppercase text-xs font-bold text-secondary">{job.aktarim_tipi}</TableCell>
                                    <TableCell className="text-sm">
                                        {new Date(job.baslama_zamani).toLocaleString('tr-TR')}
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant={
                                            job.durum === 'tamamlandi' ? 'success' :
                                            job.durum === 'hata' ? 'danger' :
                                            job.durum === 'geri_alindi' ? 'warning' : 'default'
                                        }>
                                            {job.durum.replace('_', ' ')}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-sm">
                                        <span className="text-success font-medium">{job.basarili}</span> / 
                                        <span className="text-danger font-medium ml-1">{job.hatali}</span> / 
                                        <span className="text-secondary ml-1">{job.toplam}</span>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <Button 
                                            variant="outline" 
                                            size="sm" 
                                            className="h-8 text-warning hover:text-warning/80 hover:bg-warning/5 border-warning/20"
                                            onClick={() => handleRollback(job.id)}
                                            disabled={job.durum === 'geri_alindi' || rollingBack === job.id}
                                        >
                                            {rollingBack === job.id ? (
                                                <div className="w-3 h-3 border-2 border-warning/20 border-t-warning rounded-full animate-spin mr-2" />
                                            ) : (
                                                <RotateCcw className="w-3 h-3 mr-2" />
                                            )}
                                            Geri Al
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                            {history.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={6} className="h-32 text-center text-secondary">
                                        Aktarım geçmişi bulunamadı
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
