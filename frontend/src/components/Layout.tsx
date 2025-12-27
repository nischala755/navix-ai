import { Outlet, Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Ship, BarChart3, Settings, Home, Compass } from 'lucide-react'

const navItems = [
    { path: '/', icon: Home, label: 'Home' },
    { path: '/optimize', icon: Compass, label: 'Optimizer' },
    { path: '/dashboard', icon: BarChart3, label: 'Dashboard' },
]

export default function Layout() {
    const location = useLocation()

    return (
        <div className="min-h-screen flex">
            {/* Sidebar */}
            <motion.aside
                initial={{ x: -80 }}
                animate={{ x: 0 }}
                className="w-20 fixed left-0 top-0 h-screen glass-dark flex flex-col items-center py-6 z-50"
            >
                <Link to="/" className="mb-8">
                    <motion.div
                        whileHover={{ scale: 1.1 }}
                        className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-teal-400 flex items-center justify-center"
                    >
                        <Ship className="w-6 h-6 text-white" />
                    </motion.div>
                </Link>

                <nav className="flex-1 flex flex-col gap-4">
                    {navItems.map((item) => {
                        const Icon = item.icon
                        const isActive = location.pathname === item.path
                        return (
                            <Link key={item.path} to={item.path}>
                                <motion.div
                                    whileHover={{ scale: 1.1 }}
                                    whileTap={{ scale: 0.95 }}
                                    className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-300 ${isActive
                                        ? 'bg-cyan-500/20 text-cyan-400 glow-cyan'
                                        : 'text-gray-400 hover:text-cyan-400 hover:bg-white/5'
                                        }`}
                                >
                                    <Icon className="w-5 h-5" />
                                </motion.div>
                            </Link>
                        )
                    })}
                </nav>

                <motion.button
                    whileHover={{ scale: 1.1 }}
                    className="w-12 h-12 rounded-xl flex items-center justify-center text-gray-400 hover:text-cyan-400 hover:bg-white/5 transition-all"
                >
                    <Settings className="w-5 h-5" />
                </motion.button>
            </motion.aside>

            {/* Main Content */}
            <main className="flex-1 ml-20">
                <Outlet />
            </main>
        </div>
    )
}
