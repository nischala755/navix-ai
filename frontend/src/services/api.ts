import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Types
export interface ObjectiveWeights {
    fuel: number;
    time: number;
    risk: number;
    emissions: number;
    comfort: number;
}

export interface OptimizationRequest {
    origin_locode: string;
    destination_locode: string;
    ship_id: string;
    algorithm?: 'hacopso' | 'ga' | 'pso';
    weights?: ObjectiveWeights;
    swarm_size?: number;
    max_iterations?: number;
}

export interface JobStatus {
    job_id: string;
    status: string;
    algorithm: string;
    origin: string;
    destination: string;
    created_at: string;
    started_at?: string;
    completed_at?: string;
    iterations_completed: number;
    solutions_count: number;
    error_message?: string;
    progress_pct: number;
}

export interface RouteWaypoint {
    sequence: number;
    latitude: number;
    longitude: number;
    eta?: string;
    leg_distance_nm?: number;
    leg_speed_kt?: number;
    leg_fuel_tonnes?: number;
}

export interface ObjectiveValues {
    fuel_tonnes: number;
    travel_time_hours: number;
    risk_score: number;
    co2_emissions_tonnes: number;
    comfort_score: number;
}

export interface RouteSolution {
    route_id: string;
    job_id: string;
    rank: number;
    objectives: ObjectiveValues;
    total_distance_nm: number;
    waypoint_count: number;
    average_speed_kt?: number;
    waypoints: RouteWaypoint[];
    geojson?: any;
}

export interface ExplainResponse {
    route_id: string;
    summary: string;
    primary_optimization: string;
    key_decisions: Array<{
        type: string;
        description: string;
        impact: any;
        trade_off: string;
    }>;
    trade_offs: Record<string, string>;
    confidence: number;
    sensitivity: {
        fuel_weight_sensitivity: number;
        time_weight_sensitivity: number;
        risk_sensitivity: number;
        comfort_importance: number;
    };
}

export interface MapLayer {
    name: string;
    description: string;
    type: string;
}

// API Functions
export const optimizeRoute = async (request: OptimizationRequest) => {
    const response = await api.post('/optimize', request);
    return response.data;
};

export const getJobStatus = async (jobId: string): Promise<JobStatus> => {
    const response = await api.get(`/jobs/${jobId}`);
    return response.data;
};

export const getRoutes = async (jobId: string): Promise<{ routes: RouteSolution[] }> => {
    const response = await api.get(`/routes/${jobId}`);
    return response.data;
};

export const explainRoute = async (routeId: string): Promise<ExplainResponse> => {
    const response = await api.get(`/explain/${routeId}`);
    return response.data;
};

export const getMapLayers = async (): Promise<{ layers: MapLayer[] }> => {
    const response = await api.get('/map/layers');
    return response.data;
};

export const getLayerData = async (layerName: string) => {
    const response = await api.get(`/map/layer/${layerName}`);
    return response.data;
};

export const getHealth = async () => {
    const response = await api.get('/health');
    return response.data;
};

export default api;
