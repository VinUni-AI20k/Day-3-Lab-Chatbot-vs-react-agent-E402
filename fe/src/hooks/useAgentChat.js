import { useState, useCallback, useRef } from 'react';
import { AGENT_SCENARIOS, matchScenario, MOCK_MOVIES } from '../data/mockData';

/**
 * Custom hook to manage agent chat interactions
 * Simulates the ReAct agent loop with step-by-step execution
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
  const stepIndexRef = useRef(0);

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
   * Process agent steps one by one with delays to simulate thinking
   */
  const processSteps = useCallback(async (scenario) => {
    const steps = scenario.steps;
    const allSteps = [];

    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      const delay = step.type === 'thought' ? 1200 :
                    step.type === 'action' ? 800 :
                    step.type === 'observation' ? 1000 : 600;

      await new Promise(resolve => setTimeout(resolve, delay));

      const stepData = {
        ...step,
        id: `step-${Date.now()}-${i}`,
        timestamp: new Date()
      };
      allSteps.push(stepData);
      setAgentSteps([...allSteps]);

      // Update activity panel based on scenario type
      if (step.type === 'action' || step.type === 'observation') {
        if (scenario.activityType === 'movies') {
          setCurrentActivity({
            type: 'movies',
            data: MOCK_MOVIES
          });
        } else if (scenario.activityType === 'showtimes') {
          const movie = MOCK_MOVIES.find(m => m.film_name === scenario.filmName);
          setCurrentActivity({
            type: 'showtimes',
            data: movie
          });
        } else if (scenario.activityType === 'seatmap') {
          const movie = MOCK_MOVIES.find(m => m.film_name === scenario.filmName);
          const showtime = movie?.showtimes.find(s => s.cinema === scenario.cinema && s.time === scenario.time);
          setCurrentActivity({
            type: 'seatmap',
            data: { movie, showtime }
          });
        } else if (scenario.activityType === 'booking' && step.type === 'observation' && i === steps.length - 2) {
          setCurrentActivity({
            type: 'booking',
            data: {
              filmName: scenario.filmName,
              cinema: scenario.cinema,
              time: scenario.time,
              zone: scenario.zone,
              seats: scenario.seats,
              bookingId: scenario.bookingId,
              totalPrice: scenario.totalPrice
            }
          });
        }
      }

      // Add final answer as a chat message
      if (step.type === 'final_answer') {
        addMessage('agent', step.content);
      }
    }

    setIsTyping(false);
  }, [addMessage]);

  /**
   * Send a message from the user
   */
  const sendMessage = useCallback((content) => {
    if (!content.trim() || isTyping) return;

    // Add user message
    addMessage('user', content);
    setIsTyping(true);
    setAgentSteps([]);

    // Match scenario and process
    const scenarioKey = matchScenario(content);
    const scenario = AGENT_SCENARIOS[scenarioKey];

    // Small delay before agent starts "thinking"
    setTimeout(() => {
      processSteps(scenario);
    }, 500);
  }, [isTyping, addMessage, processSteps]);

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
