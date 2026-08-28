import React from 'react';
import { useStore } from '../hooks/useStore';

export function ChatInput() {
  const { currentSessionId, sendMessage, isStreaming, isLoading, skills } = useStore();
  const [input, setInput] = React.useState('');
  const [showSkills, setShowSkills] = React.useState(false);
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const message = input.trim();
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = '44px';
    }
    sendMessage(message);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = '44px';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  return (
    <div className="flex-shrink-0 border-t border-gray-800 bg-gray-900/50 backdrop-blur-sm p-3">
      <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
        <div className="relative flex items-end gap-2 bg-gray-800 rounded-xl border border-gray-700 focus-within:border-emerald-500/50 focus-within:ring-1 focus-within:ring-emerald-500/20 transition-all">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder={currentSessionId ? "Ask about product, growth, startups..." : "Start a new chat to begin..."}
            disabled={isStreaming || isLoading || !currentSessionId}
            className="flex-1 bg-transparent text-gray-100 placeholder-gray-500 px-4 py-3 text-sm resize-none focus:outline-none min-h-[44px] max-h-[120px]"
            rows={1}
            aria-label="Message input"
          />

          <div className="flex items-center gap-1 px-2 pb-2">
            <button
              type="button"
              onClick={() => setShowSkills(!showSkills)}
              className="p-1.5 rounded-lg text-gray-500 hover:text-emerald-400 hover:bg-gray-700 transition-colors"
              aria-label="Show skills"
              aria-expanded={showSkills}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </button>

            <button
              type="submit"
              disabled={!input.trim() || isStreaming || isLoading || !currentSessionId}
              className="p-1.5 rounded-lg bg-emerald-500 text-white hover:bg-emerald-400 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              aria-label="Send message"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
          </div>

          {showSkills && skills.length > 0 && (
            <div className="absolute bottom-full left-0 right-0 mb-2 p-2 bg-gray-800 border border-gray-700 rounded-xl shadow-2xl z-10">
              <p className="px-2 py-1 text-[10px] font-medium text-gray-500 uppercase tracking-wider">Skills</p>
              {skills.map((skill) => (
                <button
                  key={skill.name}
                  type="button"
                  onClick={() => {
                    setInput(`/skill ${skill.name} `);
                    setShowSkills(false);
                    textareaRef.current?.focus();
                  }}
                  className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <span className="font-medium text-emerald-400">{skill.name}</span>
                  <span className="text-gray-500 ml-2 text-xs">{skill.description}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <p className="mt-1.5 text-[10px] text-gray-600 text-center">
          <kbd className="px-1 py-0.5 bg-gray-800 rounded text-gray-500 font-mono">Enter</kbd> to send
          <span className="mx-1.5 text-gray-700">|</span>
          <kbd className="px-1 py-0.5 bg-gray-800 rounded text-gray-500 font-mono">Shift+Enter</kbd> new line
        </p>
      </form>
    </div>
  );
}
