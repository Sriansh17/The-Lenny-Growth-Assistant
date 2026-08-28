import React from 'react';
import { useStore } from '../hooks/useStore';
import type { Session } from '../types';
import { formatDistanceToNow } from 'date-fns';

interface SessionListProps {
  sessions: Session[];
  currentSessionId: string | null;
  isLoading: boolean;
}

export function SessionList({ sessions, currentSessionId, isLoading }: SessionListProps) {
  const { selectSession, deleteSession, updateSessionTitle } = useStore();

  if (isLoading && sessions.length === 0) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-10 animate-pulse bg-gray-800 rounded-lg" />
        ))}
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <p className="text-xs text-gray-600 text-center py-3">
        No sessions yet
      </p>
    );
  }

  return (
    <div className="space-y-0.5">
      {sessions.map((session) => (
        <SessionItem
          key={session.id}
          session={session}
          isActive={session.id === currentSessionId}
          onSelect={selectSession}
          onDelete={deleteSession}
          onUpdateTitle={updateSessionTitle}
        />
      ))}
    </div>
  );
}

function SessionItem({
  session,
  isActive,
  onSelect,
  onDelete,
}: {
  session: Session;
  isActive: boolean;
  onSelect: (id: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onUpdateTitle: (id: string, title: string) => Promise<void>;
}) {
  const formatDate = (dateStr: string) => {
    try {
      // Backend returns UTC timestamps without timezone suffix
      const utcDate = dateStr.endsWith('Z') ? new Date(dateStr) : new Date(dateStr + 'Z');
      return formatDistanceToNow(utcDate, { addSuffix: true });
    } catch {
      return '';
    }
  };

  return (
    <div className="group relative">
      <button
        onClick={() => onSelect(session.id)}
        className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
          isActive
            ? 'bg-gray-800 text-white'
            : 'text-gray-400 hover:bg-gray-800/50 hover:text-gray-200'
        }`}
      >
        <p className="truncate text-xs font-medium">{session.title || 'Untitled'}</p>
        <p className="text-[10px] text-gray-600 mt-0.5">
          {session.message_count} msgs · {formatDate(session.updated_at)}
        </p>
      </button>

      <button
        onClick={(e) => {
          e.stopPropagation();
          if (confirm('Delete this session?')) onDelete(session.id);
        }}
        className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-500/20 text-gray-600 hover:text-red-400 transition-all"
        aria-label="Delete session"
      >
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>
    </div>
  );
}
