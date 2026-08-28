import React from 'react';
import { useStore } from '../hooks/useStore';
import { SessionList } from './SessionList';
import { NewSessionButton } from './NewSessionButton';
import { ModelSelector } from './ModelSelector';
import { SkillList } from './SkillList';

export function Sidebar() {
  const { sidebarOpen, setSidebarOpen, sessions, currentSessionId, isLoading, fetchSessions } = useStore();

  React.useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  if (!sidebarOpen) return null;

  return (
    <>
      {/* Mobile overlay */}
      <div
        className="lg:hidden fixed inset-0 bg-black/60 z-30"
        onClick={() => setSidebarOpen(false)}
      />

      <aside className="fixed left-0 top-14 bottom-0 w-72 bg-gray-900 border-r border-gray-800 flex flex-col z-40 lg:relative lg:top-0 lg:z-auto">
        <div className="p-3">
          <NewSessionButton />
        </div>

        <div className="px-3 pb-3">
          <ModelSelector />
        </div>

        <div className="flex-1 overflow-y-auto px-3 scrollbar-thin">
          <SkillList />

          <div className="pt-3 mt-3 border-t border-gray-800">
            <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest mb-2 px-1">History</h3>
            <SessionList sessions={sessions} currentSessionId={currentSessionId} isLoading={isLoading} />
          </div>
        </div>

        <div className="p-3 border-t border-gray-800 text-[10px] text-gray-600">
          Powered by Lenny's Podcast transcripts
        </div>
      </aside>
    </>
  );
}
