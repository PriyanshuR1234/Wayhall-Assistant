import React, { useState, useEffect } from 'react';
import {
  FaTimes,
  FaBook,
  FaDatabase,
  FaCheckCircle,
  FaExclamationCircle,
  FaLayerGroup,
  FaSearch,
} from 'react-icons/fa';
import { fetchDocuments, fetchDocumentChunks } from '../api/client';
import { DOC_COLORS } from './CitationCard';

export default function KnowledgeBaseModal({ isOpen, onClose }) {
  const [documents, setDocuments] = useState([]);
  const [selectedLabel, setSelectedLabel] = useState(null);
  const [chunks, setChunks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadDocs();
    }
  }, [isOpen]);

  const loadDocs = async () => {
    setLoading(true);
    const docs = await fetchDocuments();
    setDocuments(docs);
    if (docs.length > 0 && !selectedLabel) {
      setSelectedLabel(docs[0].doc_label);
      loadChunks(docs[0].doc_label);
    }
    setLoading(false);
  };

  const loadChunks = async (label) => {
    setSelectedLabel(label);
    const data = await fetchDocumentChunks(label);
    setChunks(data);
  };

  if (!isOpen) return null;

  const filteredChunks = chunks.filter(
    (c) =>
      c.snippet.toLowerCase().includes(searchFilter.toLowerCase()) ||
      (c.section && c.section.toLowerCase().includes(searchFilter.toLowerCase())) ||
      c.chunk_id.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-4xl h-[85vh] bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden text-slate-100">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 px-6 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <FaDatabase size={16} />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Municipal Knowledge Base Inspector
                <span className="text-xs font-mono font-normal bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                  Supabase pgvector (768d)
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Inspect indexed documents, section boundaries, and verified page numbers.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <FaTimes size={16} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex flex-1 overflow-hidden">
          {/* Document list tab */}
          <div className="w-72 border-r border-slate-800 bg-slate-950/40 p-4 space-y-2 overflow-y-auto">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
              Indexed Documents ({documents.length})
            </div>

            {documents.length === 0 && !loading && (
              <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-800/40 text-amber-300 text-xs text-center">
                <FaExclamationCircle className="mx-auto mb-2" size={18} />
                No PDFs indexed yet. Place PDFs in <code className="text-amber-200">backend/data/</code> and run the ingestion command.
              </div>
            )}

            {documents.map((doc) => {
              const active = selectedLabel === doc.doc_label;
              const style = DOC_COLORS[doc.doc_label] || DOC_COLORS.service_requests;
              return (
                <div
                  key={doc.doc_label}
                  onClick={() => loadChunks(doc.doc_label)}
                  className={`p-3 rounded-xl border cursor-pointer transition select-none ${
                    active
                      ? `${style.bg} ${style.border} shadow-sm`
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs font-semibold mb-1">
                    <span className={active ? style.text : 'text-slate-200'}>
                      {style.label}
                    </span>
                    <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded font-mono">
                      {doc.chunk_count} chunks
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 truncate mb-1.5" title={doc.source}>
                    {doc.source}
                  </p>
                  <div className="text-[10px] text-slate-400 flex items-center justify-between font-mono">
                    <span>Pages: {doc.page_min}–{doc.page_max}</span>
                    <span className="text-emerald-400 flex items-center gap-1 font-sans">
                      <FaCheckCircle size={9} /> Verified
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Chunks viewer */}
          <div className="flex-1 flex flex-col overflow-hidden bg-slate-900/40">
            {/* Filter bar */}
            <div className="p-3 px-5 border-b border-slate-800 bg-slate-900/80 flex items-center justify-between gap-4">
              <div className="relative flex-1 max-w-md">
                <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={12} />
                <input
                  type="text"
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  placeholder="Search inside retrieved chunks..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <span className="text-xs text-slate-400 font-mono">
                Showing {filteredChunks.length} of {chunks.length} chunks
              </span>
            </div>

            {/* Chunk cards list */}
            <div className="flex-1 overflow-y-auto p-5 space-y-3">
              {filteredChunks.length === 0 ? (
                <div className="text-center py-12 text-slate-400 text-xs">
                  {chunks.length === 0
                    ? 'Select a document on the left to preview its indexed passages.'
                    : 'No chunks matched your search term.'}
                </div>
              ) : (
                filteredChunks.map((chunk) => (
                  <div
                    key={chunk.chunk_id}
                    className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-slate-700 transition"
                  >
                    <div className="flex items-center justify-between text-xs mb-2 pb-1.5 border-b border-slate-800/80">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-emerald-400 font-semibold text-[11px]">
                          {chunk.chunk_id}
                        </span>
                        <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded text-[10px] font-mono">
                          Page {chunk.page}
                        </span>
                        {chunk.section && (
                          <span className="text-slate-400 text-[11px] italic truncate max-w-sm">
                            • {chunk.section}
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono">{chunk.source}</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed font-sans select-text">
                      {chunk.snippet}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
