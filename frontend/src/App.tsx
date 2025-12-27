import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import Optimizer from './pages/Optimizer'
import LiveOptimization from './pages/LiveOptimization'
import ParetoExplorer from './pages/ParetoExplorer'
import Dashboard from './pages/Dashboard'
import Explain from './pages/Explain'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route element={<Layout />}>
        <Route path="/optimize" element={<Optimizer />} />
        <Route path="/job/:jobId" element={<LiveOptimization />} />
        <Route path="/routes/:jobId" element={<ParetoExplorer />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/explain/:routeId" element={<Explain />} />
      </Route>
    </Routes>
  )
}

export default App
