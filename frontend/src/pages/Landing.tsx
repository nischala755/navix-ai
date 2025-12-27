import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Ship, Zap, Leaf, Shield, ArrowRight, Waves } from 'lucide-react'
import OceanScene from '../components/OceanScene'

const features = [
    {
        icon: Zap,
        title: 'HACOPSO Engine',
        description: 'Research-grade hybrid swarm optimization with chaotic inertia scheduling',
    },
    {
        icon: Leaf,
        title: 'Carbon Aware',
        description: 'IMO-compliant emission modeling with CII rating integration',
    },
    {
        icon: Shield,
        title: 'Risk Intelligence',
        description: 'Real-time storm tracking and piracy zone avoidance',
    },
]

export default function Landing() {
    return (
        <div className="min-h-screen relative overflow-hidden">
            {/* Ocean Background */}
            <OceanScene />

            {/* Content */}
            <div className="relative z-10">
                {/* Nav */}
                <nav className="flex items-center justify-between px-8 py-6">
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="flex items-center gap-3"
                    >
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500 to-teal-400 flex items-center justify-center">
                            <Ship className="w-5 h-5 text-white" />
                        </div>
                        <span className="text-xl font-bold gradient-text">NaviX-AI</span>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                    >
                        <Link
                            to="/optimize"
                            className="px-5 py-2.5 rounded-full bg-cyan-500/20 border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/30 transition-all"
                        >
                            Launch App
                        </Link>
                    </motion.div>
                </nav>

                {/* Hero */}
                <section className="px-8 pt-20 pb-32">
                    <div className="max-w-5xl mx-auto text-center">
                        <motion.div
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm mb-8"
                        >
                            <Waves className="w-4 h-4" />
                            <span>HACOPSO-Powered Maritime Intelligence</span>
                        </motion.div>

                        <motion.h1
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.3 }}
                            className="text-5xl md:text-7xl font-bold mb-6 leading-tight"
                        >
                            <span className="gradient-text">Carbon-Aware</span>
                            <br />
                            Maritime Routing
                        </motion.h1>

                        <motion.p
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.4 }}
                            className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto"
                        >
                            Multi-objective route optimization balancing fuel, time, safety, and emissions
                            using cutting-edge swarm intelligence
                        </motion.p>

                        <motion.div
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.5 }}
                            className="flex flex-col sm:flex-row gap-4 justify-center"
                        >
                            <Link
                                to="/optimize"
                                className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-teal-500 text-white font-semibold hover:shadow-lg hover:shadow-cyan-500/30 transition-all"
                            >
                                Start Optimizing
                                <ArrowRight className="w-5 h-5" />
                            </Link>
                            <Link
                                to="/dashboard"
                                className="inline-flex items-center gap-2 px-8 py-4 rounded-xl glass text-white font-semibold hover:bg-white/10 transition-all"
                            >
                                View Dashboard
                            </Link>
                        </motion.div>
                    </div>
                </section>

                {/* Features */}
                <section className="px-8 py-20">
                    <div className="max-w-6xl mx-auto grid md:grid-cols-3 gap-6">
                        {features.map((feature, i) => {
                            const Icon = feature.icon
                            return (
                                <motion.div
                                    key={feature.title}
                                    initial={{ opacity: 0, y: 30 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.6 + i * 0.1 }}
                                    className="glass p-6 rounded-2xl hover:border-cyan-500/40 transition-all group"
                                >
                                    <div className="w-12 h-12 rounded-xl bg-cyan-500/10 flex items-center justify-center mb-4 group-hover:bg-cyan-500/20 transition-all">
                                        <Icon className="w-6 h-6 text-cyan-400" />
                                    </div>
                                    <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                                    <p className="text-gray-400 text-sm">{feature.description}</p>
                                </motion.div>
                            )
                        })}
                    </div>
                </section>

                {/* Stats */}
                <section className="px-8 py-20">
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.9 }}
                        className="max-w-4xl mx-auto glass rounded-2xl p-8"
                    >
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
                            {[
                                { value: '5+', label: 'Objectives' },
                                { value: '15+', label: 'Major Ports' },
                                { value: '< 2s', label: 'Optimization' },
                                { value: '100%', label: 'Carbon Aware' },
                            ].map((stat) => (
                                <div key={stat.label}>
                                    <div className="text-3xl font-bold gradient-text">{stat.value}</div>
                                    <div className="text-sm text-gray-400 mt-1">{stat.label}</div>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                </section>
            </div>
        </div>
    )
}
