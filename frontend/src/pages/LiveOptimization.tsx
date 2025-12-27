import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { CheckCircle, XCircle, Loader2, ArrowRight, Zap } from 'lucide-react'
import { getJobStatus } from '../services/api'
import type { JobStatus } from '../services/api'

export default function LiveOptimization() {
    const { jobId } = useParams<{ jobId: string }>()
    const navigate = useNavigate()
    const [job, setJob] = useState<JobStatus | null>(null)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (!jobId) return

        const poll = async () => {
            try {
                const status = await getJobStatus(jobId)
                setJob(status)

                if (status.status === 'completed') {
                    setTimeout(() => navigate(`/routes/${jobId}`), 1500)
                } else if (status.status === 'failed') {
                    setError(status.error_message || 'Optimization failed')
                } else if (!['completed', 'failed', 'cancelled'].includes(status.status)) {
                    setTimeout(poll, 1000)
                }
            } catch (err) {
                setError('Failed to fetch job status')
            }
        }

        poll()
    }, [jobId, navigate])

    const getStatusIcon = () => {
        if (!job) return <Loader2 className="w-12 h-12 text-cyan-400 animate-spin" />
        switch (job.status) {
            case 'completed':
                return <CheckCircle className="w-12 h-12 text-green-400" />
            case 'failed':
            case 'cancelled':
                return <XCircle className="w-12 h-12 text-red-400" />
            default:
                return <Loader2 className="w-12 h-12 text-cyan-400 animate-spin" />
        }
    }

    const getStatusText = () => {
        if (!job) return 'Initializing...'
        switch (job.status) {
            case 'pending':
                return 'Queued for optimization...'
            case 'running':
                return 'HACOPSO optimization in progress...'
            case 'completed':
                return 'Optimization complete!'
            case 'failed':
                return 'Optimization failed'
            case 'cancelled':
                return 'Optimization cancelled'
            default:
                return job.status
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center p-6">
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass rounded-3xl p-12 max-w-lg w-full text-center"
            >
                <motion.div
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-white/5 mb-8"
                >
                    {getStatusIcon()}
                </motion.div>

                <h2 className="text-2xl font-bold mb-2">{getStatusText()}</h2>

                {job && (
                    <p className="text-gray-400 mb-8">
                        Algorithm: <span className="text-cyan-400">{job.algorithm.toUpperCase()}</span>
                    </p>
                )}

                {job && job.status === 'running' && (
                    <div className="mb-8">
                        <div className="flex justify-between text-sm mb-2">
                            <span>Progress</span>
                            <span className="text-cyan-400">{job.progress_pct.toFixed(0)}%</span>
                        </div>
                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${job.progress_pct}%` }}
                                transition={{ duration: 0.5 }}
                                className="h-full bg-gradient-to-r from-cyan-500 to-teal-500"
                            />
                        </div>
                        <p className="text-sm text-gray-500 mt-2">
                            Iteration {job.iterations_completed}
                        </p>
                    </div>
                )}

                {error && (
                    <div className="p-4 rounded-lg bg-red-500/20 border border-red-500/30 text-red-400 mb-6">
                        {error}
                    </div>
                )}

                {job?.status === 'completed' && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-4"
                    >
                        <div className="flex items-center justify-center gap-4 text-sm">
                            <div className="flex items-center gap-2">
                                <Zap className="w-4 h-4 text-cyan-400" />
                                <span>{job.solutions_count} Pareto solutions</span>
                            </div>
                        </div>

                        <button
                            onClick={() => navigate(`/routes/${jobId}`)}
                            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-teal-500 text-white font-semibold"
                        >
                            View Routes
                            <ArrowRight className="w-4 h-4" />
                        </button>
                    </motion.div>
                )}
            </motion.div>
        </div>
    )
}
