import { Plus, MessageSquare, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import GradientShaderCard from './gradient/GradientShaderCard';
import './Sidebar.css';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
}) {
  return (
    <div className="sidebar-inner">
      <div className="sidebar-header">
        <div className="brand">
          <div className="brand-icon">🏛️</div>
          <h1>LLM Council</h1>
        </div>

        <motion.button
          className="new-chat-btn"
          onClick={onNewConversation}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <Plus size={20} />
          <span>New Conversation</span>
        </motion.button>

        {/* Gradient Shader Card below button */}
        <div className="sidebar-shader-card">
          <GradientShaderCard width={220} height={140} borderRadius={16} />
        </div>
      </div>

      <div className="conversation-list">
        <h3 className="list-title">History</h3>

        {conversations.length === 0 ? (
          <div className="empty-state">
            <MessageSquare size={32} />
            <p>No conversations yet</p>
          </div>
        ) : (
          <div className="list-content">
            {conversations.map((conv, i) => (
              <motion.button
                key={conv.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className={clsx(
                  'conversation-item',
                  conv.id === currentConversationId && 'active'
                )}
                onClick={() => onSelectConversation(conv.id)}
              >
                <div className="conv-info">
                  <span className="conv-title">{conv.title || 'New Conversation'}</span>
                  <span className="conv-meta">{conv.message_count} messages</span>
                </div>
                {conv.id === currentConversationId && (
                  <ChevronRight size={16} className="active-indicator" />
                )}
              </motion.button>
            ))}
          </div>
        )}
      </div>

      <div className="sidebar-footer">
        <div className="user-profile">
          <div className="avatar">U</div>
          <div className="user-info">
            <span className="name">User</span>
            <span className="plan">Free Tier</span>
          </div>
        </div>
      </div>
    </div>
  );
}
