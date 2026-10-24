import React, { useRef, useEffect } from 'react';
import { FaPaperPlane, FaSpinner, FaLightbulb } from 'react-icons/fa';

const EXAMPLE_PROMPTS = [
  'What are the quiet hours and rules for residential noise?',
  'How do I report illegal dumping on city property?',
  'Do I need a building permit to construct a backyard deck?',
  'What is the standard response timeline for pothole repair?',
];

export default function InputBox({
  userInput,
  setUserInput,
  handleSendMessage,
  isTyping,
}) {
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 130)}px`;
    }
  }, [userInput]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (userInput.trim() && !isTyping) {
        handleSendMessage(userInput);
        setUserInput('');
      }
    }
  };

  const handleChipClick = (prompt) => {
    setUserInput(prompt);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto px-4 pb-4">
      {/* Quick Prompts Chips */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none text-[11.5px] select-none">
        <span className="text-slate-400 flex items-center gap-1 shrink-0 px-1 font-medium">
          <FaLightbulb className="text-amber-400" size={11} /> Suggested:
        </span>
        {EXAMPLE_PROMPTS.map((p, i) => (
          <button
            key={i}
            onClick={() => handleChipClick(p)}
            className="shrink-0 bg-slate-900/90 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 hover:border-slate-700 px-2.5 py-1 rounded-full transition shadow-sm truncate max-w-[240px]"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input container */}
      <div className="relative flex items-end bg-slate-900/95 border border-slate-800 hover:border-slate-700 focus-within:border-emerald-500/80 rounded-2xl p-2.5 shadow-xl transition backdrop-blur-md">
        <textarea
          ref={textareaRef}
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder="Ask a question about municipal services, by-laws, or permits... (Press Enter to send)"
          className="w-full bg-transparent text-slate-100 placeholder-slate-400 text-sm focus:outline-none resize-none px-3 py-1.5 max-h-32 overflow-y-auto leading-relaxed"
          disabled={isTyping}
        />

        <div className="flex items-center gap-2 shrink-0 pb-0.5">
          <button
            onClick={() => {
              if (userInput.trim() && !isTyping) {
                handleSendMessage(userInput);
                setUserInput('');
              }
            }}
            disabled={!userInput.trim() || isTyping}
            className={`p-2.5 rounded-xl transition flex items-center justify-center ${
              userInput.trim() && !isTyping
                ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-900/30'
                : 'bg-slate-800/80 text-slate-400 cursor-not-allowed'
            }`}
            aria-label="Send query"
          >
            {isTyping ? <FaSpinner className="animate-spin" size={14} /> : <FaPaperPlane size={13} />}
          </button>
        </div>
      </div>
      <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1.5 px-2">
        <span>Grounded on North American municipal documents • Refuses speculative answers</span>
        <span>Enter to send • Shift + Enter for new line</span>
      </div>
    </div>
  );
}
