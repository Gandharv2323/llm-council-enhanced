import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Coins } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import './InputArea.css';

export default function InputArea({ onSendMessage, onCheckCost, isLoading }) {
    const [input, setInput] = useState('');
    const textareaRef = useRef(null);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
        }
    }, [input]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (input.trim() && !isLoading) {
            onSendMessage(input);
            setInput('');
            if (textareaRef.current) textareaRef.current.style.height = 'auto';
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    return (
        <div className="input-area-container">
            <form className="input-form glass-panel" onSubmit={handleSubmit}>
                <div className="input-wrapper">
                    <textarea
                        ref={textareaRef}
                        className="message-input"
                        placeholder="Ask the council..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={isLoading}
                        rows={1}
                    />
                </div>

                <div className="input-actions">
                    <button
                        type="button"
                        className="action-icon-btn"
                        onClick={() => onCheckCost && onCheckCost(input)}
                        disabled={isLoading || !input.trim()}
                        title="Estimate Cost"
                    >
                        <Coins size={20} />
                    </button>

                    <AnimatePresence>
                        {input.trim() && (
                            <motion.button
                                initial={{ scale: 0, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                exit={{ scale: 0, opacity: 0 }}
                                type="submit"
                                className="send-button"
                                disabled={isLoading}
                            >
                                {isLoading ? (
                                    <Sparkles className="animate-spin" size={20} />
                                ) : (
                                    <Send size={20} />
                                )}
                            </motion.button>
                        )}
                    </AnimatePresence>
                </div>
            </form>
            <div className="input-footer">
                Powered by Multi-LLM Consensus • Enter to send, Shift+Enter for newline
            </div>
        </div>
    );
}
