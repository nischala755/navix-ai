import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Anchor, Play, Settings2, Fuel, Clock, Shield, Leaf, Compass } from 'lucide-react'
import { optimizeRoute } from '../services/api'
import type { ObjectiveWeights } from '../services/api'
import MapView from '../components/MapView'

const PORTS = [
    { locode: 'SGSIN', name: 'Singapore', lat: 1.29, lng: 103.85 },
    { locode: 'NLRTM', name: 'Rotterdam', lat: 51.95, lng: 4.48 },
    { locode: 'CNSHA', name: 'Shanghai', lat: 31.23, lng: 121.47 },
    { locode: 'HKHKG', name: 'Hong Kong', lat: 22.32, lng: 114.17 },
    { locode: 'AEJEA', name: 'Jebel Ali', lat: 25.02, lng: 55.06 },
    { locode: 'DEHAM', name: 'Hamburg', lat: 53.55, lng: 9.99 },
    { locode: 'USNYC', name: 'New York', lat: 40.71, lng: -74.01 },
    { locode: 'USLAX', name: 'Los Angeles', lat: 33.74, lng: -118.26 },
    { locode: 'JPYOK', name: 'Yokohama', lat: 35.44, lng: 139.64 },
]

const SHIPS = [
    { id: 'container_large', name: 'Large Container Ship', type: 'Container' },
    { id: 'tanker_vlcc', name: 'VLCC Tanker', type: 'Tanker' },
    { id: 'bulk_capesize', name: 'Capesize Bulk Carrier', type: 'Bulk' },
]

interface WeightSliderProps {
    icon: any
    label: string
    value: number
    onChange: (value: number) => void
    color: string
}

function WeightSlider({ icon: Icon, label, value, onChange, color }: WeightSliderProps) {
    return (
        <div className="flex items-center gap-4">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
                <Icon className="w-5 h-5" />
            </div>
            <div className="flex-1">
                <div className="flex justify-between text-sm mb-1">
                    <span>{label}</span>
                    <span className="text-cyan-400">{(value * 100).toFixed(0)}%</span>
                </div>
                <input
                    type="range"
                    min="0"
                    max="100"
                    value={value * 100}
                    onChange={(e) => onChange(Number(e.target.value) / 100)}
                    className="w-full"
                />
            </div>
        </div>
    )
}

export default function Optimizer() {
    const navigate = useNavigate()
    const [origin, setOrigin] = useState(PORTS[0])
    const [destination, setDestination] = useState(PORTS[1])
    const [ship, setShip] = useState(SHIPS[0])
    const [algorithm, setAlgorithm] = useState<'hacopso' | 'ga'>('hacopso')
    const [loading, setLoading] = useState(false)
    const [weights, setWeights] = useState<ObjectiveWeights>({
        fuel: 0.3,
        time: 0.25,
        risk: 0.2,
        emissions: 0.15,
        comfort: 0.1,
    })

    const updateWeight = (key: keyof ObjectiveWeights, value: number) => {
        setWeights((prev) => ({ ...prev, [key]: value }))
    }

    const handleOptimize = async () => {
        setLoading(true)
        try {
            const response = await optimizeRoute({
                origin_locode: origin.locode,
                destination_locode: destination.locode,
                ship_id: ship.id,
                algorithm,
                weights,
            })
            navigate(`/job/${response.job_id}`)
        } catch (error) {
            console.error('Optimization failed:', error)
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-8"
                >
                    <h1 className="text-3xl font-bold mb-2">Route Optimizer</h1>
                    <p className="text-gray-400">Configure your voyage parameters and optimize</p>
                </motion.div>

                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Map */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="lg:col-span-2 glass rounded-2xl overflow-hidden h-[600px]"
                    >
                        <MapView
                            origin={origin}
                            destination={destination}
                            ports={PORTS}
                            onSelectOrigin={(p) => setOrigin(p)}
                            onSelectDestination={(p) => setDestination(p)}
                        />
                    </motion.div>

                    {/* Controls */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="space-y-6"
                    >
                        {/* Ports */}
                        <div className="glass rounded-2xl p-6">
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <Anchor className="w-5 h-5 text-cyan-400" />
                                Voyage
                            </h3>

                            <div className="space-y-4">
                                <div>
                                    <label className="text-sm text-gray-400 mb-1 block">Origin Port</label>
                                    <select
                                        value={origin.locode}
                                        onChange={(e) => setOrigin(PORTS.find((p) => p.locode === e.target.value)!)}
                                        className="w-full bg-white/5 rounded-lg px-4 py-3 border border-white/10 focus:border-cyan-500 focus:outline-none"
                                    >
                                        {PORTS.map((p) => (
                                            <option key={p.locode} value={p.locode} className="bg-gray-900">
                                                {p.name} ({p.locode})
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div>
                                    <label className="text-sm text-gray-400 mb-1 block">Destination Port</label>
                                    <select
                                        value={destination.locode}
                                        onChange={(e) => setDestination(PORTS.find((p) => p.locode === e.target.value)!)}
                                        className="w-full bg-white/5 rounded-lg px-4 py-3 border border-white/10 focus:border-cyan-500 focus:outline-none"
                                    >
                                        {PORTS.map((p) => (
                                            <option key={p.locode} value={p.locode} className="bg-gray-900">
                                                {p.name} ({p.locode})
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div>
                                    <label className="text-sm text-gray-400 mb-1 block">Vessel</label>
                                    <select
                                        value={ship.id}
                                        onChange={(e) => setShip(SHIPS.find((s) => s.id === e.target.value)!)}
                                        className="w-full bg-white/5 rounded-lg px-4 py-3 border border-white/10 focus:border-cyan-500 focus:outline-none"
                                    >
                                        {SHIPS.map((s) => (
                                            <option key={s.id} value={s.id} className="bg-gray-900">
                                                {s.name}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                        </div>

                        {/* Weights */}
                        <div className="glass rounded-2xl p-6">
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <Settings2 className="w-5 h-5 text-cyan-400" />
                                Objective Weights
                            </h3>

                            <div className="space-y-4">
                                <WeightSlider
                                    icon={Fuel}
                                    label="Fuel Efficiency"
                                    value={weights.fuel}
                                    onChange={(v) => updateWeight('fuel', v)}
                                    color="bg-orange-500/20 text-orange-400"
                                />
                                <WeightSlider
                                    icon={Clock}
                                    label="Travel Time"
                                    value={weights.time}
                                    onChange={(v) => updateWeight('time', v)}
                                    color="bg-blue-500/20 text-blue-400"
                                />
                                <WeightSlider
                                    icon={Shield}
                                    label="Safety"
                                    value={weights.risk}
                                    onChange={(v) => updateWeight('risk', v)}
                                    color="bg-red-500/20 text-red-400"
                                />
                                <WeightSlider
                                    icon={Leaf}
                                    label="Emissions"
                                    value={weights.emissions}
                                    onChange={(v) => updateWeight('emissions', v)}
                                    color="bg-green-500/20 text-green-400"
                                />
                                <WeightSlider
                                    icon={Compass}
                                    label="Comfort"
                                    value={weights.comfort}
                                    onChange={(v) => updateWeight('comfort', v)}
                                    color="bg-purple-500/20 text-purple-400"
                                />
                            </div>
                        </div>

                        {/* Algorithm */}
                        <div className="glass rounded-2xl p-6">
                            <h3 className="text-lg font-semibold mb-4">Algorithm</h3>
                            <div className="flex gap-2">
                                {(['hacopso', 'ga'] as const).map((alg) => (
                                    <button
                                        key={alg}
                                        onClick={() => setAlgorithm(alg)}
                                        className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${algorithm === alg
                                            ? 'bg-cyan-500 text-white'
                                            : 'bg-white/5 text-gray-400 hover:bg-white/10'
                                            }`}
                                    >
                                        {alg.toUpperCase()}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Submit */}
                        <motion.button
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={handleOptimize}
                            disabled={loading}
                            className="w-full py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-teal-500 text-white font-semibold flex items-center justify-center gap-2 hover:shadow-lg hover:shadow-cyan-500/30 transition-all disabled:opacity-50"
                        >
                            {loading ? (
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <>
                                    <Play className="w-5 h-5" />
                                    Start Optimization
                                </>
                            )}
                        </motion.button>
                    </motion.div>
                </div>
            </div>
        </div>
    )
}
