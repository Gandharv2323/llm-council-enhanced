import { useEffect, useRef, useState } from "react";
import { shaders, vertexShader } from "./shaders";
import "./ShaderCanvas.css";

/**
 * ShaderCanvas - A WebGL-powered animated sphere with various shader effects
 * @param {number} size - Size of the canvas in pixels
 * @param {function} onClick - Click handler
 * @param {number} shaderId - Which shader to use (1, 2, or 3)
 * @param {string} className - Additional CSS classes
 */
export const ShaderCanvas = ({
    size = 200,
    onClick,
    shaderId = 1,
    className = ""
}) => {
    const canvasRef = useRef(null);
    const animationRef = useRef(0);
    const mousePositionRef = useRef([0.5, 0.5]);
    const programInfoRef = useRef(null);
    const [isHovered, setIsHovered] = useState(false);

    // Get the selected shader
    const selectedShader = shaders.find(s => s.id === shaderId) || shaders[0];

    // Track mouse position relative to the canvas
    const handleMouseMove = (e) => {
        if (!canvasRef.current) return;

        const rect = canvasRef.current.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width;
        const y = (e.clientY - rect.top) / rect.height;
        mousePositionRef.current = [x, y];
    };

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const gl = canvas.getContext("webgl");
        if (!gl) {
            console.error("WebGL not supported");
            return;
        }

        // Initialize shader program
        const shaderProgram = initShaderProgram(gl, vertexShader, selectedShader.fragmentShader);
        if (!shaderProgram) return;

        programInfoRef.current = {
            program: shaderProgram,
            attribLocations: {
                vertexPosition: gl.getAttribLocation(shaderProgram, 'aVertexPosition'),
                textureCoord: gl.getAttribLocation(shaderProgram, 'aTextureCoord'),
            },
            uniformLocations: {
                iResolution: gl.getUniformLocation(shaderProgram, 'iResolution'),
                iTime: gl.getUniformLocation(shaderProgram, 'iTime'),
                iMouse: gl.getUniformLocation(shaderProgram, 'iMouse'),
            },
        };

        // Create buffers
        const buffers = initBuffers(gl);
        let startTime = Date.now();

        // Set canvas size
        canvas.width = size;
        canvas.height = size;
        gl.viewport(0, 0, canvas.width, canvas.height);

        // Render function
        const render = () => {
            const currentTime = (Date.now() - startTime) / 1000;
            const mousePos = mousePositionRef.current;

            drawScene(
                gl,
                programInfoRef.current,
                buffers,
                currentTime,
                canvas.width,
                canvas.height,
                mousePos
            );
            animationRef.current = requestAnimationFrame(render);
        };

        render();

        return () => {
            cancelAnimationFrame(animationRef.current);
            if (gl && shaderProgram) {
                gl.deleteProgram(shaderProgram);
            }
        };
    }, [size, shaderId, selectedShader.fragmentShader]);

    // Initialize shader program
    function initShaderProgram(gl, vsSource, fsSource) {
        const vertShader = loadShader(gl, gl.VERTEX_SHADER, vsSource);
        const fragShader = loadShader(gl, gl.FRAGMENT_SHADER, fsSource);

        if (!vertShader || !fragShader) return null;

        const shaderProgram = gl.createProgram();
        if (!shaderProgram) return null;

        gl.attachShader(shaderProgram, vertShader);
        gl.attachShader(shaderProgram, fragShader);
        gl.linkProgram(shaderProgram);

        if (!gl.getProgramParameter(shaderProgram, gl.LINK_STATUS)) {
            console.error('Unable to initialize shader program: ' + gl.getProgramInfoLog(shaderProgram));
            return null;
        }

        return shaderProgram;
    }

    // Load shader
    function loadShader(gl, type, source) {
        const shader = gl.createShader(type);
        if (!shader) return null;

        gl.shaderSource(shader, source);
        gl.compileShader(shader);

        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            console.error('Shader compile error: ' + gl.getShaderInfoLog(shader));
            gl.deleteShader(shader);
            return null;
        }

        return shader;
    }

    // Initialize buffers
    function initBuffers(gl) {
        const positionBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
        const positions = [
            -1.0, -1.0,
            1.0, -1.0,
            1.0, 1.0,
            -1.0, 1.0,
        ];
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(positions), gl.STATIC_DRAW);

        const textureCoordBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, textureCoordBuffer);
        const textureCoordinates = [
            0.0, 0.0,
            1.0, 0.0,
            1.0, 1.0,
            0.0, 1.0,
        ];
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(textureCoordinates), gl.STATIC_DRAW);

        const indexBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer);
        const indices = [0, 1, 2, 0, 2, 3];
        gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(indices), gl.STATIC_DRAW);

        return {
            position: positionBuffer,
            textureCoord: textureCoordBuffer,
            indices: indexBuffer,
        };
    }

    // Draw the scene
    function drawScene(gl, programInfo, buffers, currentTime, width, height, mousePos) {
        gl.clearColor(0.0, 0.0, 0.0, 0.0);
        gl.clearDepth(1.0);
        gl.enable(gl.DEPTH_TEST);
        gl.depthFunc(gl.LEQUAL);
        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

        gl.useProgram(programInfo.program);

        // Set uniforms
        gl.uniform2f(programInfo.uniformLocations.iResolution, width, height);
        gl.uniform1f(programInfo.uniformLocations.iTime, currentTime);
        gl.uniform2f(programInfo.uniformLocations.iMouse, mousePos[0], mousePos[1]);

        // Set vertex position attribute
        gl.bindBuffer(gl.ARRAY_BUFFER, buffers.position);
        gl.vertexAttribPointer(programInfo.attribLocations.vertexPosition, 2, gl.FLOAT, false, 0, 0);
        gl.enableVertexAttribArray(programInfo.attribLocations.vertexPosition);

        // Set texture coordinate attribute
        gl.bindBuffer(gl.ARRAY_BUFFER, buffers.textureCoord);
        gl.vertexAttribPointer(programInfo.attribLocations.textureCoord, 2, gl.FLOAT, false, 0, 0);
        gl.enableVertexAttribArray(programInfo.attribLocations.textureCoord);

        // Draw
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, buffers.indices);
        gl.drawElements(gl.TRIANGLES, 6, gl.UNSIGNED_SHORT, 0);
    }

    const handleMouseLeave = () => {
        setIsHovered(false);
        mousePositionRef.current = [0.5, 0.5];
    };

    return (
        <canvas
            ref={canvasRef}
            className={`shader-canvas ${className}`}
            style={{
                width: size,
                height: size,
                transform: isHovered ? 'scale(1.05)' : 'scale(1)',
                cursor: onClick ? 'pointer' : 'default',
                boxShadow: isHovered ? `0 0 30px ${selectedShader.color}40` : 'none'
            }}
            onClick={onClick}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={handleMouseLeave}
            onMouseMove={handleMouseMove}
        />
    );
};

export default ShaderCanvas;
