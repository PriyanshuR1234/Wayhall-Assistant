import React, { useState, useEffect } from 'react';
import {
  FaBars,
  FaPlus,
  FaDatabase,
  FaCity,
  FaShieldAlt,
  FaBook,
  FaExternalLinkAlt,
} from 'react-icons/fa';
import ChatWindow from './components/ChatWindow';
import InputBox from './components/InputBox';
import Sidebar from './components/Sidebar';
import KnowledgeBaseModal from './components/KnowledgeBaseModal';
import {
  checkHealth,
  sendChatMessage,
  fetchSessionHistory,
} from './api/client';
import './index.css';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [knowledgeModalOpen, setKnowledgeModalOpen] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);
  const [sessions, setSessions] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('wayhall_sessions') || '[]');
    } catch {
      return [];
    }
  });

  // Check health and load status on mount
  useEffect(() => {
    loadHealth();
    const interval = setInterval(loadHealth, 20000);
    return () => clearInterval(interval);
  }, []);

  const loadHealth = async () => {
    const status = await checkHealth();
    setSystemStatus(status);
  };

  const saveSessionMetadata = (id, firstMessage) => {
    setSessions((prev) => {
      const exists = prev.find((s) => s.id === id);
      if (exists) return prev;
      const title =
        firstMessage.length > 38 ? firstMessage.slice(0, 38) + '...' : firstMessage;
      const updated = [{ id, title, createdAt: new Date().toISOString() }, ...prev];
      localStorage.setItem('wayhall_sessions', JSON.stringify(updated));
      return updated;
    });
  };

  const handleSendMessage = async (messageText) => {
    const text = messageText.trim();
    if (!text || isTyping) return;

    const userTurn = {
      text,
      isUserMessage: true,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userTurn]);
    setIsTyping(true);

    try {
      const result = await sendChatMessage(text, sessionId);
      const currentId = result.session_id || sessionId;
      setSessionId(currentId);

      // Save session title if first turn
      if (messages.length === 0) {
        saveSessionMetadata(currentId, text);
      }

      const assistantTurn = {
        text: result.answer,
        isUserMessage: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: result.citations || [],
        unsupported_parts: result.unsupported_parts || [],
        retrieval_doc_labels: result.retrieval_doc_labels || [],
      };

      setMessages((prev) => [...prev, assistantTurn]);
    } catch (err) {
      console.error('Chat error:', err);
      const errorTurn = {
        text: `**System Communication Error:** ${err.message || 'Unable to connect to the municipal knowledge engine. Please ensure the backend is running at http://localhost:8000.'}`,
        isUserMessage: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: [],
        unsupported_parts: [],
      };
      setMessages((prev) => [...prev, errorTurn]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleNewChat = () => {
    setSessionId(null);
    setMessages([]);
    setSidebarOpen(false);
  };

  const handleSelectSession = async (id) => {
    setSessionId(id);
    setSidebarOpen(false);
    setIsTyping(true);
    try {
      const detail = await fetchSessionHistory(id);
      const formatted = (detail.messages || []).map((m) => ({
        text: m.content,
        isUserMessage: m.role === 'user',
        timestamp: new Date(m.created_at).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
        citations: m.citations || [],
        unsupported_parts: [],
      }));
      setMessages(formatted);
    } catch (err) {
      console.error('Failed to load session:', err);
    } finally {
      setIsTyping(false);
    }
  };

  const handleDeleteSession = (id) => {
    const updated = sessions.filter((s) => s.id !== id);
    setSessions(updated);
    localStorage.setItem('wayhall_sessions', JSON.stringify(updated));
    if (sessionId === id) {
      handleNewChat();
    }
  };

  const isConnected = systemStatus?.status === 'healthy';

  return (
    <div className="flex flex-col h-screen w-screen bg-[#0b0f19] text-slate-100 overflow-hidden font-sans">
      {/* Top Civic Navigation Bar */}
      <header className="flex items-center justify-between w-full h-15 px-4 bg-slate-950/80 border-b border-slate-800/80 backdrop-blur-md z-30 select-none">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-900 transition"
            aria-label="Toggle navigation drawer"
          >
            <FaBars size={16} />
          </button>

          <button
            onClick={handleNewChat}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-900 transition flex items-center gap-1.5 text-xs font-medium"
            title="Start new inquiry"
          >
            <FaPlus size={12} />
            <span className="hidden sm:inline">New Inquiry</span>
          </button>

          <div className="h-4 w-px bg-slate-800 hidden sm:block" />

          {/* Title Branding */}
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white font-bold text-sm shadow-sm shadow-emerald-950">
              <FaCity size={15} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-white tracking-tight">Wayhall</span>
                <span className="text-xs font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                  Civic AI
                </span>
              </div>
              <p className="text-[10px] text-slate-400 hidden md:block">
                North American Municipal Services, By-laws & Permits
              </p>
            </div>
          </div>
        </div>

        {/* Right Action Icons */}
        <div className="flex items-center gap-2.5">
          {/* Knowledge Base Inspector button */}
          <button
            onClick={() => setKnowledgeModalOpen(true)}
            className="flex items-center gap-1.5 bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white px-3 py-1.5 rounded-xl text-xs font-medium transition shadow-sm"
          >
            <FaDatabase className="text-emerald-400" size={12} />
            <span className="hidden sm:inline">Knowledge Base</span>
            <span className="bg-slate-800 text-slate-400 text-[10px] font-mono px-1.5 py-0.5 rounded ml-0.5">
              {systemStatus?.chunks_indexed || 0}
            </span>
          </button>

          {/* Connection Pill */}
          <div
            className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border ${
              isConnected
                ? 'bg-emerald-950/40 text-emerald-300 border-emerald-800/40'
                : 'bg-rose-950/40 text-rose-300 border-rose-800/40'
            }`}
            title={`Database: ${systemStatus?.db || 'unreachable'} | Gemini: ${systemStatus?.gemini || 'unreachable'}`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
              }`}
            />
            <span className="text-[11px] font-medium hidden sm:inline">
              {isConnected ? 'Engine Online' : 'Engine Degraded'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <div className="relative flex flex-1 w-full h-[calc(100vh-3.75rem)] overflow-hidden">
        {/* Navigation Sidebar */}
        <Sidebar
          isOpen={sidebarOpen}
          toggleSidebar={() => setSidebarOpen(false)}
          sessions={sessions}
          currentSessionId={sessionId}
          onSelectSession={handleSelectSession}
          onNewChat={handleNewChat}
          onDeleteSession={handleDeleteSession}
          onOpenKnowledgeBase={() => {
            setSidebarOpen(false);
            setKnowledgeModalOpen(true);
          }}
          systemStatus={systemStatus}
        />

        {/* Backdrop for mobile drawer */}
        {sidebarOpen && (
          <div
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 z-30 bg-black/60 backdrop-blur-xs transition-opacity"
          />
        )}

        {/* Center Chat Canvas */}
        <main className="flex-1 flex flex-col h-full overflow-hidden w-full max-w-4xl mx-auto">
          <ChatWindow
            messages={messages}
            isTyping={isTyping}
            sessionId={sessionId}
            onSelectPrompt={(prompt) => handleSendMessage(prompt)}
          />

          <InputBox
            userInput={userInput}
            setUserInput={setUserInput}
            handleSendMessage={handleSendMessage}
            isTyping={isTyping}
          />
        </main>
      </div>

      {/* Knowledge Base Inspector Modal */}
      <KnowledgeBaseModal
        isOpen={knowledgeModalOpen}
        onClose={() => setKnowledgeModalOpen(false)}
      />
    </div>
  );
}
