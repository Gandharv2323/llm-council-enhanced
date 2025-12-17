import { useState } from 'react';
import { ChevronDown, ChevronRight, AlertTriangle, CheckCircle2, TrendingUp, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import './EpistemicPanel.css';

export function EpistemicPanel({
    agreementScore = 0,
    confidenceMean = 0,
    disagreements = [],
    onInvestigate
}) {
    const [expanded, setExpanded] = useState(false);

    const getAgreementLevel = (score) => {
        if (score >= 0.8) return { label: 'Strong Consensus', color: 'var(--status-success)', icon: CheckCircle2 };
        if (score >= 0.6) return { label: 'Moderate Agreement', color: 'var(--status-warning)', icon: Activity };
        return { label: 'High Divergence', color: 'var(--status-error)', icon: AlertTriangle };
    };

    const agreement = getAgreementLevel(agreementScore);
    const hasDisagreements = disagreements.length > 0;
    const AgreementIcon = agreement.icon;

    return (
        <div className="epistemic-panel glass-panel">
            <div className="epistemic-header">
                <div className="header-title">
                    <Activity size={18} className="header-icon" />
                    <h4>Council Analytics</h4>
                </div>
                {hasDisagreements && (
                    <span className="disagreement-badge">
                        <AlertTriangle size={14} />
                        {disagreements.length} Potential Issues
                    </span>
                )}
            </div>

            <div className="epistemic-metrics">
                <div className="metric-card">
                    <div className="metric-header">
                        <span className="metric-label">Agreement</span>
                        <span className="metric-value" style={{ color: agreement.color }}>
                            {(agreementScore * 100).toFixed(0)}%
                        </span>
                    </div>
                    <div className="progress-bar">
                        <div
                            className="progress-fill"
                            style={{
                                width: `${agreementScore * 100}%`,
                                backgroundColor: agreement.color,
                                boxShadow: `0 0 10px ${agreement.color}40`
                            }}
                        />
                    </div>
                    <div className="metric-status" style={{ color: agreement.color }}>
                        <AgreementIcon size={14} />
                        {agreement.label}
                    </div>
                </div>

                <div className="metric-card">
                    <div className="metric-header">
                        <span className="metric-label">Confidence</span>
                        <span className="metric-value">
                            {(confidenceMean * 100).toFixed(0)}%
                        </span>
                    </div>
                    <div className="progress-bar">
                        <div
                            className="progress-fill"
                            style={{
                                width: `${confidenceMean * 100}%`,
                                backgroundColor: 'var(--accent-primary)'
                            }}
                        />
                    </div>
                    <div className="metric-status">
                        <TrendingUp size={14} />
                        Average Confidence
                    </div>
                </div>
            </div>

            {hasDisagreements && (
                <div className="disagreements-section">
                    <button
                        className="toggle-disagreements"
                        onClick={() => setExpanded(!expanded)}
                    >
                        {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                        View Disagreements
                    </button>

                    <AnimatePresence>
                        {expanded && (
                            <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                className="disagreements-list"
                            >
                                {disagreements.map((d, i) => (
                                    <div key={i} className="disagreement-item">
                                        <div className="claim-text">{d.claim}</div>
                                        <div className="claim-positions">
                                            <div className="position-group supporting">
                                                <span className="group-label">Supporting:</span>
                                                <div className="model-chips">
                                                    {d.supporting.map((m, j) => (
                                                        <span key={j} className="model-chip support">{m}</span>
                                                    ))}
                                                </div>
                                            </div>
                                            <div className="position-group contradicting">
                                                <span className="group-label">Contradicting:</span>
                                                <div className="model-chips">
                                                    {d.contradicting.map((m, j) => (
                                                        <span key={j} className="model-chip contradict">{m}</span>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                        {onInvestigate && (
                                            <button
                                                className="investigate-btn"
                                                onClick={() => onInvestigate(d)}
                                            >
                                                Details
                                            </button>
                                        )}
                                    </div>
                                ))}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            )}
        </div>
    );
}

export default EpistemicPanel;
