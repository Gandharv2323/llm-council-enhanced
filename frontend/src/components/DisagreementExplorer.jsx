import { useState } from 'react';
import { ShieldCheck, AlertCircle, ThumbsUp, ThumbsDown, Search, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import './DisagreementExplorer.css';

export function DisagreementExplorer({ claims = [], onVerify }) {
    const [selectedClaimIndex, setSelectedClaimIndex] = useState(null);
    const [verifying, setVerifying] = useState(false);

    const contested = claims.filter(c =>
        c.contradicting.length > 0 && c.supporting.length > 0
    );

    const handleVerify = async (claim) => {
        if (!onVerify) return;
        setVerifying(true);
        try {
            await onVerify(claim);
        } finally {
            setVerifying(false);
        }
    };

    if (contested.length === 0) return null;

    return (
        <div className="disagreement-explorer glass-panel">
            <div className="explorer-header">
                <AlertCircle size={20} className="header-icon" />
                <div className="header-text">
                    <h4>Conflict Resolution</h4>
                    <span className="count">{contested.length} contested issues found</span>
                </div>
            </div>

            <div className="claims-list">
                {contested.map((claim, i) => {
                    const isSelected = selectedClaimIndex === i;

                    return (
                        <motion.div
                            key={i}
                            layout
                            className={clsx('claim-card', isSelected && 'selected')}
                            onClick={() => setSelectedClaimIndex(isSelected ? null : i)}
                        >
                            <div className="claim-summary">
                                <div className="claim-vote-bar">
                                    <div className="vote-segment support" style={{ flex: claim.supporting.length || 1 }} />
                                    <div className="vote-segment contradict" style={{ flex: claim.contradicting.length || 1 }} />
                                </div>
                                <p className="claim-preview">{claim.claim}</p>
                                <motion.div
                                    className="expand-indicator"
                                    animate={{ rotate: isSelected ? 90 : 0 }}
                                >
                                    <ArrowRight size={16} />
                                </motion.div>
                            </div>

                            <AnimatePresence>
                                {isSelected && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        className="claim-details"
                                    >
                                        <div className="positions-grid">
                                            <div className="position-col">
                                                <div className="col-header support">
                                                    <ThumbsUp size={14} />
                                                    <span>Supporting ({claim.supporting.length})</span>
                                                </div>
                                                <div className="model-list">
                                                    {claim.supporting.map((m, j) => (
                                                        <div key={j} className="model-tag support">{m}</div>
                                                    ))}
                                                </div>
                                            </div>
                                            <div className="position-col">
                                                <div className="col-header contradict">
                                                    <ThumbsDown size={14} />
                                                    <span>Contradicting ({claim.contradicting.length})</span>
                                                </div>
                                                <div className="model-list">
                                                    {claim.contradicting.map((m, j) => (
                                                        <div key={j} className="model-tag contradict">{m}</div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="action-row">
                                            <button
                                                className="verify-action-btn"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleVerify(claim);
                                                }}
                                                disabled={verifying}
                                            >
                                                {verifying ? (
                                                    <span className="animate-pulse">Verifying...</span>
                                                ) : (
                                                    <>
                                                        <Search size={14} />
                                                        Verify with Web Search
                                                    </>
                                                )}
                                            </button>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </motion.div>
                    );
                })}
            </div>
        </div>
    );
}

export default DisagreementExplorer;
