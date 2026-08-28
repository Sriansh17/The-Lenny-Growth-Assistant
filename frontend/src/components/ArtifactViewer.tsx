import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import type { Artifact } from '../types';

interface ArtifactViewerProps {
  artifact: Artifact;
  onClose: () => void;
}

export function ArtifactViewer({ artifact, onClose }: ArtifactViewerProps) {
  const [viewMode, setViewMode] = React.useState<'render' | 'source'>('render');

  const renderArtifact = () => {
    if (artifact.type === 'markdown') {
      return (
        <div className="prose prose-sm max-w-none p-6 text-gray-200">
          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
            {artifact.content}
          </ReactMarkdown>
        </div>
      );
    }

    return (
      <iframe
        className="w-full flex-1 border-0 bg-white rounded-lg"
        sandbox="allow-scripts allow-same-origin"
        srcDoc={artifact.sanitized_content || artifact.content}
        title={artifact.title}
      />
    );
  };

  const renderSource = () => (
    <pre className="flex-1 bg-gray-950 text-gray-300 p-4 overflow-auto text-xs font-mono">
      <code>{artifact.type === 'markdown' ? artifact.content : artifact.sanitized_content || artifact.content}</code>
    </pre>
  );

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-gray-800">
        <div className="flex items-center gap-2 min-w-0">
          <h3 className="text-sm font-medium text-white truncate">{artifact.title}</h3>
          <span className="px-1.5 py-0.5 text-[10px] font-medium bg-gray-800 text-gray-400 rounded capitalize flex-shrink-0">
            {artifact.type}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex bg-gray-800 rounded-lg p-0.5">
            <button
              onClick={() => setViewMode('render')}
              className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                viewMode === 'render' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              Render
            </button>
            <button
              onClick={() => setViewMode('source')}
              className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                viewMode === 'source' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              Source
            </button>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-500 hover:text-white hover:bg-gray-800 transition-colors"
            aria-label="Close artifact"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {viewMode === 'render' ? renderArtifact() : renderSource()}
      </div>
    </div>
  );
}
