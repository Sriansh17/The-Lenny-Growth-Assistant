export interface Session {
  id: string;
  title: string | null;
  user_id: string | null;
  llm_provider: string;
  llm_model: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations: string | null;
  model_used: string | null;
  tokens_used: number | null;
  created_at: string;
}

export interface Artifact {
  id: string;
  session_id: string;
  type: 'markdown' | 'html';
  title: string;
  content: string;
  sanitized_content: string | null;
  created_at: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  use_skill?: string;
}

export interface ChatResponse {
  session_id: string;
  message: Message;
  artifacts: Artifact[];
}

export interface Skill {
  name: string;
  description: string;
  trigger_keywords: string[];
}

export interface HealthResponse {
  status: string;
  version: string;
  database: string;
  llm_provider: string;
  llm_model: string;
}