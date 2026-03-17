import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Activity, Fuel, Gauge, Thermometer, AlertCircle } from 'lucide-react'

interface VehicleStatusCardProps {
  plate: string
  model: string
  fuelLevel: number // 0-100 initial
  tirePressure: number // 0-100 initial
  engineTemp: number // 0-120 initial
  status: 'active' | 'warning' | 'critical'
  isSimulated?: boolean
}

export function VehicleStatusCard({ plate, model, fuelLevel: initialFuel, tirePressure: initialTire, engineTemp: initialTemp, status: initialStatus, isSimulated = true }: VehicleStatusCardProps) {
  const [fuelLevel, setFuelLevel] = useState(initialFuel)
  const [tirePressure, setTirePressure] = useState(initialTire)
  const [engineTemp, setEngineTemp] = useState(initialTemp)
  const [status, setStatus] = useState(initialStatus)

  useEffect(() => {
    if (!isSimulated) return

    const interval = setInterval(() => {
      // Zeynep'in önerdiği rastgele veri mantığı (Backend Simulation)
      setFuelLevel(prev => Math.max(0, prev - (Math.random() * 0.5)))
      setTirePressure(prev => {
        const change = (Math.random() - 0.5) * 2
        return Math.min(100, Math.max(60, prev + change))
      })
      setEngineTemp(prev => {
        const change = (Math.random() - 0.5) * 4
        return Math.min(120, Math.max(70, prev + change))
      })
      
      // Dinamik Durum Tahmini (Otonom)
      setStatus(() => {
        if (engineTemp > 105 || fuelLevel < 5) return 'critical'
        if (tirePressure < 80 || fuelLevel < 15) return 'warning'
        return 'active'
      })
    }, 3000)

    return () => clearInterval(interval)
  }, [isSimulated, fuelLevel, tirePressure, engineTemp])
  const getStatusColor = () => {
    switch (status) {
      case 'active': return 'from-success/20 to-success/30 text-success'
      case 'warning': return 'from-warning/20 to-warning/30 text-warning'
      case 'critical': return 'from-danger/20 to-danger/30 text-danger'
      default: return 'from-accent/20 to-accent/30 text-accent'
    }
  }

  const getStatusBadge = () => {
    switch (status) {
      case 'active': return 'bg-success/20 text-success border-success/30'
      case 'warning': return 'bg-warning/20 text-warning border-warning/30'
      case 'critical': return 'bg-danger/20 text-danger border-danger/30 font-black'
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      className="relative overflow-hidden rounded-2xl border border-border bg-surface p-6 shadow-sm"
    >
      {/* Glossy Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent pointer-events-none" />
      
      {/* Header */}
      <div className="flex justify-between items-start mb-8 relative z-10">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-xl font-black text-primary tracking-tight">{plate}</h3>
            <span className={`px-2 py-0.5 rounded-full text-[10px] uppercase tracking-widest border ${getStatusBadge()}`}>
              {status === 'active' ? 'Yolda' : status === 'warning' ? 'Uyarı' : 'Kritik'}
            </span>
          </div>
          <p className="text-xs text-secondary font-bold uppercase tracking-wider">{model}</p>
        </div>
        <div className={`p-3 rounded-2xl bg-gradient-to-br ${getStatusColor()} border border-border/50`}>
          <Activity className="w-6 h-6" />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="space-y-6 relative z-10">
        {/* Fuel Level */}
        <div className="space-y-2">
          <div className="flex justify-between text-[11px] font-black uppercase tracking-widest text-secondary">
            <div className="flex items-center gap-2">
              <Fuel className="w-3.5 h-3.5" />
              <span>Yakit Seviyesi</span>
            </div>
            <span className={fuelLevel < 20 ? 'text-danger' : 'text-primary'}>%{fuelLevel.toFixed(0)}</span>
          </div>
          <div className="h-2 w-full bg-bg-elevated rounded-full overflow-hidden border border-border/50">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${fuelLevel}%` }}
              className={`h-full rounded-full bg-gradient-to-r ${fuelLevel < 20 ? 'from-danger to-danger/80' : 'from-accent to-accent/80'}`}
              transition={{ duration: 1.5, ease: "easeOut" }}
            />
          </div>
        </div>

        {/* Tire Pressure */}
        <div className="space-y-2">
          <div className="flex justify-between text-[11px] font-black uppercase tracking-widest text-secondary">
            <div className="flex items-center gap-2">
              <Gauge className="w-3.5 h-3.5" />
              <span>Lastik Basinci</span>
            </div>
            <span className={tirePressure < 85 ? 'text-warning' : 'text-primary'}>%{tirePressure.toFixed(0)}</span>
          </div>
          <div className="h-2 w-full bg-bg-elevated rounded-full overflow-hidden border border-border/50">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${tirePressure}%` }}
              className="h-full rounded-full bg-gradient-to-r from-success to-success/80"
              transition={{ duration: 1.5, ease: "easeOut", delay: 0.2 }}
            />
          </div>
        </div>

        {/* Engine Temp */}
        <div className="space-y-2">
          <div className="flex justify-between text-[11px] font-black uppercase tracking-widest text-secondary">
            <div className="flex items-center gap-2">
              <Thermometer className="w-3.5 h-3.5" />
              <span>Motor Sicakligi</span>
            </div>
            <span className={engineTemp > 100 ? 'text-danger' : 'text-primary'}>{engineTemp.toFixed(0)}°C</span>
          </div>
          <div className="h-2 w-full bg-bg-elevated rounded-full overflow-hidden border border-border/50">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(engineTemp / 120) * 100}%` }}
              className={`h-full rounded-full bg-gradient-to-r ${engineTemp > 100 ? 'from-danger to-danger/80' : 'from-warning to-warning/80'}`}
              transition={{ duration: 1.5, ease: "easeOut", delay: 0.4 }}
            />
          </div>
        </div>
      </div>

      {/* Warning Footer */}
      {status !== 'active' && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mt-6 p-3 rounded-xl bg-danger/10 border border-danger/20 flex items-center gap-3"
        >
          <AlertCircle className="w-4 h-4 text-danger shrink-0" />
          <p className="text-[10px] font-bold text-danger leading-tight">
            {status === 'critical' ? 'Kritik sistem hatası! Aracı hemen güvenli bir yere çekin.' : 'Lastik basıncı düşük tespit edildi. En yakın istasyonda kontrol edin.'}
          </p>
        </motion.div>
      )}

      {/* Decorative Blur Circles */}
      <div className="absolute -top-12 -right-12 w-24 h-24 bg-accent/5 blur-[40px] rounded-full pointer-events-none" />
      <div className="absolute -bottom-12 -left-12 w-24 h-24 bg-secondary/5 blur-[40px] rounded-full pointer-events-none" />
    </motion.div>
  )
}
