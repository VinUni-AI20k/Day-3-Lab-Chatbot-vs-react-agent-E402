import './App.css';
import ChatPanel from './components/ChatPanel';
import ActivityPanel from './components/ActivityPanel';
import { useAgentChat } from './hooks/useAgentChat';

/**
 * App - Main layout with split screen:
 * Left: Agent chat interface
 * Right: Visual activity panel showing what the agent is doing
 */
export default function App() {
  const {
    messages,
    isTyping,
    currentActivity,
    agentSteps,
    sendMessage,
    clearChat
  } = useAgentChat();

  return (
    <div className="app">
      {/* Left Panel - Chat */}
      <div className="panel-left">
        <ChatPanel
          messages={messages}
          isTyping={isTyping}
          agentSteps={agentSteps}
          onSendMessage={sendMessage}
          onClear={clearChat}
        />
      </div>

      {/* Divider */}
      <div className="panel-divider" />

      {/* Right Panel - Activity */}
      <div className="panel-right">
        <ActivityPanel
          currentActivity={currentActivity}
          agentSteps={agentSteps}
        />
      </div>
    </div>
  );
}
