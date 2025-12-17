import { useState, useEffect, useCallback } from 'react';

/**
 * Hook for streaming council responses via SSE
 */
export function useStreaming(conversationId, messageId) {
  const [state, setState] = useState({
    stage1: { complete: [], streaming: null, status: 'pending' },
    stage2: { complete: [], streaming: null, status: 'pending' },
    stage3: { content: null, status: 'pending' },
    error: null,
    isComplete: false
  });

  const [eventSource, setEventSource] = useState(null);

  const startStreaming = useCallback((queryId) => {
    if (eventSource) {
      eventSource.close();
    }

    const es = new EventSource(`/api/stream/${queryId}`);
    setEventSource(es);

    es.onmessage = (event) => {
      try {
        const update = JSON.parse(event.data);
        
        setState(prev => {
          const newState = { ...prev };
          
          if (update.type === 'stage1_start') {
            newState.stage1.status = 'running';
          } else if (update.type === 'stage1_response') {
            newState.stage1.complete = [...prev.stage1.complete, update.data];
          } else if (update.type === 'stage1_complete') {
            newState.stage1.status = 'complete';
          } else if (update.type === 'stage2_start') {
            newState.stage2.status = 'running';
          } else if (update.type === 'stage2_response') {
            newState.stage2.complete = [...prev.stage2.complete, update.data];
          } else if (update.type === 'stage2_complete') {
            newState.stage2.status = 'complete';
          } else if (update.type === 'stage3_start') {
            newState.stage3.status = 'running';
          } else if (update.type === 'stage3_complete') {
            newState.stage3.content = update.data;
            newState.stage3.status = 'complete';
            newState.isComplete = true;
          } else if (update.type === 'error') {
            newState.error = update.message;
          }
          
          return newState;
        });
      } catch (e) {
        console.error('Failed to parse SSE message:', e);
      }
    };

    es.onerror = (error) => {
      console.error('SSE error:', error);
      setState(prev => ({ ...prev, error: 'Connection lost' }));
      es.close();
    };
  }, [eventSource]);

  const stopStreaming = useCallback(() => {
    if (eventSource) {
      eventSource.close();
      setEventSource(null);
    }
  }, [eventSource]);

  useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [eventSource]);

  return {
    ...state,
    startStreaming,
    stopStreaming
  };
}

/**
 * Hook for cost estimation
 */
export function useCostEstimate() {
  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(false);

  const getEstimate = useCallback(async (query, models) => {
    setLoading(true);
    try {
      const response = await fetch('/api/estimate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, models })
      });
      const data = await response.json();
      setEstimate(data);
    } catch (e) {
      console.error('Failed to get cost estimate:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  return { estimate, loading, getEstimate };
}

/**
 * Hook for council configuration
 */
export function useCouncilConfig() {
  const [config, setConfig] = useState({
    models: [],
    chairman: null,
    skipStage2: false
  });

  const [availableModels, setAvailableModels] = useState([]);

  useEffect(() => {
    fetch('/api/models')
      .then(r => r.json())
      .then(data => setAvailableModels(data.models || []))
      .catch(e => console.error('Failed to load models:', e));
  }, []);

  const addModel = useCallback((model) => {
    setConfig(prev => ({
      ...prev,
      models: [...prev.models, model]
    }));
  }, []);

  const removeModel = useCallback((model) => {
    setConfig(prev => ({
      ...prev,
      models: prev.models.filter(m => m !== model)
    }));
  }, []);

  const setChairman = useCallback((model) => {
    setConfig(prev => ({ ...prev, chairman: model }));
  }, []);

  const toggleStage2 = useCallback(() => {
    setConfig(prev => ({ ...prev, skipStage2: !prev.skipStage2 }));
  }, []);

  return {
    config,
    availableModels,
    addModel,
    removeModel,
    setChairman,
    toggleStage2
  };
}

export default { useStreaming, useCostEstimate, useCouncilConfig };
