import { Card } from '@/components/ui/Card'
import { Activity, Database, Server, Users } from 'lucide-react'

export default function OverviewPage() {
    return (
        <div className="space-y-6">
            <div className="mb-6">
                <h1 className="text-2xl font-bold tracking-tight text-neutral-900">Sistem Genel Bakış</h1>
                <p className="text-neutral-500 mt-1">Sisteminizin güncel durumunu takip edin.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card padding="md" className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center shrink-0">
                        <Users className="w-6 h-6 text-blue-500" />
                    </div>
                    <div>
                        <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">Aktif Kullanıcı</p>
                        <p className="text-2xl font-black text-neutral-900 mt-0.5">8</p>
                    </div>
                </Card>
                <Card padding="md" className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center shrink-0">
                        <Server className="w-6 h-6 text-emerald-500" />
                    </div>
                    <div>
                        <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">Sistem Durumu</p>
                        <p className="text-2xl font-black text-emerald-600 mt-0.5">Aktif</p>
                    </div>
                </Card>
                <Card padding="md" className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-amber-50 flex items-center justify-center shrink-0">
                        <Database className="w-6 h-6 text-amber-500" />
                    </div>
                    <div>
                        <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">Veritabanı Yükü</p>
                        <p className="text-2xl font-black text-neutral-900 mt-0.5">42%</p>
                    </div>
                </Card>
                <Card padding="md" className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-purple-50 flex items-center justify-center shrink-0">
                        <Activity className="w-6 h-6 text-purple-500" />
                    </div>
                    <div>
                        <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">Hata Oranı</p>
                        <p className="text-2xl font-black text-neutral-900 mt-0.5">0.01%</p>
                    </div>
                </Card>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
                <Card padding="md">
                    <div className="space-y-4">
                        <h3 className="font-bold text-neutral-900 border-b border-neutral-100 pb-2">Hızlı İşlemler</h3>
                        <p className="text-sm text-neutral-500">Sık kullanılan yönetim araçlarına buradan erişebilirsiniz.</p>
                        <div className="grid grid-cols-1 gap-2">
                             <a 
                                href="/settings/physical-data" 
                                className="flex items-center justify-between p-3 rounded-lg border border-neutral-200 hover:bg-neutral-50 transition-colors group"
                             >
                                <div className="flex items-center gap-3">
                                    <Database className="w-5 h-5 text-amber-500" />
                                    <div>
                                        <p className="font-semibold text-neutral-900 group-hover:text-blue-600 transition-colors">Fiziksel Veri Girişi</p>
                                        <p className="text-xs text-neutral-500">Araç ve dorse fiziksel parametrelerini yönetin</p>
                                    </div>
                                </div>
                             </a>
                        </div>
                    </div>
                </Card>
                <Card padding="md" className="h-64 flex flex-col items-center justify-center text-neutral-400 bg-neutral-50/50">
                    <p className="font-medium">Sistem Yük Grafiği</p>
                    <p className="text-xs mt-2">Geliştirme aşamasında</p>
                </Card>
            </div>
        </div>
    )
}
