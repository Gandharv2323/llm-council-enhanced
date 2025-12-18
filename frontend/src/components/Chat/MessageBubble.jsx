import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { User, Sparkles } from 'lucide-react';
import clsx from 'clsx';
import './MessageBubble.css';

export default function MessageBubble({ message, isUser, children }) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className={clsx(
                "message-row",
                isUser ? "message-user" : "message-council"
            )}
        >
            <div className="message-avatar">
                {isUser ? <User size={18} /> : <Sparkles size={18} />}
            </div>

            <div className="message-bubble glass-panel">
                <div className="message-header">
                    <span className="role-name">{isUser ? "You" : "LLM Council"}</span>
                </div>

                <div className="message-content markdown-content">
                    {/* Primary content (User/Assistant text) */}
                    {message.content && <ReactMarkdown>{message.content}</ReactMarkdown>}

                    {/* Stage components passed as children */}
                    {children}
                </div>
            </div>
        </motion.div>
    );
}
