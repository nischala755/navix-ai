import { useEffect, useRef, useState } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'

// Use a public token or environment variable
mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN || 'pk.eyJ1IjoibmF2aXgtYWkiLCJhIjoiY2x4ZGVtbzAwMDAwMDJ4bXhwdGRjMGFmMiJ9.demo'

interface Port {
    locode: string
    name: string
    lat: number
    lng: number
}

interface MapViewProps {
    origin: Port
    destination: Port
    ports: Port[]
    route?: number[][]
    onSelectOrigin?: (port: Port) => void
    onSelectDestination?: (port: Port) => void
}

export default function MapView({ origin, destination, ports, route }: MapViewProps) {
    const mapContainer = useRef<HTMLDivElement>(null)
    const map = useRef<mapboxgl.Map | null>(null)
    const [mapLoaded, setMapLoaded] = useState(false)

    useEffect(() => {
        if (!mapContainer.current) return

        map.current = new mapboxgl.Map({
            container: mapContainer.current,
            style: 'mapbox://styles/mapbox/dark-v11',
            center: [60, 20],
            zoom: 2,
            projection: { name: 'mercator' },
        })

        map.current.on('load', () => {
            setMapLoaded(true)
        })

        return () => {
            map.current?.remove()
        }
    }, [])

    // Add port markers
    useEffect(() => {
        if (!map.current || !mapLoaded) return

        // Clear existing markers
        const existingMarkers = document.querySelectorAll('.port-marker')
        existingMarkers.forEach((m) => m.remove())

        // Add origin marker
        const originEl = document.createElement('div')
        originEl.className = 'port-marker'
        originEl.style.cssText = `
      width: 20px;
      height: 20px;
      background: #00ffc8;
      border-radius: 50%;
      border: 3px solid white;
      box-shadow: 0 0 20px rgba(0, 255, 200, 0.5);
    `
        new mapboxgl.Marker(originEl)
            .setLngLat([origin.lng, origin.lat])
            .setPopup(new mapboxgl.Popup().setHTML(`<strong>${origin.name}</strong><br/>Origin`))
            .addTo(map.current)

        // Add destination marker
        const destEl = document.createElement('div')
        destEl.className = 'port-marker'
        destEl.style.cssText = `
      width: 20px;
      height: 20px;
      background: #ff6b6b;
      border-radius: 50%;
      border: 3px solid white;
      box-shadow: 0 0 20px rgba(255, 107, 107, 0.5);
    `
        new mapboxgl.Marker(destEl)
            .setLngLat([destination.lng, destination.lat])
            .setPopup(new mapboxgl.Popup().setHTML(`<strong>${destination.name}</strong><br/>Destination`))
            .addTo(map.current)

        // Add other ports
        ports.forEach((port) => {
            if (port.locode === origin.locode || port.locode === destination.locode) return
            const el = document.createElement('div')
            el.className = 'port-marker'
            el.style.cssText = `
        width: 12px;
        height: 12px;
        background: #00d4ff;
        border-radius: 50%;
        border: 2px solid white;
        opacity: 0.7;
      `
            new mapboxgl.Marker(el)
                .setLngLat([port.lng, port.lat])
                .setPopup(new mapboxgl.Popup().setHTML(`<strong>${port.name}</strong>`))
                .addTo(map.current!)
        })

        // Fit bounds
        const bounds = new mapboxgl.LngLatBounds()
        bounds.extend([origin.lng, origin.lat])
        bounds.extend([destination.lng, destination.lat])
        map.current.fitBounds(bounds, { padding: 100, duration: 1000 })
    }, [origin, destination, ports, mapLoaded])

    // Draw route
    useEffect(() => {
        if (!map.current || !mapLoaded || !route) return

        const sourceId = 'route'

        // Remove existing
        if (map.current.getLayer('route-line')) {
            map.current.removeLayer('route-line')
        }
        if (map.current.getSource(sourceId)) {
            map.current.removeSource(sourceId)
        }

        // Add route
        map.current.addSource(sourceId, {
            type: 'geojson',
            data: {
                type: 'Feature',
                properties: {},
                geometry: {
                    type: 'LineString',
                    coordinates: route,
                },
            },
        })

        map.current.addLayer({
            id: 'route-line',
            type: 'line',
            source: sourceId,
            layout: {
                'line-join': 'round',
                'line-cap': 'round',
            },
            paint: {
                'line-color': '#00d4ff',
                'line-width': 3,
                'line-opacity': 0.8,
            },
        })
    }, [route, mapLoaded])

    return (
        <div ref={mapContainer} className="w-full h-full">
            {!mapLoaded && (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-900/50">
                    <div className="w-8 h-8 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
                </div>
            )}
        </div>
    )
}
