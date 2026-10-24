import React, { useEffect, useRef } from 'react';
import {
  FaCity,
  FaFileInvoice,
  FaGavel,
  FaTools,
  FaShieldAlt,
  FaSearch,
} from 'react-icons/fa';
import MessageBubble from './MessageBubble';

export default function ChatWindow({
  messages,
  isTyping,
  sessionId,
  onSelectPrompt,
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-2xl mx-auto animate-fade-in select-none">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-500 border border-emerald-400/40 flex items-center justify-center text-white shadow-xl shadow-emerald-950/40 mb-4">
          <FaCity size={30} />
        </div>

        <h2 className="text-2xl font-bold text-white tracking-tight">
          Wayhall Civic Assistant
        </h2>
        <p className="text-sm text-slate-400 mt-1.5 max-w-md leading-relaxed">
          AI-powered answers grounded strictly in official municipal documents. Every response is verified with exact page numbers and document citations.
        </p>

        {/* 3 Core Documents Card Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 w-full mt-6 text-left">
          <div
            onClick={() =>
              onSelectPrompt?.('How do I report illegal dumping and what is the response timeline?')
            }
            className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-blue-500/50 hover:bg-slate-850 cursor-pointer transition group shadow-sm"
          >
            <div className="w-7 h-7 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center mb-2 group-hover:scale-105 transition">
              <FaTools size={13} />
            </div>
            <h3 className="text-xs font-bold text-slate-200">Service Requests</h3>
            <p className="text-[11px] text-slate-400 mt-1 leading-normal">
              Potholes, illegal dumping, waste collection, and municipal resolution timelines.
            </p>
          </div>

          <div
            onClick={() =>
              onSelectPrompt?.('What are the municipal quiet hours and rules for residential noise?')
            }
            className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-amber-500/50 hover:bg-slate-850 cursor-pointer transition group shadow-sm"
          >
            <div className="w-7 h-7 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center mb-2 group-hover:scale-105 transition">
              <FaGavel size={13} />
            </div>
            <h3 className="text-xs font-bold text-slate-200">Municipal By-laws</h3>
            <p className="text-[11px] text-slate-400 mt-1 leading-normal">
              Noise restrictions, property standards, parking regulations, and enforcement.
            </p>
          </div>

          <div
            onClick={() =>
              onSelectPrompt?.('When is a building permit required for home renovations or decks?')
            }
            className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-emerald-500/50 hover:bg-slate-850 cursor-pointer transition group shadow-sm"
          >
            <div className="w-7 h-7 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center mb-2 group-hover:scale-105 transition">
              <FaFileInvoice size={13} />
            </div>
            <h3 className="text-xs font-bold text-slate-200">Permits & Licensing</h3>
            <p className="text-[11px] text-slate-400 mt-1 leading-normal">
              Building permits, deck construction, licensing, and application review process.
            </p>
          </div>
        </div>

        {/* Anti-Hallucination Guardrail Note */}
        <div className="mt-6 flex items-center gap-2 text-xs text-slate-400 bg-slate-900/60 px-3.5 py-1.5 rounded-full border border-slate-800">
          <FaShieldAlt className="text-emerald-400" size={12} />
          <span>Strict Anti-Hallucination Guardrails: Uncovered topics are refused rather than guessed.</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 max-w-3xl w-full mx-auto scroll-smooth">
      {messages.map((msg, index) => (
        <MessageBubble
          key={index}
          message={msg}
          sessionId={sessionId}
          isTyping={false}
        />
      ))}

      {isTyping && (
        <MessageBubble
          message={{ isUserMessage: false }}
          sessionId={sessionId}
          isTyping={true}
        />
      )}

      <div ref={bottomRef} />
    </div>
  );
}
