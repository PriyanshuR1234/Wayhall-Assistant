import React, { useState } from 'react';
import { FaBookOpen, FaChevronDown, FaChevronUp, FaFileAlt } from 'react-icons/fa';

export const DOC_COLORS = {
  service_requests: {
    bg: 'bg-blue-950/60',
    border: 'border-blue-800/60',
    text: 'text-blue-300',
    badge: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    label: 'Service Requests',
  },
  bylaws: {
    bg: 'bg-amber-950/60',
    border: 'border-amber-800/60',
    text: 'text-amber-300',
    badge: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    label: 'Municipal By-laws',
  },
  permits: {
    bg: 'bg-emerald-950/60',
    border: 'border-emerald-800/60',
    text: 'text-emerald-300',
    badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    label: 'Permits & Licensing',
  },
};

function inferDocStyle(source = '') {
  const s = source.toLowerCase();
  if (s.includes('bylaw') || s.includes('noise')) return DOC_COLORS.bylaws;
  if (s.includes('permit') || s.includes('licens')) return DOC_COLORS.permits;
  return DOC_COLORS.service_requests;
}

export default function CitationCard({ citation, index }) {
  const [expanded, setExpanded] = useState(false);
  const style = inferDocStyle(citation.source);

  return (
    <div
      className={`rounded-xl border transition-all duration-200 overflow-hidden ${style.bg} ${style.border} hover:border-slate-500/50 shadow-sm`}
    >
      <div
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between p-2.5 px-3 cursor-pointer select-none text-xs"
      >
        <div className="flex items-center gap-2 flex-wrap">
          <span className="flex items-center gap-1 font-semibold text-slate-300">
            <FaBookOpen className="text-slate-400" size={11} />
            Citation [{index + 1}]
          </span>

          <span className={`px-2 py-0.5 rounded-full border text-[11px] font-medium ${style.badge}`}>
            {style.label}
          </span>

          <span className="bg-slate-800/80 text-slate-300 px-2 py-0.5 rounded text-[11px] font-mono border border-slate-700/60">
            Page {citation.page}
          </span>

          {citation.section && (
            <span className="text-slate-400 italic text-[11px] max-w-[180px] truncate" title={citation.section}>
              • {citation.section}
            </span>
          )}
        </div>

        <button
          className="text-slate-400 hover:text-white p-1 transition"
          aria-label={expanded ? 'Collapse citation' : 'Expand citation'}
        >
          {expanded ? <FaChevronUp size={10} /> : <FaChevronDown size={10} />}
        </button>
      </div>

      {expanded && (
        <div className="px-3 pb-3 pt-1 border-t border-slate-800/60 bg-slate-900/60 text-xs">
          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1.5">
            <span className="font-mono text-slate-400 truncate max-w-[80%]">
              <FaFileAlt className="inline mr-1 opacity-70" />
              Source: {citation.source}
            </span>
            <span className="text-slate-400 font-mono text-[10px]">ID: {citation.chunk_id}</span>
          </div>
          <div className="bg-slate-950/80 p-2.5 rounded-lg border border-slate-800/80 text-slate-200 leading-relaxed font-sans select-text">
            "{citation.snippet}"
          </div>
        </div>
      )}
    </div>
  );
}
