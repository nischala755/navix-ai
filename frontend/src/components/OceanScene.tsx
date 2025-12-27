import { useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import * as THREE from 'three'

function WaterPlane() {
    const meshRef = useRef<THREE.Mesh>(null)
    const geometryRef = useRef<THREE.PlaneGeometry>(null)

    useFrame(({ clock }) => {
        if (meshRef.current && geometryRef.current) {
            const positions = geometryRef.current.attributes.position as THREE.BufferAttribute
            const time = clock.getElapsedTime()

            for (let i = 0; i < positions.count; i++) {
                const x = positions.getX(i)
                const z = positions.getZ(i)
                const y = Math.sin(x * 0.3 + time * 0.8) * 0.3 +
                    Math.sin(z * 0.2 + time * 0.6) * 0.4 +
                    Math.sin((x + z) * 0.1 + time * 0.4) * 0.2
                positions.setY(i, y)
            }
            positions.needsUpdate = true
        }
    })

    return (
        <mesh ref={meshRef} rotation={[-Math.PI / 2, 0, 0]}>
            <planeGeometry ref={geometryRef} args={[40, 40, 128, 128]} />
            <meshStandardMaterial
                color="#0a3d62"
                metalness={0.8}
                roughness={0.2}
                transparent
                opacity={0.8}
            />
        </mesh>
    )
}

function Particles() {
    const pointsRef = useRef<THREE.Points>(null)

    useFrame(({ clock }) => {
        if (pointsRef.current) {
            pointsRef.current.rotation.y = clock.getElapsedTime() * 0.02
        }
    })

    const count = 200
    const positions = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 40
        positions[i * 3 + 1] = Math.random() * 10 + 2
        positions[i * 3 + 2] = (Math.random() - 0.5) * 40
    }

    return (
        <points ref={pointsRef}>
            <bufferGeometry>
                <float32BufferAttribute
                    attach="attributes-position"
                    args={[positions, 3]}
                />
            </bufferGeometry>
            <pointsMaterial
                size={0.05}
                color="#00d4ff"
                transparent
                opacity={0.6}
                sizeAttenuation
            />
        </points>
    )
}

export default function OceanScene() {
    return (
        <div className="absolute inset-0 z-0">
            <Canvas
                camera={{ position: [0, 8, 15], fov: 60 }}
                gl={{ antialias: true, alpha: true }}
            >
                <ambientLight intensity={0.3} />
                <directionalLight position={[10, 10, 5]} intensity={0.5} color="#00d4ff" />
                <pointLight position={[-10, 5, -10]} intensity={0.3} color="#00ffc8" />
                <fog attach="fog" args={['#0a1628', 10, 50]} />
                <WaterPlane />
                <Particles />
            </Canvas>
        </div>
    )
}
