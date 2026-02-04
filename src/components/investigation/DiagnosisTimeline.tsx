import { Clock, Bot } from 'lucide-react';
import { TimelineStep } from '../../types/investigation';
import { Agent } from '../../types/agent';
import { statusIcons, statusColors } from '../../constants';
import { cn } from '../../lib/utils';

interface DiagnosisTimelineProps {
  timeline: TimelineStep[];
  agents: Agent[];
}

export default function DiagnosisTimeline({ timeline, agents }: DiagnosisTimelineProps) {
  if (timeline.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-text-muted">
        <div className="text-center">
          <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>暂无诊断步骤</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4">
      <div className="relative">
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border-subtle" />

        {timeline.map((step) => {
          const StatusIcon = statusIcons[step.status];
          const agent = agents.find((a) => a.id === step.agent);

          return (
            <div key={step.id} className="relative pl-12 pb-6">
              <div
                className={cn(
                  'absolute left-0 w-8 h-8 rounded-full border-2 flex items-center justify-center bg-bg-deep',
                  statusColors[step.status],
                  step.status === 'active' && 'glow-active'
                )}
              >
                <StatusIcon
                  className={cn(
                    'w-4 h-4',
                    step.status === 'active' && 'animate-spin'
                  )}
                />
              </div>

              <div className="bg-bg-surface/50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-text-main">
                    {step.step}
                  </h4>
                  <span className="text-xs text-text-muted">{step.duration}</span>
                </div>
                <p className="text-sm text-text-muted">{step.output}</p>
                <div
                  className="mt-2 text-xs flex items-center gap-1"
                  style={{ color: agent?.color }}
                >
                  <Bot className="w-3 h-3" />
                  {agent?.name}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
