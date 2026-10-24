import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  FaUser,
  FaRobot,
  FaThumbsUp,
  FaThumbsDown,
  FaCheckCircle,
  FaExclamationTriangle,
  FaLayerGroup,
} from 'react-icons/fa';
import CitationCard, { DOC_COLORS } from './CitationCard';
import TypingIndicator from './TypingIndicator';
import { submitFeedback } from '../api/client';

export default function MessageBubble({ message, sessionId, isTyping }) {
  const [feedbackSent, setFeedbackSent] = useState(null);

  const handleRating = async (isHelpful) => {
    if (feedbackSent !== null) return;
    setFeedbackSent(isHelpful);
    await submitFeedback({
      sessionId: sessionId || 'default',
      helpful: isHelpful,
      rating: isHelpful ? 5 : 1,
    });
  };

  if (isTyping) {
    return (
      <div className="flex items-start gap-3 w-full max-w-3xl py-3 px-2">
        <div className="w-8 h-8 rounded-lg bg-emerald-600/30 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shrink-0 shadow-sm">
          <FaRobot size={15} />
        </div>
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 px-5 text-slate-300 shadow-md">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-emerald-400 tracking-wide">
              Wayhall Civic AI
            </span>
            <span className="text-[10px] text-slate-400">Verifying municipal documents...</span>
          </div>
          <TypingIndicator />
        </div>
      </div>
    );
  }

  const {
    text = '',
    isUserMessage = false,
    timestamp = '',
    citations = [],
    unsupported_parts = [],
    retrieval_doc_labels = [],
  } = message;

  if (isUserMessage) {
    return (
      <div className="flex justify-end w-full py-2">
        <div className="flex items-end gap-2.5 max-w-2xl">
          <div className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white p-3.5 px-4 rounded-2xl rounded-br-sm shadow-md text-sm leading-relaxed">
            <p className="whitespace-pre-wrap">{text}</p>
            <div className="text-[10px] text-emerald-100/80 text-right mt-1 font-mono">
              {timestamp}
            </div>
          </div>
          <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0 text-xs shadow-sm">
            <FaUser size={11} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3.5 w-full max-w-3xl py-3 group">
      <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-emerald-600/40 to-teal-700/30 border border-emerald-500/50 flex items-center justify-center text-emerald-400 shrink-0 shadow-sm mt-0.5">
        <FaRobot size={16} />
      </div>

      <div className="flex-1 bg-slate-900/95 border border-slate-800/90 rounded-2xl p-4.5 px-5 shadow-lg text-slate-100">
        {/* Assistant Header */}
        <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800/80 text-xs">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-bold text-emerald-400 tracking-tight flex items-center gap-1.5">
              Wayhall Assistant
              <FaCheckCircle className="text-emerald-500 text-[10px]" title="Strictly Grounded" />
            </span>

            {/* Document Badges */}
            {retrieval_doc_labels && retrieval_doc_labels.length > 0 && (
              <div className="flex items-center gap-1.5 ml-2">
                <FaLayerGroup className="text-slate-400 text-[10px]" />
                {retrieval_doc_labels.map((lbl) => {
                  const style = DOC_COLORS[lbl] || DOC_COLORS.service_requests;
                  return (
                    <span
                      key={lbl}
                      className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${style.badge}`}
                    >
                      {style.label}
                    </span>
                  );
                })}
              </div>
            )}
          </div>

          <span className="text-[11px] text-slate-400 font-mono">{timestamp}</span>
        </div>

        {/* Markdown Content */}
        <div className="prose prose-invert prose-sm max-w-none text-slate-200 leading-relaxed text-[13.5px]">
          <ReactMarkdown>{text}</ReactMarkdown>
        </div>

        {/* Unsupported Parts Disclaimer */}
        {unsupported_parts && unsupported_parts.length > 0 && (
          <div className="mt-3.5 p-3 rounded-xl bg-amber-950/40 border border-amber-800/50 text-amber-200/90 text-xs flex items-start gap-2.5">
            <FaExclamationTriangle className="text-amber-400 shrink-0 mt-0.5" size={13} />
            <div>
              <p className="font-semibold text-amber-300">Document Gap Notice:</p>
              <p className="text-amber-200/80 mt-0.5">
                The supplied municipal documents do not contain information on:{' '}
                <span className="font-medium underline underline-offset-2">
                  {unsupported_parts.join(', ')}
                </span>
                . In accordance with municipal guidelines, no speculative answers were invented.
              </p>
            </div>
          </div>
        )}

        {/* Verified Citations List */}
        {citations && citations.length > 0 && (
          <div className="mt-4 pt-3 border-t border-slate-800/70">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>Verified Citations ({citations.length})</span>
              <span className="text-[10px] lowercase text-slate-400 font-normal">
                Click any citation to view page snippet
              </span>
            </div>
            <div className="space-y-1.5">
              {citations.map((cit, idx) => (
                <CitationCard key={cit.chunk_id || idx} citation={cit} index={idx} />
              ))}
            </div>
          </div>
        )}

        {/* Helpful Feedback Bar */}
        <div className="flex items-center justify-between mt-3.5 pt-2 border-t border-slate-800/40 text-[11px] text-slate-400">
          <span>Was this municipal information accurate & helpful?</span>
          <div className="flex items-center gap-2">
            {feedbackSent !== null ? (
              <span className="text-emerald-400 text-xs font-medium flex items-center gap-1">
                <FaCheckCircle size={11} /> Feedback recorded
              </span>
            ) : (
              <>
                <button
                  onClick={() => handleRating(true)}
                  className="p-1.5 px-2 rounded-md hover:bg-slate-800 hover:text-emerald-400 transition flex items-center gap-1"
                  title="Helpful & verified"
                >
                  <FaThumbsUp size={11} /> Yes
                </button>
                <button
                  onClick={() => handleRating(false)}
                  className="p-1.5 px-2 rounded-md hover:bg-slate-800 hover:text-rose-400 transition flex items-center gap-1"
                  title="Not helpful or inaccurate"
                >
                  <FaThumbsDown size={11} /> No
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
