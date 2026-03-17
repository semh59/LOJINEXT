import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useForm, SubmitHandler, FieldValues } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useQuery } from '@tanstack/react-query'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { Trip, Vehicle, Driver, Guzergah } from '../../types'
import { vehiclesApi, driversApi, locationService, weatherApi } from '../../services/api'
import { Truck, User, MapPin, ChevronRight, ChevronLeft, Loader2, Weight, Check, Route } from 'lucide-react'
import { cn } from '../../lib/utils'
import { WeatherAnalysisCard } from '../weather/WeatherAnalysisCard'

const stepperSchema = z.object({
    arac_id: z.coerce.number().int().min(1, 'Araç seçimi gereklidir'),
    sofor_id: z.coerce.number().int().min(1, 'Şoför seçimi gereklidir'),
    guzergah_id: z.coerce.number().int().min(0).optional().transform(v => (v === 0 || v === undefined) ? undefined : v),
    
    // Auto-filled but required
    cikis_yeri: z.string().min(1, 'Çıkış yeri'), 
    varis_yeri: z.string().min(1, 'Varış yeri'),
    mesafe_km: z.coerce.number().min(0.1, 'Mesafe > 0 olmalı'),
    
    // Weights
    bos_agirlik_kg: z.coerce.number().min(0).catch(0),
    dolu_agirlik_kg: z.coerce.number().min(0).catch(0),
    net_kg: z.coerce.number().min(0).catch(0),
    ton: z.coerce.number().min(0).catch(0),
    
    tarih: z.string(),
    saat: z.string(),
    _datetime: z.string(),
    durum: z.string()
})

type StepperFormData = z.infer<typeof stepperSchema>

interface NewTripStepperProps {
    onComplete: (data: Partial<Trip>) => void
    onCancel: () => void
    isSubmitting?: boolean
}

const steps = [
    { id: 1, title: 'Araç Seçimi', icon: Truck },
    { id: 2, title: 'Sürücü Ata', icon: User },
    { id: 3, title: 'Rota & Yük', icon: MapPin },
]

export function NewTripStepper({ onComplete, onCancel, isSubmitting = false }: NewTripStepperProps) {
    const [currentStep, setCurrentStep] = useState(1)
    const [weatherImpact, setWeatherImpact] = useState<number | null>(null)
    const [weatherLoading, setWeatherLoading] = useState(false)

    // Data Fetching
    const { data: vehiclesData = [] } = useQuery({ queryKey: ['vehicles', 'active'], queryFn: () => vehiclesApi.getAll({ aktif_only: true }) })
    const { data: driversData = [] } = useQuery({ queryKey: ['drivers', 'active'], queryFn: () => driversApi.getAll({ aktif_only: true }) })
    const { data: routesData = [] } = useQuery({ queryKey: ['routes', 'active'], queryFn: () => locationService.getAll({ limit: 1000 }) })
    
    const vehicles = Array.isArray(vehiclesData) ? vehiclesData : (vehiclesData as any).items || []
    const drivers = Array.isArray(driversData) ? driversData : (driversData as any).items || []
    const routes = Array.isArray(routesData) ? routesData : (routesData as any).items || []

    const { register, handleSubmit, watch, setValue, trigger, formState: { errors } } = useForm<StepperFormData & FieldValues>({
        resolver: zodResolver(stepperSchema) as any,
        defaultValues: {
            durum: 'Planlandı',
            tarih: new Date().toISOString().split('T')[0],
            saat: new Date().toTimeString().slice(0, 5),
            _datetime: new Date().toISOString().slice(0, 16),
            ton: 0,
            mesafe_km: 0,
            guzergah_id: 0,
            bos_agirlik_kg: 0,
            dolu_agirlik_kg: 0,
            net_kg: 0
        }
    })

    const watchAracId = watch('arac_id')
    const watchSoforId = watch('sofor_id')
    const watchGuzergahId = watch('guzergah_id')
    const watchCikis = watch('cikis_yeri')
    const watchVaris = watch('varis_yeri')
    const watchTarih = watch('tarih')
    const watchBos = watch('bos_agirlik_kg')
    const watchDolu = watch('dolu_agirlik_kg')

    // Auto-Calculate Net Weight & Ton
    useEffect(() => {
        const bos = Number(watchBos || 0);
        const dolu = Number(watchDolu || 0);
        if (dolu > bos) {
            const net = dolu - bos;
            setValue('net_kg', net);
            setValue('ton', Number((net / 1000).toFixed(2))); // Map kg to ton
        } else {
            setValue('net_kg', 0);
            setValue('ton', 0);
        }
    }, [watchBos, watchDolu, setValue]);

    // Handle Route Selection
    useEffect(() => {
        if (watchGuzergahId && routes.length > 0) {
            const selectedRoute = (routes as Guzergah[]).find(r => r.id === Number(watchGuzergahId));
            if (selectedRoute) {
                setValue('cikis_yeri', selectedRoute.cikis_yeri);
                setValue('varis_yeri', selectedRoute.varis_yeri);
                setValue('mesafe_km', selectedRoute.mesafe_km);
                
                // Trigger weather check immediately after route set
                // We do this by depending on watchCikis/watchVaris below
            }
        }
    }, [watchGuzergahId, routes, setValue]);

    // Weather Check Logic
    useEffect(() => {
        if (currentStep === 3 && watchCikis && watchVaris) {
            const timer = setTimeout(async () => {
                setWeatherLoading(true)
                try {
                    // Start fresh search or use route coordinates if we had them (simplified to search for now)
                    const res = await locationService.searchByRoute(watchCikis, watchVaris)
                    if (res.found && res.location?.cikis_lat) {
                        const imp = await weatherApi.getTripImpact({
                            cikis_lat: res.location.cikis_lat, cikis_lon: res.location.cikis_lon!,
                            varis_lat: res.location.varis_lat!, varis_lon: res.location.varis_lon!,
                            trip_date: watchTarih
                        })
                        setWeatherImpact(imp.fuel_impact_factor)
                    } else setWeatherImpact(null)
                } catch { setWeatherImpact(null) } finally { setWeatherLoading(false) }
            }, 1000)
            return () => clearTimeout(timer)
        }
    }, [watchCikis, watchVaris, watchTarih, currentStep])

    const handleNext = async () => {
        let isValid = false
        if (currentStep === 1) isValid = await trigger('arac_id')
        else if (currentStep === 2) isValid = await trigger('sofor_id')
        else if (currentStep === 3) isValid = await trigger(['guzergah_id', 'bos_agirlik_kg', 'dolu_agirlik_kg'])

        if (isValid) {
            if (currentStep < 3) setCurrentStep(c => c + 1)
            else {
                // Submit logic
                handleSubmit(onSubmit as any)()
            }
        }
    }

    const onSubmit: SubmitHandler<StepperFormData> = (data) => {
        const { _datetime, ...tripData } = data
        onComplete(tripData as any)
    }


    return (
        <div className="bg-surface/40 backdrop-blur-xl p-8 rounded-[32px] border border-border relative overflow-hidden">
            <div className="flex justify-between relative mb-12">
                <div className="absolute top-1/2 left-0 right-0 h-1 bg-bg-elevated -z-10 rounded-full"></div>
                <div className="absolute top-1/2 left-0 h-1 bg-accent -z-10 rounded-full transition-all duration-500" style={{ width: `${((currentStep - 1) / 2) * 100}%` }}></div>
                {steps.map((s) => (
                    <div key={s.id} className="flex flex-col items-center gap-2 bg-transparent px-2">
                        <div className={cn("w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all", 
                            s.id === currentStep 
                                ? "border-accent bg-accent text-bg-base scale-110 shadow-lg shadow-accent/20" 
                                : s.id < currentStep 
                                    ? "border-success bg-success text-bg-base" 
                                    : "border-border bg-surface text-secondary"
                        )}>
                            {s.id < currentStep ? <Check className="w-5 h-5" /> : <s.icon className="w-5 h-5" />}
                        </div>
                        <span className={cn("text-xs font-bold", s.id === currentStep ? "text-accent" : "text-secondary")}>{s.title}</span>
                    </div>
                ))}
            </div>

            <div className="min-h-[350px] max-h-[50vh] overflow-y-auto pr-2 overflow-x-hidden">
                <AnimatePresence mode="wait">
                    {/* STEP 1: ARAÇ */}
                    {currentStep === 1 && (
                        <motion.div key="step1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-4">
                            <h3 className="text-xl font-bold text-primary mb-4">Hangi araç yola çıkacak?</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {(vehicles as Vehicle[]).map(v => (
                                    <div key={v.id} onClick={() => { if(v.id) { setValue('arac_id', v.id); trigger('arac_id'); } }} className={cn("p-4 rounded-xl border-2 cursor-pointer transition-all", watchAracId === v.id ? "border-accent bg-accent/10 ring-2 ring-accent/20" : "border-border hover:border-accent/40 bg-surface")}>
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-bg-elevated rounded-lg text-secondary"><Truck className="w-6 h-6" /></div>
                                            <div><div className="font-bold text-primary">{v.plaka}</div><div className="text-xs text-secondary">{v.marka} - {v.model}</div></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                            {errors.arac_id && <p className="text-xs text-danger font-medium">{errors.arac_id.message}</p>}
                        </motion.div>
                    )}

                    {/* STEP 2: SÜRÜCÜ */}
                    {currentStep === 2 && (
                        <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-4">
                            <h3 className="text-xl font-bold text-primary mb-4">Sürücüyü belirleyin</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {(drivers as Driver[]).map(d => (
                                    <div key={d.id} onClick={() => { if(d.id) { setValue('sofor_id', d.id); trigger('sofor_id'); } }} className={cn("p-4 rounded-xl border-2 cursor-pointer transition-all", watchSoforId === d.id ? "border-accent bg-accent/10 ring-2 ring-accent/20" : "border-border hover:border-accent/40 bg-surface")}>
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-bg-elevated rounded-lg text-secondary"><User className="w-6 h-6" /></div>
                                            <div><div className="font-bold text-primary">{d.ad_soyad}</div><div className="text-xs text-secondary">{d.ehliyet_sinifi} Sınıfı • {d.score} Puan</div></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                            {errors.sofor_id && <p className="text-xs text-danger font-medium">{errors.sofor_id.message}</p>}
                        </motion.div>
                    )}

                    {/* STEP 3: ROTA & YÜK (REFACTORED) */}
                    {currentStep === 3 && (
                        <motion.div key="step3" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-6">
                            <h3 className="text-xl font-bold text-primary">Rota ve yük detayları</h3>
                            
                            {/* Weather Card (Conditional) */}
                            {/* Weather Card (Reusable) */}
                            <WeatherAnalysisCard weatherImpact={weatherImpact} weatherLoading={weatherLoading} />
 
                            {/* Route Selection */}
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-secondary uppercase tracking-wider flex items-center gap-2">
                                        <Route className="w-4 h-4" /> Güzergah Seçimi
                                    </label>
                                    <select
                                        {...register('guzergah_id')}
                                        className="w-full text-lg font-bold p-4 rounded-xl border-2 border-border focus:border-accent focus:ring-4 focus:ring-accent/20 bg-surface transition-all outline-none appearance-none"
                                    >
                                        <option value="">Bir güzergah seçiniz...</option>
                                        {routes?.map((r: Guzergah) => (
                                            <option key={r.id} value={r.id}>
                                                {r.cikis_yeri} ➜ {r.varis_yeri} ({r.mesafe_km} km)
                                            </option>
                                        ))}
                                    </select>
                                    {errors.guzergah_id && <p className="text-xs text-danger font-bold">{errors.guzergah_id.message}</p>}
                                </div>
 
                                {/* Route Details Card */}
                                {Number(watchGuzergahId) > 0 && (
                                    <div className="bg-bg-elevated/20 p-4 rounded-xl border border-border">
                                        <div className="flex items-center justify-between text-sm">
                                            <div className="flex flex-col">
                                                <span className="text-[10px] text-secondary font-bold uppercase">Çıkış</span>
                                                <span className="font-bold text-primary">{watchCikis}</span>
                                            </div>
                                            <div className="flex flex-col items-center px-4">
                                                <span className="text-xs text-secondary/40">➜</span>
                                                <span className="text-[10px] font-black text-secondary text-center uppercase">{watch('mesafe_km')} km</span>
                                            </div>
                                            <div className="flex flex-col items-end">
                                                <span className="text-[10px] text-secondary font-bold uppercase">Varış</span>
                                                <span className="font-bold text-primary">{watchVaris}</span>
                                            </div>
                                        </div>
                                        {/* Hidden inputs to stash data for submit */}
                                        <input type="hidden" {...register('cikis_yeri')} />
                                        <input type="hidden" {...register('varis_yeri')} />
                                        <input type="hidden" {...register('mesafe_km', { valueAsNumber: true })} />
                                    </div>
                                )}
                            </div>

                            {/* Time */}
                            <div className="space-y-1">
                                <label className="text-xs font-bold text-secondary px-1">Planlanan Zaman</label>
                                <Input type="datetime-local" {...register('_datetime')} onChange={e => {
                                    const v = e.target.value; setValue('_datetime', v); setValue('tarih', v.split('T')[0]); setValue('saat', v.split('T')[1] || '00:00');
                                }} />
                            </div>
 
                            {/* Weight Inputs */}
                             <div className="bg-success/5 p-4 rounded-xl border border-success/20 space-y-3">
                                <h4 className="text-xs font-bold text-success uppercase tracking-widest flex items-center gap-2">
                                    <Weight className="w-3.5 h-3.5" /> Kantar / Ağırlık
                                </h4>
                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <label className="text-[10px] font-bold text-secondary ml-1">Boş (kg)</label>
                                        <Input type="number" {...register('bos_agirlik_kg')} className="h-10 text-sm font-semibold" />
                                    </div>
                                    <div>
                                        <label className="text-[10px] font-bold text-secondary ml-1">Dolu (kg)</label>
                                        <Input type="number" {...register('dolu_agirlik_kg')} className="h-10 text-sm font-semibold" />
                                    </div>
                                </div>
                                <div className="pt-2 border-t border-success/20 flex justify-between items-center">
                                    <span className="text-xs font-bold text-success">Net Yük:</span>
                                    <span className="text-lg font-black text-success">{Number(watch('net_kg') || 0).toLocaleString()} kg</span>
                                </div>
                                <input type="hidden" {...register('net_kg')} />
                                <input type="hidden" {...register('ton')} />
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
 
            <div className="flex justify-between mt-8 pt-6 border-t border-border">
                <Button variant="secondary" onClick={currentStep === 1 ? onCancel : () => setCurrentStep(c => c - 1)}>
                    {currentStep === 1 ? 'İptal Et' : <><ChevronLeft className="w-4 h-4 mr-2" /> Geri</>}
                </Button>
                <Button onClick={handleNext} disabled={isSubmitting}>
                    {isSubmitting && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                    {currentStep === 3 ? 'Seferi Oluştur' : <>Devam Et <ChevronRight className="w-4 h-4 ml-2" /></>}
                </Button>
            </div>
        </div>
    )
}
