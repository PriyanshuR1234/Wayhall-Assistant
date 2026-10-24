import React from 'react';
import {
  FaPlus,
  FaTrash,
  FaComments,
  FaDatabase,
  FaCheckCircle,
  FaTimesCircle,
  FaTimes,
  FaShieldAlt,
} from 'react-icons/fa';

export default function Sidebar({
  isOpen,
  toggleSidebar,
  sessions,
  currentSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  onOpenKnowledgeBase,
  systemStatus,
}) {
  const isHealthy = systemStatus?.status === 'healthy';

  return (
    <div
      className={`fixed inset-y-0 left-0 z-40 w-72 bg-slate-950 border-r border-slate-800/80 transform transition-transform duration-300 ease-in-out flex flex-col ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
    >
      {/* Sidebar Header */}
      <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-bold text-xs shadow-sm">
            W
          </div>
          <div>
            <h1 className="text-sm font-bold text-white tracking-tight">Wayhall Civic AI</h1>
            <p className="text-[10px] text-slate-400">Municipal Knowledge Assistant</p>
          </div>
        </div>

        <button
          onClick={toggleSidebar}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 transition"
        >
          <FaTimes size={14} />
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs py-2.5 px-4 rounded-xl transition shadow-md shadow-emerald-950/40"
        >
          <FaPlus size={11} /> New Municipal Inquiry
        </button>
      </div>

      {/* Knowledge Base Inspector Action */}
      <div className="px-3 pb-2">
        <button
          onClick={onOpenKnowledgeBase}
          className="w-full flex items-center justify-between bg-slate-900/80 hover:bg-slate-850 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white text-xs py-2 px-3 rounded-xl transition"
        >
          <span className="flex items-center gap-2">
            <FaDatabase className="text-emerald-400" size={12} />
            Knowledge Base
          </span>
          <span className="text-[10px] font-mono bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">
            {systemStatus?.chunks_indexed || 0} chunks
          </span>
        </button>
      </div>

      {/* Session History List */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
        <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-2 py-1">
          Recent Sessions
        </div>

        {sessions.length === 0 ? (
          <div className="text-center py-6 text-slate-400 text-xs px-4">
            No saved sessions yet. Start asking questions to save conversations.
          </div>
        ) : (
          sessions.map((s) => {
            const active = currentSessionId === s.id;
            return (
              <div
                key={s.id}
                onClick={() => onSelectSession(s.id)}
                className={`group flex items-center justify-between p-2 px-2.5 rounded-xl cursor-pointer text-xs transition ${
                  active
                    ? 'bg-slate-800 text-white border border-slate-700'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <FaComments size={12} className={active ? 'text-emerald-400' : 'text-slate-400'} />
                  <span className="truncate">{s.title || `Inquiry ${s.id.slice(0, 8)}`}</span>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(s.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-rose-400 transition"
                  title="Delete session"
                >
                  <FaTrash size={11} />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Backend & DB Health Indicator Footer */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-950/80 text-xs text-slate-400">
        <div className="flex items-center justify-between mb-2">
          <span className="flex items-center gap-1.5 font-medium">
            <span
              className={`w-2 h-2 rounded-full ${
                isHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
              }`}
            />
            {isHealthy ? 'Backend Connected' : 'Backend Offline'}
          </span>
          <span className="font-mono text-[10px] text-slate-400">FastAPI :8000</span>
        </div>

        <div className="text-[10px] text-slate-400 flex items-center justify-between">
          <span>Database: {systemStatus?.db || 'unknown'}</span>
          <span>Gemini: {systemStatus?.gemini || 'unknown'}</span>
        </div>
      </div>
    </div>
  );
}
