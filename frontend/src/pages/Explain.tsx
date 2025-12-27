import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, Lightbulb, TrendingUp, AlertTriangle, CheckCircle, Info } from 'lucide-react'
import { explainRoute } from '../services/api'
import type { ExplainResponse } from '../services/api'

export default function Explain() {
    const { routeId } = useParams<{ routeId: string }>()
    const navigate = useNavigate()
    const [explanation, setExplanation] = useState<ExplainResponse | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (!routeId) return
        explainRoute(routeId)
            .then(setExplanation)
            .catch(console.error)
            .finally(() => setLoading(false))
    }, [routeId])

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="w-10 h-10 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
            </div>
        )
    }

    if (!explanation) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="glass rounded-2xl p-8 text-center">
                    <AlertTriangle className="w-12 h-12 text-yellow-400 mx-auto mb-4" />
                    <h2 className="text-xl font-bold mb-2">Explanation Not Found</h2>
                    <p className="text-gray-400 mb-4">Unable to load explanation for this route.</p>
                    <button
                        onClick={() => navigate(-1)}
                        className="px-4 py-2 rounded-lg bg-cyan-500/20 text-cyan-400"
                    >
                        Go Back
                    </button>
                </div>
            </div>
        )
    }

    const sensitivity = explanation.sensitivity || {
        fuel_weight_sensitivity: 0.3,
        time_weight_sensitivity: 0.25,
        risk_sensitivity: 0.2,
        comfort_importance: 0.1,
    }

    return (
        <div className="min-h-screen p-6">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center gap-4 mb-8"
                >
                    <button
                        onClick={() => navigate(-1)}
                        className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-all"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h1 className="text-3xl font-bold">Why This Route?</h1>
                        <p className="text-gray-400">Explainable AI Analysis</p>
                    </div>
                </motion.div>

                {/* Summary */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="glass rounded-2xl p-6 mb-6"
                >
                    <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-xl bg-cyan-500/20 flex items-center justify-center flex-shrink-0">
                            <Lightbulb className="w-6 h-6 text-cyan-400" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold mb-2">Summary</h3>
                            <p className="text-gray-300">{explanation.summary}</p>
                            <div className="mt-3 flex items-center gap-4 text-sm">
                                <span className="px-3 py-1 rounded-full bg-cyan-500/20 text-cyan-400">
                                    {explanation.primary_optimization}
                                </span>
                                <span className="text-gray-400">
                                    Confidence: {(explanation.confidence * 100).toFixed(0)}%
                                </span>
                            </div>
                        </div>
                    </div>
                </motion.div>

                {/* Key Decisions */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="glass rounded-2xl p-6 mb-6"
                >
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-green-400" />
                        Key Decisions
                    </h3>
                    <div className="space-y-4">
                        {explanation.key_decisions.length === 0 ? (
                            <p className="text-gray-400">No specific decisions recorded for this route.</p>
                        ) : (
                            explanation.key_decisions.map((decision, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: 0.1 * i }}
                                    className="p-4 rounded-xl bg-white/5 border border-white/10"
                                >
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="px-2 py-1 rounded text-xs font-medium bg-purple-500/20 text-purple-400">
                                            {decision.type.replace(/_/g, ' ').toUpperCase()}
                                        </span>
                                    </div>
                                    <p className="text-gray-300 mb-2">{decision.description}</p>
                                    <p className="text-sm text-gray-500 italic">{decision.trade_off}</p>
                                </motion.div>
                            ))
                        )}
                    </div>
                </motion.div>

                {/* Trade-offs */}
                {Object.keys(explanation.trade_offs).length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="glass rounded-2xl p-6 mb-6"
                    >
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <TrendingUp className="w-5 h-5 text-yellow-400" />
                            Trade-offs
                        </h3>
                        <div className="space-y-3">
                            {Object.entries(explanation.trade_offs).map(([key, value]) => (
                                <div key={key} className="p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/20">
                                    <div className="font-medium text-yellow-400 mb-1">
                                        {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                    </div>
                                    <p className="text-gray-300 text-sm">{value}</p>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                )}

                {/* Sensitivity */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="glass rounded-2xl p-6"
                >
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <Info className="w-5 h-5 text-blue-400" />
                        Sensitivity Analysis
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="p-4 rounded-xl bg-white/5 text-center">
                            <div className="text-2xl font-bold gradient-text">
                                {(sensitivity.fuel_weight_sensitivity * 100).toFixed(0)}%
                            </div>
                            <div className="text-sm text-gray-400">Fuel Weight</div>
                        </div>
                        <div className="p-4 rounded-xl bg-white/5 text-center">
                            <div className="text-2xl font-bold gradient-text">
                                {(sensitivity.time_weight_sensitivity * 100).toFixed(0)}%
                            </div>
                            <div className="text-sm text-gray-400">Time Weight</div>
                        </div>
                        <div className="p-4 rounded-xl bg-white/5 text-center">
                            <div className="text-2xl font-bold gradient-text">
                                {(sensitivity.risk_sensitivity * 100).toFixed(0)}%
                            </div>
                            <div className="text-sm text-gray-400">Risk Sensitivity</div>
                        </div>
                        <div className="p-4 rounded-xl bg-white/5 text-center">
                            <div className="text-2xl font-bold gradient-text">
                                {(sensitivity.comfort_importance * 100).toFixed(0)}%
                            </div>
                            <div className="text-sm text-gray-400">Comfort</div>
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    )
}
