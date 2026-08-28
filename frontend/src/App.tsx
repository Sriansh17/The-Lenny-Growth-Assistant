import React from 'react';
import { Sidebar } from './components/Sidebar';
import { MessageList } from './components/MessageList';
import { ChatInput } from './components/ChatInput';
import { ArtifactViewer } from './components/ArtifactViewer';
import { useStore } from './hooks/useStore';

function Header() {
  const { sidebarOpen, setSidebarOpen, currentSessionId, sessions, llmProvider, llmModel, health } = useStore();
  const currentSession = sessions.find((s) => s.id === currentSessionId);

  return (
    <header className="h-14 flex-shrink-0 bg-gray-900/80 backdrop-blur-md border-b border-gray-800 flex items-center justify-between px-4">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {sidebarOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>

        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-emerald-500 rounded-lg flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z" />
            </svg>
          </div>
          <h1 className="text-sm font-semibold text-white hidden sm:block">Lenny Growth Assistant</h1>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {currentSession && (
          <span className="text-xs text-gray-500 truncate max-w-[200px] hidden md:block">
            {currentSession.title || 'New Chat'}
          </span>
        )}

        <div className="flex items-center gap-2">
          <span className="px-2 py-1 bg-gray-800 rounded-md text-xs text-gray-300 font-mono capitalize">{llmProvider}</span>
          <span className="px-2 py-1 bg-gray-800 rounded-md text-xs text-gray-400 font-mono hidden sm:inline">{llmModel}</span>
          <span className={`w-2 h-2 rounded-full ${health?.database === 'connected' ? 'bg-emerald-400' : 'bg-red-400'}`} />
        </div>
      </div>
    </header>
  );
}

export function App() {
  const { fetchHealth, fetchSkills, fetchSessions, artifactOpen, selectedArtifact, setArtifactOpen } = useStore();

  React.useEffect(() => {
    fetchHealth();
    fetchSkills();
    fetchSessions();
  }, [fetchHealth, fetchSkills, fetchSessions]);

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-gray-950">
      <Header />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <MessageList />
          <ChatInput />
        </main>
        {artifactOpen && selectedArtifact && (
          <aside className="hidden lg:flex w-[45%] max-w-2xl border-l border-gray-800 bg-gray-900 flex-col overflow-hidden">
            <ArtifactViewer
              artifact={selectedArtifact}
              onClose={() => setArtifactOpen(false)}
            />
          </aside>
        )}
      </div>
    </div>
  );
}
