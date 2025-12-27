import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Ship, Fuel, Clock, Leaf, Shield, Eye, ArrowLeft } from 'lucide-react'
import { getRoutes } from '../services/api'
import type { RouteSolution } from '../services/api'
import MapView from '../components/MapView'

const COLORS = ['#00d4ff', '#00ffc8', '#ffd700', '#ff6b6b', '#a855f7']

interface ParetoDataPoint {
    fuel: number
    time: number
    risk: number
    emissions: number
    id: string
    rank: number
    color: string
}

export default function ParetoExplorer() {
    const { jobId } = useParams<{ jobId: string }>()
    const navigate = useNavigate()
    const [routes, setRoutes] = useState<RouteSolution[]>([])
    const [selected, setSelected] = useState<RouteSolution | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (!jobId) return
        getRoutes(jobId)
            .then((data) => {
                setRoutes(data.routes)
                if (data.routes.length > 0) setSelected(data.routes[0])
            })
            .finally(() => setLoading(false))
    }, [jobId])

    const paretoData: ParetoDataPoint[] = routes.map((r, i) => ({
        fuel: r.objectives.fuel_tonnes,
        time: r.objectives.travel_time_hours,
        risk: r.objectives.risk_score * 100,
        emissions: r.objectives.co2_emissions_tonnes,
        id: r.route_id,
        rank: r.rank,
        color: COLORS[i % COLORS.length],
    }))

    const routeCoords = selected?.waypoints.map((w) => [w.longitude, w.latitude]) || []

    const handleScatterClick = (data: ParetoDataPoint) => {
        const route = routes.find((r) => r.route_id === data.id)
        if (route) setSelected(route)
    }

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="w-10 h-10 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
            </div>
        )
    }

    return (
        <div className="min-h-screen p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center gap-4 mb-8"
                >
                    <button
                        onClick={() => navigate('/optimize')}
                        className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-all"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h1 className="text-3xl font-bold">Pareto Front Explorer</h1>
                        <p className="text-gray-400">{routes.length} optimal routes found</p>
                    </div>
                </motion.div>

                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Pareto Chart */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="lg:col-span-2 glass rounded-2xl p-6"
                    >
                        <h3 className="text-lg font-semibold mb-4">Fuel vs Time Trade-off</h3>
                        <ResponsiveContainer width="100%" height={400}>
                            <ScatterChart margin={{ top: 20, right: 20, bottom: 40, left: 40 }}>
                                <XAxis
                                    dataKey="fuel"
                                    name="Fuel"
                                    type="number"
                                    tick={{ fill: '#9ca3af' }}
                                    axisLine={{ stroke: '#374151' }}
                                    label={{ value: 'Fuel (tonnes)', position: 'bottom', fill: '#9ca3af' }}
                                />
                                <YAxis
                                    dataKey="time"
                                    name="Time"
                                    type="number"
                                    tick={{ fill: '#9ca3af' }}
                                    axisLine={{ stroke: '#374151' }}
                                    label={{ value: 'Time (hours)', angle: -90, position: 'left', fill: '#9ca3af' }}
                                />
                                <Tooltip
                                    content={({ payload }) => {
                                        if (!payload || !payload[0]) return null
                                        const data = payload[0].payload as ParetoDataPoint
                                        return (
                                            <div className="glass p-3 rounded-lg text-sm">
                                                <p className="font-semibold mb-1">Route #{data.rank + 1}</p>
                                                <p>Fuel: {data.fuel.toFixed(1)} tonnes</p>
                                                <p>Time: {data.time.toFixed(1)} hours</p>
                                                <p>Risk: {data.risk.toFixed(1)}%</p>
                                            </div>
                                        )
                                    }}
                                />
                                <Scatter
                                    data={paretoData}
                                    onClick={(e) => e && handleScatterClick(e as unknown as ParetoDataPoint)}
                                >
                                    {paretoData.map((entry, index) => (
                                        <Cell
                                            key={`cell-${index}`}
                                            fill={entry.id === selected?.route_id ? '#00ffc8' : '#00d4ff'}
                                            stroke={entry.id === selected?.route_id ? '#fff' : 'transparent'}
                                            strokeWidth={2}
                                            style={{ cursor: 'pointer' }}
                                        />
                                    ))}
                                </Scatter>
                            </ScatterChart>
                        </ResponsiveContainer>
                    </motion.div>

                    {/* Route List */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="glass rounded-2xl p-6 max-h-[500px] overflow-y-auto"
                    >
                        <h3 className="text-lg font-semibold mb-4">Routes</h3>
                        <div className="space-y-3">
                            {routes.map((route, i) => (
                                <motion.button
                                    key={route.route_id}
                                    whileHover={{ scale: 1.02 }}
                                    onClick={() => setSelected(route)}
                                    className={`w-full p-4 rounded-xl text-left transition-all ${selected?.route_id === route.route_id
                                        ? 'bg-cyan-500/20 border border-cyan-500/40'
                                        : 'bg-white/5 hover:bg-white/10 border border-transparent'
                                        }`}
                                >
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="font-semibold">Route #{i + 1}</span>
                                        <span
                                            className="w-3 h-3 rounded-full"
                                            style={{ background: COLORS[i % COLORS.length] }}
                                        />
                                    </div>
                                    <div className="grid grid-cols-2 gap-2 text-sm text-gray-400">
                                        <div className="flex items-center gap-1">
                                            <Fuel className="w-3 h-3" />
                                            {route.objectives.fuel_tonnes.toFixed(0)}t
                                        </div>
                                        <div className="flex items-center gap-1">
                                            <Clock className="w-3 h-3" />
                                            {route.objectives.travel_time_hours.toFixed(0)}h
                                        </div>
                                        <div className="flex items-center gap-1">
                                            <Leaf className="w-3 h-3" />
                                            {route.objectives.co2_emissions_tonnes.toFixed(0)}t CO₂
                                        </div>
                                        <div className="flex items-center gap-1">
                                            <Shield className="w-3 h-3" />
                                            {(route.objectives.risk_score * 100).toFixed(0)}%
                                        </div>
                                    </div>
                                </motion.button>
                            ))}
                        </div>
                    </motion.div>
                </div>

                {/* Selected Route Details */}
                {selected && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mt-6 grid lg:grid-cols-2 gap-6"
                    >
                        {/* Map */}
                        <div className="glass rounded-2xl overflow-hidden h-[400px]">
                            <MapView
                                origin={{ locode: '', name: 'Origin', lat: selected.waypoints[0]?.latitude || 0, lng: selected.waypoints[0]?.longitude || 0 }}
                                destination={{ locode: '', name: 'Destination', lat: selected.waypoints[selected.waypoints.length - 1]?.latitude || 0, lng: selected.waypoints[selected.waypoints.length - 1]?.longitude || 0 }}
                                ports={[]}
                                route={routeCoords}
                            />
                        </div>

                        {/* Stats */}
                        <div className="glass rounded-2xl p-6">
                            <div className="flex items-center justify-between mb-6">
                                <h3 className="text-lg font-semibold">Route Details</h3>
                                <button
                                    onClick={() => navigate(`/explain/${selected.route_id}`)}
                                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30 transition-all"
                                >
                                    <Eye className="w-4 h-4" />
                                    Why this route?
                                </button>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-4 rounded-xl bg-white/5">
                                    <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                                        <Ship className="w-4 h-4" />
                                        Distance
                                    </div>
                                    <div className="text-xl font-semibold">{selected.total_distance_nm.toFixed(0)} nm</div>
                                </div>
                                <div className="p-4 rounded-xl bg-white/5">
                                    <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                                        <Fuel className="w-4 h-4" />
                                        Fuel
                                    </div>
                                    <div className="text-xl font-semibold">{selected.objectives.fuel_tonnes.toFixed(1)} tonnes</div>
                                </div>
                                <div className="p-4 rounded-xl bg-white/5">
                                    <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                                        <Clock className="w-4 h-4" />
                                        Time
                                    </div>
                                    <div className="text-xl font-semibold">{selected.objectives.travel_time_hours.toFixed(1)} hours</div>
                                </div>
                                <div className="p-4 rounded-xl bg-white/5">
                                    <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                                        <Leaf className="w-4 h-4" />
                                        CO₂
                                    </div>
                                    <div className="text-xl font-semibold">{selected.objectives.co2_emissions_tonnes.toFixed(1)} tonnes</div>
                                </div>
                                <div className="p-4 rounded-xl bg-white/5">
                                    <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                                        <Shield className="w-4 h-4" />
                                        Risk
                                    </div>
                                    <div className="text-xl font-semibold">{(selected.objectives.risk_score * 100).toFixed(1)}%</div>
                                </div>
                                <div className="p-4 rounded-xl bg-white/5">
                                    <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                                        <Ship className="w-4 h-4" />
                                        Waypoints
                                    </div>
                                    <div className="text-xl font-semibold">{selected.waypoint_count}</div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </div>
        </div>
    )
}
