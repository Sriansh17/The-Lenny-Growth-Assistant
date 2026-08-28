import React from 'react';
import { useStore } from '../hooks/useStore';

export function NewSessionButton() {
  const { createSession, selectSession } = useStore();
  const [isCreating, setIsCreating] = React.useState(false);

  const handleCreate = async () => {
    setIsCreating(true);
    try {
      const session = await createSession();
      await selectSession(session.id);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <button
      onClick={handleCreate}
      disabled={isCreating}
      className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 disabled:opacity-50 transition-all"
    >
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
      </svg>
      <span>New Chat</span>
    </button>
  );
}
