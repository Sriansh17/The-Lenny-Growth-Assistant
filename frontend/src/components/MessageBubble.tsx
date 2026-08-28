import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import type { Message } from '../types';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold ${
          isUser ? 'bg-gray-700 text-gray-300' : 'bg-emerald-500/20 text-emerald-400'
        }`}
        aria-hidden="true"
      >
        {isUser ? 'U' : 'L'}
      </div>

      <div className={`flex-1 min-w-0 max-w-[85%] ${isUser ? 'flex flex-col items-end' : ''}`}>
        <div
          className={`inline-block px-4 py-2.5 rounded-2xl text-sm ${
            isUser
              ? 'bg-emerald-600 text-white rounded-tr-md'
              : 'bg-gray-800 text-gray-200 rounded-tl-md border border-gray-700'
          }`}
        >
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw]}
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                code: ({ children, className, ...props }) => {
                  const isInline = !className;
                  if (isInline) {
                    return <code className="bg-gray-900/50 px-1 py-0.5 rounded text-xs font-mono text-emerald-400">{children}</code>;
                  }
                  return (
                    <pre className="bg-gray-900 text-gray-100 p-3 rounded-lg overflow-x-auto text-xs my-2 border border-gray-700">
                      <code>{children}</code>
                    </pre>
                  );
                },
                a: ({ href, children }) => (
                  <a href={href} target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:text-emerald-300 underline">
                    {children}
                  </a>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        </div>

        {message.citations && !isUser && (
          <details className="mt-1.5 group">
            <summary className="flex items-center gap-1 text-[10px] text-gray-500 hover:text-gray-400 cursor-pointer list-none">
              <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <span>Sources ({message.citations.split('\n').filter(Boolean).length})</span>
            </summary>
            <div className="mt-1 ml-4 text-[11px] text-gray-500 whitespace-pre-line border-l border-gray-700 pl-3">
              {message.citations}
            </div>
          </details>
        )}

        <div className={`mt-1 text-[10px] text-gray-600 ${isUser ? 'text-right' : ''}`}>
          {message.created_at && (
            <time dateTime={message.created_at}>
              {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </time>
          )}
          {message.model_used && (
            <span className="ml-2 px-1.5 py-0.5 bg-gray-800 rounded text-gray-500 font-mono">
              {message.model_used}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
