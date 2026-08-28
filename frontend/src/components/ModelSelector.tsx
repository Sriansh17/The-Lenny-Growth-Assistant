import React from 'react';
import { useStore } from '../hooks/useStore';

const PROVIDERS = [
  { id: 'ollama', name: 'Ollama (Local)', models: ['llama3.1:8b', 'llama3.1:70b', 'mistral:7b'] },
  { id: 'anthropic', name: 'Anthropic', models: ['claude-sonnet-4-20250514', 'claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307'] },
  { id: 'openai', name: 'OpenAI', models: ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'] },
];

export function ModelSelector() {
  const { llmProvider, llmModel, setLlmProvider, setLlmModel, health } = useStore();

  const provider = PROVIDERS.find((p) => p.id === llmProvider) || PROVIDERS[0];
  const isHealthy = health?.database === 'connected';

  return (
    <div className="space-y-2 p-3 bg-gray-800/50 rounded-xl border border-gray-800">
      <label className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest">Model</label>

      <select
        value={llmProvider}
        onChange={(e) => {
          const newProvider = e.target.value;
          setLlmProvider(newProvider);
          const p = PROVIDERS.find((p) => p.id === newProvider);
          if (p) setLlmModel(p.models[0]);
        }}
        className="w-full px-3 py-1.5 text-xs bg-gray-800 border border-gray-700 rounded-lg text-gray-300 focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
      >
        {PROVIDERS.map((p) => (
          <option key={p.id} value={p.id}>{p.name}</option>
        ))}
      </select>

      <select
        value={llmModel}
        onChange={(e) => setLlmModel(e.target.value)}
        className="w-full px-3 py-1.5 text-xs bg-gray-800 border border-gray-700 rounded-lg text-gray-300 focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
      >
        {provider.models.map((model) => (
          <option key={model} value={model}>{model}</option>
        ))}
      </select>

      <div className="flex items-center gap-1.5 text-[10px]">
        <span className={`w-1.5 h-1.5 rounded-full ${isHealthy ? 'bg-emerald-400' : 'bg-red-400'}`} />
        <span className={isHealthy ? 'text-emerald-400' : 'text-red-400'}>
          {isHealthy ? 'Connected' : 'Disconnected'}
        </span>
      </div>
    </div>
  );
}
