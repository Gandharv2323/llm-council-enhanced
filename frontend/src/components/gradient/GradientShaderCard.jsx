import { Canvas } from "@react-three/fiber";
import { motion } from "framer-motion";
import GrainyGradientMesh from "./GrainyGradientMesh";
import "./GradientShaderCard.css";

/**
 * GradientShaderCard - A beautiful animated gradient card using Three.js
 * @param {number} width - Width in pixels
 * @param {number} height - Height in pixels  
 * @param {number} borderRadius - Border radius in pixels
 */
export default function GradientShaderCard({
    width = 200,
    height = 150,
    borderRadius = 24
}) {
    return (
        <motion.div
            className="gradient-shader-card"
            style={{
                width: `${width}px`,
                height: `${height}px`,
                borderRadius: `${borderRadius}px`,
            }}
            whileHover={{ scale: 1.02 }}
            transition={{
                type: "spring",
                stiffness: 300,
                damping: 30,
                mass: 0.8,
            }}
        >
            <Canvas
                camera={{ position: [0, 0, 1] }}
                gl={{ preserveDrawingBuffer: true }}
                style={{ borderRadius: `${borderRadius}px` }}
            >
                <GrainyGradientMesh
                    width={width}
                    height={height}
                />
            </Canvas>
        </motion.div>
    );
}
