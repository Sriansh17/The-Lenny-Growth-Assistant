import React from 'react';
import { useStore } from '../hooks/useStore';
import { MessageBubble } from './MessageBubble';

export function MessageList() {
  const { messages, isStreaming, currentSessionId, artifacts, setSelectedArtifact, setArtifactOpen } = useStore();
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!currentSessionId) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 mx-auto mb-6 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Lenny Growth Assistant</h2>
          <p className="text-gray-400 text-sm mb-8">
            Ask anything about product, growth, or startups — grounded in 269 episodes of Lenny's Podcast.
          </p>
          <div className="grid gap-2 text-left">
            <div className="px-4 py-3 bg-gray-800/50 rounded-xl border border-gray-800 hover:border-gray-700 transition-colors cursor-default">
              <p className="text-sm text-gray-300">"How does Gokul define product-market fit?"</p>
            </div>
            <div className="px-4 py-3 bg-gray-800/50 rounded-xl border border-gray-800 hover:border-gray-700 transition-colors cursor-default">
              <p className="text-sm text-gray-300">"Write a Ship 30 essay on retention strategies"</p>
            </div>
            <div className="px-4 py-3 bg-gray-800/50 rounded-xl border border-gray-800 hover:border-gray-700 transition-colors cursor-default">
              <p className="text-sm text-gray-300">"Create an HTML growth experiment template"</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 scrollbar-thin" role="log" aria-live="polite" aria-label="Chat messages">
      <div className="max-w-3xl mx-auto space-y-5">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {isStreaming && (
          <div className="flex items-center gap-2 text-sm text-gray-500 animate-pulse pl-11">
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-xs">Thinking...</span>
          </div>
        )}

        {artifacts.length > 0 && (
          <div className="mt-4 space-y-2">
            {artifacts.map((artifact) => (
              <button
                key={artifact.id}
                onClick={() => { setSelectedArtifact(artifact); setArtifactOpen(true); }}
                className="w-full text-left px-4 py-3 bg-emerald-900/30 border border-emerald-700/50 rounded-xl hover:bg-emerald-900/50 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span className="text-sm font-medium text-emerald-300">{artifact.title}</span>
                  <span className="text-[10px] px-1.5 py-0.5 bg-emerald-800/50 rounded text-emerald-400 uppercase">{artifact.type}</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">Click to view rendered artifact</p>
              </button>
            ))}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
