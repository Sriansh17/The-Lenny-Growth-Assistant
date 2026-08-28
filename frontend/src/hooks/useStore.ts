import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Session, Message, Artifact, Skill, HealthResponse } from '../types';
import { api } from '../utils/api';

interface AppState {
  // Sessions
  sessions: Session[];
  currentSessionId: string | null;
  messages: Message[];
  artifacts: Artifact[];
  
  // UI State
  isLoading: boolean;
  isStreaming: boolean;
  sidebarOpen: boolean;
  artifactOpen: boolean;
  selectedArtifact: Artifact | null;
  
  // System
  health: HealthResponse | null;
  skills: Skill[];
  llmProvider: string;
  llmModel: string;
  
  // Actions
  setSidebarOpen: (open: boolean) => void;
  setArtifactOpen: (open: boolean) => void;
  setSelectedArtifact: (artifact: Artifact | null) => void;
  setLlmProvider: (provider: string) => void;
  setLlmModel: (model: string) => void;
  
  // Session actions
  fetchSessions: () => Promise<void>;
  createSession: (title?: string) => Promise<Session>;
  selectSession: (id: string) => Promise<void>;
  deleteSession: (id: string) => Promise<void>;
  updateSessionTitle: (id: string, title: string) => Promise<void>;
  
  // Chat actions
  sendMessage: (message: string, useSkill?: string) => Promise<void>;
  clearMessages: () => void;
  
  // Artifact actions
  fetchArtifacts: (sessionId: string) => Promise<void>;
  
  // System actions
  fetchHealth: () => Promise<void>;
  fetchSkills: () => Promise<void>;
  
  // Optimistic updates
  addOptimisticMessage: (message: Message) => void;
  updateLastMessage: (content: string) => void;
}

export const useStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Initial state
      sessions: [],
      currentSessionId: null,
      messages: [],
      artifacts: [],
      isLoading: false,
      isStreaming: false,
      sidebarOpen: true,
      artifactOpen: false,
      selectedArtifact: null,
      health: null,
      skills: [],
      llmProvider: 'ollama',
      llmModel: 'llama3.1:8b',

      // UI Actions
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setArtifactOpen: (open) => set({ artifactOpen: open, selectedArtifact: open ? get().selectedArtifact : null }),
      setSelectedArtifact: (artifact) => set({ selectedArtifact: artifact, artifactOpen: !!artifact }),
      setLlmProvider: (provider) => set({ llmProvider: provider }),
      setLlmModel: (model) => set({ llmModel: model }),

      // Session Actions
      fetchSessions: async () => {
        try {
          const sessions = await api.listSessions();
          set({ sessions });
        } catch (error) {
          console.error('Failed to fetch sessions:', error);
        }
      },

      createSession: async (title) => {
        set({ isLoading: true });
        try {
          const session = await api.createSession({
            title,
            llm_provider: get().llmProvider,
            llm_model: get().llmModel,
          });
          set((state) => ({ sessions: [session, ...state.sessions] }));
          return session;
        } finally {
          set({ isLoading: false });
        }
      },

      selectSession: async (id) => {
        set({ isLoading: true, currentSessionId: id });
        try {
          const sessionData = await api.getSession(id);
          set({ 
            messages: sessionData.messages,
            currentSessionId: id,
          });
          await get().fetchArtifacts(id);
        } catch (error) {
          console.error('Failed to load session:', error);
        } finally {
          set({ isLoading: false });
        }
      },

      deleteSession: async (id) => {
        try {
          await api.deleteSession(id);
          set((state) => ({
            sessions: state.sessions.filter((s) => s.id !== id),
            currentSessionId: state.currentSessionId === id ? null : state.currentSessionId,
            messages: state.currentSessionId === id ? [] : state.messages,
          }));
        } catch (error) {
          console.error('Failed to delete session:', error);
        }
      },

      updateSessionTitle: async (id, title) => {
        try {
          await api.updateSession(id, { title });
          set((state) => ({
            sessions: state.sessions.map((s) => (s.id === id ? { ...s, title } : s)),
          }));
        } catch (error) {
          console.error('Failed to update session:', error);
        }
      },

      // Chat Actions
      sendMessage: async (message, useSkill) => {
        const { currentSessionId, addOptimisticMessage } = get();
        
        if (!currentSessionId) {
          const session = await get().createSession();
          set({ currentSessionId: session.id });
        }

        const sessionId = get().currentSessionId!;
        set({ isStreaming: true });

        // Auto-title the session from first message
        const currentSession = get().sessions.find((s) => s.id === sessionId);
        if (currentSession && !currentSession.title) {
          const title = message.length > 50 ? message.slice(0, 50) + '...' : message;
          get().updateSessionTitle(sessionId, title);
        }

        // Add optimistic user message
        const userMessage: Message = {
          id: crypto.randomUUID(),
          session_id: sessionId,
          role: 'user',
          content: message,
          citations: null,
          model_used: null,
          tokens_used: null,
          created_at: new Date().toISOString(),
        };
        addOptimisticMessage(userMessage);

        // Use skill endpoint (non-streaming) for skill requests
        if (useSkill) {
          try {
            const response = await api.chat({
              message,
              session_id: sessionId,
              use_skill: useSkill,
            });

            // Add assistant message
            set((state) => ({
              messages: [...state.messages, response.message],
              sessions: state.sessions.map((s) => 
                s.id === sessionId ? { ...s, message_count: s.message_count + 2 } : s
              ),
            }));

            if (response.artifacts.length > 0) {
              set((state) => ({ artifacts: [...state.artifacts, ...response.artifacts] }));
              if (!get().artifactOpen && response.artifacts[0]) {
                set({ selectedArtifact: response.artifacts[0], artifactOpen: true });
              }
            }
          } catch (error) {
            console.error('Chat error:', error);
            set((state) => ({
              messages: state.messages.filter((m) => m.id !== userMessage.id),
            }));
          } finally {
            set({ isStreaming: false });
          }
          return;
        }

        // Streaming path for regular chat
        const assistantMessage: Message = {
          id: crypto.randomUUID(),
          session_id: sessionId,
          role: 'assistant',
          content: '',
          citations: null,
          model_used: null,
          tokens_used: null,
          created_at: new Date().toISOString(),
        };
        set((state) => ({ messages: [...state.messages, assistantMessage] }));

        try {
          const response = await fetch('/api/v1/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, session_id: sessionId }),
          });

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
          }

          const reader = response.body?.getReader();
          const decoder = new TextDecoder();
          let fullContent = '';
          let citations = '';

          if (reader) {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              const text = decoder.decode(value, { stream: true });
              const lines = text.split('\n');

              for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const data = line.slice(6).trim();
                if (!data) continue;

                try {
                  const event = JSON.parse(data);
                  
                  if (event.type === 'chunk') {
                    fullContent += event.content;
                    // Update the assistant message in place
                    set((state) => ({
                      messages: state.messages.map((m) =>
                        m.id === assistantMessage.id ? { ...m, content: fullContent } : m
                      ),
                    }));
                  } else if (event.type === 'citations') {
                    citations = event.citations;
                  } else if (event.type === 'done') {
                    // Final update with citations appended
                    const finalContent = citations
                      ? `${fullContent}\n\n**Sources:**\n${citations}`
                      : fullContent;
                    set((state) => ({
                      messages: state.messages.map((m) =>
                        m.id === assistantMessage.id
                          ? { ...m, content: finalContent, citations }
                          : m
                      ),
                      sessions: state.sessions.map((s) =>
                        s.id === sessionId ? { ...s, message_count: s.message_count + 2 } : s
                      ),
                    }));
                  } else if (event.type === 'error') {
                    set((state) => ({
                      messages: state.messages.map((m) =>
                        m.id === assistantMessage.id
                          ? { ...m, content: `Error: ${event.message}` }
                          : m
                      ),
                    }));
                  } else if (event.type === 'artifact') {
                    const artifact = event.artifact;
                    set((state) => ({
                      artifacts: [...state.artifacts, artifact],
                      selectedArtifact: artifact,
                      artifactOpen: true,
                    }));
                  }
                } catch {
                  // Skip malformed JSON lines
                }
              }
            }
          }
        } catch (error) {
          console.error('Stream error:', error);
          // Fallback to non-streaming endpoint
          try {
            const response = await api.chat({ message, session_id: sessionId });
            set((state) => ({
              messages: state.messages.map((m) =>
                m.id === assistantMessage.id ? response.message : m
              ),
            }));
          } catch (fallbackError) {
            set((state) => ({
              messages: state.messages.filter(
                (m) => m.id !== userMessage.id && m.id !== assistantMessage.id
              ),
            }));
          }
        } finally {
          set({ isStreaming: false });
        }
      },

      clearMessages: () => set({ messages: [] }),

      addOptimisticMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
      updateLastMessage: (content) => set((state) => {
        const messages = [...state.messages];
        const lastIdx = messages.findLastIndex((m) => m.role === 'assistant');
        if (lastIdx >= 0) {
          messages[lastIdx] = { ...messages[lastIdx], content };
        }
        return { messages };
      }),

      // Artifact Actions
      fetchArtifacts: async (sessionId) => {
        try {
          const artifacts = await api.getArtifacts(sessionId);
          set({ artifacts });
          // Auto-open the most recent artifact if any exist
          if (artifacts.length > 0) {
            set({ selectedArtifact: artifacts[artifacts.length - 1], artifactOpen: true });
          }
        } catch (error) {
          console.error('Failed to fetch artifacts:', error);
        }
      },

      // System Actions
      fetchHealth: async () => {
        try {
          const health = await api.health();
          set({ health, llmProvider: health.llm_provider, llmModel: health.llm_model });
        } catch (error) {
          console.error('Failed to fetch health:', error);
        }
      },

      fetchSkills: async () => {
        try {
          const skills = await api.listSkills();
          set({ skills });
        } catch (error) {
          console.error('Failed to fetch skills:', error);
        }
      },
    }),
    {
      name: 'lenny-assistant-store',
      partialize: (state) => ({
        llmProvider: state.llmProvider,
        llmModel: state.llmModel,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
);