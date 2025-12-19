import { useRef, useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';
import MessageBubble from './Chat/MessageBubble';
import InputArea from './Chat/InputArea';
import Stage1 from './Stage1';
import Stage2 from './Stage2';
import Stage3 from './Stage3';
import EpistemicPanel from './EpistemicPanel';
import DisagreementExplorer from './DisagreementExplorer';
import CostEstimator from './CostEstimator';
import { ShaderCanvas } from './shader/ShaderCanvas';
import { api } from '../api';
import './ChatInterface.css';

export default function ChatInterface({
  conversation,
  onSendMessage,
  isLoading,
}) {
  const messagesEndRef = useRef(null);
  const [showCostEstimator, setShowCostEstimator] = useState(false);
  const [costQuery, setCostQuery] = useState('');
  const [activeModels, setActiveModels] = useState([]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation?.messages?.length, conversation?.messages?.[conversation?.messages?.length - 1]?.stage1]);

  // Fetch models for cost estimation
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const models = await api.getModels();
        setActiveModels(models.map(m => m.id));
      } catch (e) {
        console.error("Failed to load models for cost estimation", e);
        // Fallback default
        setActiveModels(['google/gemini-2.0-flash-exp:free', 'meta-llama/llama-3.2-11b-vision-instruct:free']);
      }
    };
    fetchModels();
  }, []);

  const handleCheckCost = (query) => {
    setCostQuery(query);
    setShowCostEstimator(true);
  };

  const handleProceedWithCost = () => {
    setShowCostEstimator(false);
    onSendMessage(costQuery);
  };

  if (!conversation) {
    return (
      <div className="chat-interface">
        <div className="welcome-sphere">
          <ShaderCanvas size={250} shaderId={4} />
          <h2>Welcome to LLM Council</h2>
          <p>Create a new conversation to begin your research.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-interface">
      <div className="messages-container">
        {conversation.messages.length === 0 ? (
          <div className="welcome-sphere">
            <ShaderCanvas size={200} shaderId={2} />
            <h2>Start a conversation</h2>
            <p>Ask a question to consult the council of models.</p>
          </div>
        ) : (
          conversation.messages.map((msg, index) => (
            <MessageBubble
              key={index}
              message={msg}
              isUser={msg.role === 'user'}
            >
              {msg.role === 'assistant' && (
                <div className="council-stages">
                  {/* Stage 1 */}
                  {msg.loading?.stage1 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Stage 1: Gathering individual perspectives...</span>
                    </div>
                  )}
                  {msg.stage1 && <Stage1 responses={msg.stage1} />}

                  {/* Stage 2 */}
                  {msg.loading?.stage2 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Stage 2: Peer Review & Ranking...</span>
                    </div>
                  )}
                  {msg.stage2 && (
                    <Stage2
                      rankings={msg.stage2}
                      labelToModel={msg.metadata?.label_to_model}
                      aggregateRankings={msg.metadata?.aggregate_rankings}
                    />
                  )}

                  {/* Stage 3 */}
                  {msg.loading?.stage3 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Stage 3: Final Synthesis...</span>
                    </div>
                  )}
                  {msg.stage3 && (
                    <>
                      <Stage3 finalResponse={msg.stage3} />
                      {msg.metadata && (
                        <div className="post-analysis">
                          <EpistemicPanel
                            agreementScore={msg.metadata.agreement_score || 0.75} // Fallback if missing
                            confidenceMean={msg.metadata.confidence_mean || 0.8}
                            disagreements={msg.metadata.disagreements || []}
                          />
                          <DisagreementExplorer
                            claims={msg.metadata.claims || []}
                            onVerify={async (claim) => {
                              console.log("Verifying", claim);
                              // Todo: Implement verification
                            }}
                          />
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </MessageBubble>
          ))
        )}

        {isLoading && !conversation.messages[conversation.messages.length - 1]?.loading && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <span>Consulting the council...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <AnimatePresence>
        {showCostEstimator && (
          <CostEstimator
            query={costQuery}
            models={activeModels}
            onProceed={handleProceedWithCost}
            onCancel={() => setShowCostEstimator(false)}
          />
        )}
      </AnimatePresence>

      <InputArea
        onSendMessage={onSendMessage}
        onCheckCost={handleCheckCost}
        isLoading={isLoading}
      />
    </div>
  );
}
