import { Trip } from '../../types'
import { motion } from 'framer-motion'
import { MapPin, Truck, User, ArrowRight } from 'lucide-react'

interface TripListProps {
    trips: Trip[]
    onSelect: (trip: Trip) => void
    loading: boolean
}

export function TripList({ trips, onSelect, loading }: TripListProps) {
    if (loading) {
        return (
            <div className="flex items-center justify-center p-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        )
    }

    if (trips.length === 0) {
        return (
            <div className="text-center p-12 bg-bg-elevated/20 rounded-3xl border border-dashed border-border">
                <div className="w-16 h-16 bg-surface rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm border border-border">
                    <MapPin className="w-8 h-8 text-secondary" />
                </div>
                <h3 className="font-bold text-primary">Aktif Sefer Yok</h3>
                <p className="text-sm text-secondary mt-1">Planlanmış veya devam eden bir sefer bulunmuyor.</p>
            </div>
        )
    }

    return (
        <div className="space-y-4">
            {trips.map((trip, i) => (
                <motion.div
                    key={trip.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    onClick={() => onSelect(trip)}
                    className="group bg-surface rounded-2xl p-5 border border-border hover:border-accent/30 hover:shadow-lg hover:shadow-accent/5 transition-all cursor-pointer relative overflow-hidden"
                >
                    <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-bg-elevated group-hover:bg-accent transition-colors"></div>

                    <div className="flex flex-col md:flex-row md:items-center gap-6 pl-3">
                        {/* Status & ID */}
                        <div className="min-w-[100px]">
                            <span className="text-xs font-mono text-secondary block mb-1">#{trip.id?.toString().padStart(4, '0')}</span>
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${trip.durum === 'Yolda' ? 'bg-accent/10 text-accent' :
                                trip.durum === 'Tamam' ? 'bg-success/10 text-success' :
                                    trip.durum === 'İptal' ? 'bg-danger/10 text-danger' :
                                        'bg-bg-elevated text-secondary'
                                }`}>
                                {trip.durum === 'Yolda' && <span className="w-1.5 h-1.5 rounded-full bg-accent mr-1.5 animate-pulse"></span>}
                                {trip.durum}
                            </span>
                        </div>

                        {/* Route */}
                        <div className="flex-1 flex items-center gap-3">
                            <div className="text-right">
                                <div className="font-bold text-primary">{trip.cikis_yeri}</div>
                                <div className="text-xs text-secondary font-medium">
                                    {new Date(trip.tarih).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })}
                                </div>
                            </div>

                            <div className="flex-1 flex flex-col items-center px-2 min-w-[80px]">
                                <ArrowRight className="w-5 h-5 text-secondary/30" />
                            </div>

                            <div className="text-left">
                                <div className="font-bold text-primary">{trip.varis_yeri}</div>
                                <div className="text-xs text-secondary font-medium">
                                    -
                                </div>
                            </div>
                        </div>

                        {/* Details */}
                        <div className="flex items-center gap-6 border-t md:border-t-0 md:border-l border-border pt-4 md:pt-0 md:pl-6 mt-4 md:mt-0">
                            <div className="flex items-center gap-2">
                                <Truck className="w-4 h-4 text-secondary" />
                                <div className="text-sm">
                                    <div className="font-bold text-primary">{trip.arac_plaka || '34XX000'}</div>
                                    <div className="text-xs text-secondary">Araç</div>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <User className="w-4 h-4 text-secondary" />
                                <div className="text-sm">
                                    <div className="font-bold text-primary">{trip.sofor_ad_soyad?.split(' ')[0] || 'Ahmet'}</div>
                                    <div className="text-xs text-secondary">Sürücü</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </motion.div>
            ))}
        </div>
    )
}
