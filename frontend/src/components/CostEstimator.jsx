import { useState, useEffect } from 'react';
import { Clock, Coins, Users, ChevronDown, CheckCircle, XCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import './CostEstimator.css';

export function CostEstimator({ query, models, onProceed, onCancel }) {
    const [estimate, setEstimate] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!query || !models.length) return;

        setLoading(true);

        const inputTokens = Math.ceil(query.length / 4);
        const outputTokensPerModel = 500;
        const totalOutputTokens = outputTokensPerModel * models.length * 3;

        // Rough cost estimate
        const costPerInputToken = 0.000003;
        const costPerOutputToken = 0.000015;

        const maxCost = (inputTokens * costPerInputToken + totalOutputTokens * costPerOutputToken * 1.5);
        const minCost = maxCost * 0.6;

        const timePerModel = 5;
        const estimatedTime = timePerModel * models.length * 2;

        const simulatedDelay = setTimeout(() => {
            setEstimate({
                minCost: minCost.toFixed(4),
                maxCost: maxCost.toFixed(4),
                inputTokens,
                outputTokens: totalOutputTokens,
                estimatedTime,
                modelCount: models.length
            });
            setLoading(false);
        }, 600);
        return () => clearTimeout(simulatedDelay);
    }, [query, models]);

    if (loading) {
        return (
            <div className="cost-estimator glass-panel loading-state">
                <div className="spinner-sm"></div>
                <span>Analyzing complexity...</span>
            </div>
        )
    }

    if (!estimate) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="cost-estimator glass-panel"
        >
            <div className="estimator-header">
                <h4>Pre-Flight Check</h4>
            </div>

            <div className="estimates-grid">
                <div className="est-card">
                    <Coins className="est-icon" size={16} />
                    <div className="est-data">
                        <span className="est-label">Est. Cost</span>
                        <span className="est-value">${estimate.minCost} - ${estimate.maxCost}</span>
                    </div>
                </div>

                <div className="est-card">
                    <Clock className="est-icon" size={16} />
                    <div className="est-data">
                        <span className="est-label">Time</span>
                        <span className="est-value">~{estimate.estimatedTime}s</span>
                    </div>
                </div>

                <div className="est-card">
                    <Users className="est-icon" size={16} />
                    <div className="est-data">
                        <span className="est-label">Models</span>
                        <span className="est-value">{estimate.modelCount} active</span>
                    </div>
                </div>
            </div>

            <div className="estimator-actions">
                <button className="est-btn cancel" onClick={onCancel}>
                    <XCircle size={16} /> Cancel
                </button>
                <button className="est-btn proceed" onClick={onProceed}>
                    <CheckCircle size={16} /> Propose to Council
                </button>
            </div>
        </motion.div>
    );
}

export default CostEstimator;
