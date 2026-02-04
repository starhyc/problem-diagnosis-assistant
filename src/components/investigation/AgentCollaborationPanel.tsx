import { useEffect, useRef } from 'react';
import { Bot } from 'lucide-react';
import { AgentMessage } from '../../types/investigation';
import { Agent } from '../../types/agent';
import { cn } from '../../lib/utils';

interface AgentCollaborationPanelProps {
  messages: AgentMessage[];
  agents: Agent[];
  isRunning: boolean;
}

const messageTypeStyles: Record<string, string> = {
  info: 'border-l-text-muted',
  hypothesis: 'border-l-agent-knowledge',
  action: 'border-l-agent-log',
  evidence: 'border-l-semantic-success',
  decision: 'border-l-primary',
  error: 'border-l-semantic-danger',
};

export default function AgentCollaborationPanel({
  messages,
  agents,
  isRunning,
}: AgentCollaborationPanelProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0 && !isRunning) {
    return (
      <div className="h-full flex items-center justify-center text-text-muted">
        <div className="text-center">
          <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>输入问题描述后点击"开始诊断"</p>
          <p className="text-sm mt-2">Agent将协同分析问题</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {messages.map((msg) => {
        const agent = agents.find((a) => a.id === msg.agent);
        return (
          <div
            key={msg.id}
            className={cn(
              'border-l-4 bg-bg-surface/50 rounded-r-lg p-4 animate-fadeIn',
              messageTypeStyles[msg.type]
            )}
          >
            <div className="flex items-center gap-2 mb-2">
              <div
                className="w-6 h-6 rounded-full flex items-center justify-center"
                style={{ backgroundColor: agent?.color }}
              >
                <Bot className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm font-medium text-text-main">
                {agent?.name}
              </span>
              <span className="text-xs text-text-muted">{msg.timestamp}</span>
            </div>
            <div className="text-sm text-text-main whitespace-pre-wrap">
              {msg.content.includes('```') ? (
                <>
                  {msg.content.split('```')[0]}
                  <pre className="bg-bg-deep p-3 rounded-lg overflow-x-auto font-mono text-xs mt-2">
                    {msg.content.split('```')[1]?.replace(/^\w*\n/, '').replace(/```$/, '')}
                  </pre>
                </>
              ) : (
                msg.content
              )}
            </div>
          </div>
        );
      })}
      {isRunning && (
        <div className="flex items-center gap-2 text-text-muted p-4">
          <div className="w-4 h-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <span className="text-sm">Agent正在分析中...</span>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}
