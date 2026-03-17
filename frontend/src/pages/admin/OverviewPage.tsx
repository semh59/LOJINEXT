import { Card } from '@/components/ui/Card'
import { Activity, Database, Server, Users } from 'lucide-react'

export default function OverviewPage() {
    return (
        <div className="space-y-6">
            <div className="mb-6">
                <h1 className="text-2xl font-bold tracking-tight text-primary">Sistem Genel Bakış</h1>
                <p className="text-secondary mt-1">Sisteminizin güncel durumunu takip edin.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card padding="md" className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-info/10 flex items-center justify-center shrink-0">
                        <Users className="w-6 h-6 text-info" />
                    </div>
                    <div>
                        <p className="text-sm font-bold text-secondary uppercase tracking-widest">Aktif Kullanıcı</p>
                        <p className="text-2xl font-black text-primary mt-0.5">8</p>
                    </div>
                </Card>
                <Card padding="md" className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-success/10 flex items-center justify-center shrink-0">
                        <Server className="w-6 h-6 text-success" />
                    </div>
                    <div>
                        <p className="text-sm font-bold text-secondary uppercase tracking-widest">Sistem Durumu</p>
                        <p className="text-2xl font-black text-success mt-0.5">Aktif</p>
                    </div>
                </Card>
                <Card padding="md" className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-warning/10 flex items-center justify-center shrink-0">
                        <Database className="w-6 h-6 text-warning" />
                    </div>
                    <div>
                        <p className="text-sm font-bold text-secondary uppercase tracking-widest">Veritabanı Yükü</p>
                        <p className="text-2xl font-black text-primary mt-0.5">42%</p>
                    </div>
                </Card>
                <Card padding="md" className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center shrink-0">
                        <Activity className="w-6 h-6 text-accent" />
                    </div>
                    <div>
                        <p className="text-sm font-bold text-secondary uppercase tracking-widest">Hata Oranı</p>
                        <p className="text-2xl font-black text-primary mt-0.5">0.01%</p>
                    </div>
                </Card>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
                <Card padding="md">
                    <div className="space-y-4">
                        <h3 className="font-bold text-primary border-b border-border pb-2">Hızlı İşlemler</h3>
                        <p className="text-sm text-secondary">Sık kullanılan yönetim araçlarına buradan erişebilirsiniz.</p>
                        <div className="grid grid-cols-1 gap-2">
                             <a 
                                href="/settings/physical-data" 
                                className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-bg-elevated transition-colors group"
                             >
                                <div className="flex items-center gap-3">
                                    <Database className="w-5 h-5 text-warning" />
                                    <div>
                                        <p className="font-semibold text-primary group-hover:text-accent transition-colors">Fiziksel Veri Girişi</p>
                                        <p className="text-xs text-secondary">Araç ve dorse fiziksel parametrelerini yönetin</p>
                                    </div>
                                </div>
                             </a>
                        </div>
                    </div>
                </Card>
                <Card padding="md" className="h-64 flex flex-col items-center justify-center text-secondary bg-bg-elevated/50">
                    <p className="font-medium">Sistem Yük Grafiği</p>
                    <p className="text-xs mt-2">Geliştirme aşamasında</p>
                </Card>
            </div>
        </div>
    )
}
