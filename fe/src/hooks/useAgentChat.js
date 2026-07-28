import { useState, useCallback, useRef } from 'react';
import { streamChat, fetchMovies, fetchSeatMap, getPosterUrl } from '../services/api';

/**
 * Custom hook to manage agent chat interactions
 * Connects to the backend ReAct agent via SSE streaming
 */
export function useAgentChat() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'agent',
      content: 'Xin chào! 👋 Tôi là trợ lý đặt vé xem phim CGV. Hãy cho tôi biết bạn muốn xem phim gì nhé!',
      timestamp: new Date()
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [currentActivity, setCurrentActivity] = useState(null);
  const [agentSteps, setAgentSteps] = useState([]);
  const historyRef = useRef([]);

  const addMessage = useCallback((role, content) => {
    const msg = {
      id: `msg-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      role,
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, msg]);
    return msg;
  }, []);

  /**
   * Update the activity panel based on the tool being called and its result
   */
  const updateActivity = useCallback(async (step) => {
    try {
      if (step.type === 'action') {
        const toolName = step.tool || '';

        if (toolName === 'search_movie' || toolName === 'search_theater') {
          // Will update on observation
        } else if (toolName === 'get_available_seats') {
          // Will update on observation
        }
      }

      if (step.type === 'observation') {
        const toolName = step.tool || '';
        const result = step.toolResult;

        if (toolName === 'search_movie' && result && typeof result === 'object' && result.film_name) {
          // Show movie info
          setCurrentActivity({
            type: 'movie_detail',
            data: result
          });
        }

        if (toolName === 'search_theater' && Array.isArray(result)) {
          setCurrentActivity({
            type: 'theaters',
            data: result
          });
        }

        if (toolName === 'search_showtime' && Array.isArray(result)) {
          setCurrentActivity({
            type: 'showtimes',
            data: {
              showtimes: result,
              filmName: step.filmName || '',
              cinema: step.cinema || ''
            }
          });
        }

        if (toolName === 'get_available_seats' && Array.isArray(result)) {
          setCurrentActivity({
            type: 'available_seats',
            data: {
              seats: result,
              filmName: step.filmName || '',
              cinema: step.cinema || '',
              time: step.time || ''
            }
          });
        }

        if (toolName === 'book_seats' && result && typeof result === 'object') {
          if (result.status === 'SUCCESS') {
            setCurrentActivity({
              type: 'booking',
              data: result
            });
          }
        }

        if (toolName === 'generate_ticket' && result && typeof result === 'object') {
          setCurrentActivity({
            type: 'ticket',
            data: result
          });
        }
      }
    } catch (err) {
      console.error('Error updating activity:', err);
    }
  }, []);

  /**
   * Send a message from the user, stream agent responses via SSE
   */
  const sendMessage = useCallback(async (content) => {
    if (!content.trim() || isTyping) return;

    // Add user message
    addMessage('user', content);
    setIsTyping(true);
    setAgentSteps([]);

    // Build history for the API
    const history = historyRef.current.slice(-10); // Keep last 10 messages
    historyRef.current.push({ role: 'user', content });

    try {
      const allSteps = [];

      for await (const step of streamChat(content, history)) {
        const stepData = {
          ...step,
          id: `step-${Date.now()}-${Math.random().toString(36).slice(2, 5)}`,
          timestamp: new Date()
        };

        allSteps.push(stepData);
        setAgentSteps([...allSteps]);

        // Update activity panel
        await updateActivity(step);

        // If it's a final answer, add it as a chat message
        if (step.type === 'final_answer') {
          addMessage('agent', step.content);
          historyRef.current.push({ role: 'assistant', content: step.content });
        }
      }
    } catch (err) {
      console.error('Chat error:', err);
      // Fallback - show error message
      addMessage('agent', `⚠️ Có lỗi xảy ra khi kết nối với server: ${err.message}\n\nHãy đảm bảo backend đang chạy tại http://localhost:8000`);
    } finally {
      setIsTyping(false);
    }
  }, [isTyping, addMessage, updateActivity]);

  const clearChat = useCallback(() => {
    setMessages([{
      id: 'welcome',
      role: 'agent',
      content: 'Xin chào! 👋 Tôi là trợ lý đặt vé xem phim CGV. Hãy cho tôi biết bạn muốn xem phim gì nhé!',
      timestamp: new Date()
    }]);
    setAgentSteps([]);
    setCurrentActivity(null);
    setIsTyping(false);
    historyRef.current = [];
  }, []);

  return {
    messages,
    isTyping,
    currentActivity,
    agentSteps,
    sendMessage,
    clearChat
  };
}
