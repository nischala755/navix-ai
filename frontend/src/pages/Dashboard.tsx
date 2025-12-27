import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts'
import { Ship, Fuel, Leaf, Activity, TrendingDown, AlertTriangle, Shield } from 'lucide-react'
import { getHealth, getLayerData } from '../services/api'

const COLORS = ['#00d4ff', '#00ffc8', '#ffd700', '#ff6b6b', '#a855f7']

export default function Dashboard() {
    const [health, setHealth] = useState<any>(null)
    const [storms, setStorms] = useState<any[]>([])
    const [piracy, setPiracy] = useState<any[]>([])

    useEffect(() => {
        getHealth().then(setHealth).catch(console.error)
        getLayerData('storm').then((d) => setStorms(d.zones || [])).catch(console.error)
        getLayerData('piracy').then((d) => setPiracy(d.zones || [])).catch(console.error)
    }, [])

    const fleetData = [
        { name: 'Container', active: 12, idle: 3, maintenance: 2 },
        { name: 'Tanker', active: 8, idle: 2, maintenance: 1 },
        { name: 'Bulk', active: 15, idle: 5, maintenance: 3 },
    ]

    const emissionsData = [
        { month: 'Jan', co2: 4500, target: 5000 },
        { month: 'Feb', co2: 4200, target: 4800 },
        { month: 'Mar', co2: 4000, target: 4600 },
        { month: 'Apr', co2: 3800, target: 4400 },
        { month: 'May', co2: 3500, target: 4200 },
        { month: 'Jun', co2: 3200, target: 4000 },
    ]

    const fuelSavings = [
        { name: 'HACOPSO', value: 35 },
        { name: 'Traditional', value: 65 },
    ]

    return (
        <div className="min-h-screen p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-8"
                >
                    <h1 className="text-3xl font-bold mb-2">Fleet Dashboard</h1>
                    <p className="text-gray-400">Carbon & Risk Intelligence Overview</p>
                </motion.div>

                {/* Stats */}
                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    {[
                        { icon: Ship, label: 'Active Vessels', value: '35', change: '+2', color: 'text-cyan-400' },
                        { icon: Fuel, label: 'Fuel Saved', value: '1,240t', change: '-15%', color: 'text-green-400' },
                        { icon: Leaf, label: 'CO₂ Reduced', value: '3,892t', change: '-22%', color: 'text-teal-400' },
                        { icon: AlertTriangle, label: 'Active Alerts', value: storms.length + piracy.length, change: '', color: 'text-yellow-400' },
                    ].map((stat, i) => (
                        <motion.div
                            key={stat.label}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 }}
                            className="glass rounded-2xl p-5"
                        >
                            <div className="flex items-center gap-3 mb-3">
                                <div className={`w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center ${stat.color}`}>
                                    <stat.icon className="w-5 h-5" />
                                </div>
                                {stat.change && (
                                    <span className="text-xs text-green-400 bg-green-400/10 px-2 py-1 rounded-full">
                                        {stat.change}
                                    </span>
                                )}
                            </div>
                            <div className="text-2xl font-bold">{stat.value}</div>
                            <div className="text-sm text-gray-400">{stat.label}</div>
                        </motion.div>
                    ))}
                </div>

                <div className="grid lg:grid-cols-2 gap-6 mb-8">
                    {/* Emissions Trend */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="glass rounded-2xl p-6"
                    >
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <TrendingDown className="w-5 h-5 text-green-400" />
                            CO₂ Emissions Trend
                        </h3>
                        <ResponsiveContainer width="100%" height={250}>
                            <LineChart data={emissionsData}>
                                <XAxis dataKey="month" tick={{ fill: '#9ca3af' }} axisLine={{ stroke: '#374151' }} />
                                <YAxis tick={{ fill: '#9ca3af' }} axisLine={{ stroke: '#374151' }} />
                                <Tooltip
                                    contentStyle={{ background: 'rgba(13, 31, 60, 0.9)', border: 'none', borderRadius: '8px' }}
                                />
                                <Line type="monotone" dataKey="co2" stroke="#00ffc8" strokeWidth={3} dot={false} />
                                <Line type="monotone" dataKey="target" stroke="#ff6b6b" strokeWidth={2} strokeDasharray="5 5" dot={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    </motion.div>

                    {/* Fleet Status */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="glass rounded-2xl p-6"
                    >
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Activity className="w-5 h-5 text-cyan-400" />
                            Fleet Status
                        </h3>
                        <ResponsiveContainer width="100%" height={250}>
                            <BarChart data={fleetData} layout="vertical">
                                <XAxis type="number" tick={{ fill: '#9ca3af' }} axisLine={{ stroke: '#374151' }} />
                                <YAxis dataKey="name" type="category" tick={{ fill: '#9ca3af' }} axisLine={{ stroke: '#374151' }} />
                                <Tooltip
                                    contentStyle={{ background: 'rgba(13, 31, 60, 0.9)', border: 'none', borderRadius: '8px' }}
                                />
                                <Bar dataKey="active" stackId="a" fill="#00d4ff" radius={[0, 0, 0, 0]} />
                                <Bar dataKey="idle" stackId="a" fill="#ffd700" radius={[0, 0, 0, 0]} />
                                <Bar dataKey="maintenance" stackId="a" fill="#ff6b6b" radius={[0, 4, 4, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </motion.div>
                </div>

                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Fuel Savings */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="glass rounded-2xl p-6"
                    >
                        <h3 className="text-lg font-semibold mb-4">HACOPSO Savings</h3>
                        <ResponsiveContainer width="100%" height={200}>
                            <PieChart>
                                <Pie
                                    data={fuelSavings}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={80}
                                    dataKey="value"
                                >
                                    {fuelSavings.map((_, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index]} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ background: 'rgba(13, 31, 60, 0.9)', border: 'none', borderRadius: '8px' }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                        <div className="text-center">
                            <div className="text-3xl font-bold gradient-text">35%</div>
                            <div className="text-sm text-gray-400">Fuel savings with HACOPSO</div>
                        </div>
                    </motion.div>

                    {/* Active Storms */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="glass rounded-2xl p-6"
                    >
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <AlertTriangle className="w-5 h-5 text-yellow-400" />
                            Active Storms
                        </h3>
                        <div className="space-y-3">
                            {storms.length === 0 ? (
                                <p className="text-gray-400 text-sm">No active storms</p>
                            ) : (
                                storms.map((storm, i) => (
                                    <div key={i} className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                                        <div className="font-medium">{storm.name}</div>
                                        <div className="text-sm text-gray-400">
                                            Risk: {(storm.risk_level * 100).toFixed(0)}% | Cat {storm.category || 'N/A'}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </motion.div>

                    {/* Piracy Zones */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="glass rounded-2xl p-6"
                    >
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Shield className="w-5 h-5 text-red-400" />
                            Piracy Zones
                        </h3>
                        <div className="space-y-3">
                            {piracy.length === 0 ? (
                                <p className="text-gray-400 text-sm">No piracy zones</p>
                            ) : (
                                piracy.map((zone, i) => (
                                    <div key={i} className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                                        <div className="font-medium">{zone.name}</div>
                                        <div className="text-sm text-gray-400">
                                            Risk: {(zone.risk_level * 100).toFixed(0)}%
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </motion.div>
                </div>

                {/* API Status */}
                {health && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="mt-8 text-center text-sm text-gray-500"
                    >
                        API Status: <span className="text-green-400">{health.status}</span> | Version: {health.version}
                    </motion.div>
                )}
            </div>
        </div>
    )
}
