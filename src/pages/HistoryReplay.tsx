import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import AgentHierarchyTree from '../components/investigation/AgentHierarchyTree';
import ExecutionTimeline from '../components/investigation/ExecutionTimeline';
import GlobalTimeline from '../components/investigation/GlobalTimeline';
import { historyApi, HistoryEvent } from '../lib/api';
import { formatRiskLevel } from '../lib/riskLevel';
import { AgentTrace, ExecutionStep } from '../types/trace';

function buildTraceMap(events: HistoryEvent[], maxIndex: number): Map<string, AgentTrace> {
  const traces = new Map<string, AgentTrace>();

  events.slice(0, Math.max(0, maxIndex + 1)).forEach((event) => {
    const data = event.event_data || {};
    if (event.event_type === 'agent_trace_start') {
      const agentId = data.agentId;
      if (!agentId) return;
      traces.set(agentId, {
        id: agentId,
        name: data.agentName || data.name || agentId,
        parentId: data.parentAgentId || null,
        status: 'running',
        startTime: data.timestamp || event.timestamp,
        model: data.model,
        costEstimate: 0,
        totalTokens: { input: 0, output: 0 },
        steps: [],
      });
    }

    if (event.event_type === 'agent_trace_step') {
      const agentId = data.agentId;
      const trace = traces.get(agentId);
      if (!trace) return;

      const step: ExecutionStep = {
        id: data.id || data.stepId || `${event.sequence}`,
        type: data.type || 'llm_thinking',
        timestamp: data.timestamp || event.timestamp,
        duration: data.duration,
        input: data.input,
        content: data.content,
        toolName: data.toolName,
        toolInput: data.toolInput,
        toolOutput: data.toolOutput,
        status: data.status,
        targetAgentId: data.targetAgentId,
        targetAgentName: data.targetAgentName,
        taskDescription: data.taskDescription,
      };

      trace.steps.push(step);
      trace.costEstimate = (trace.costEstimate || 0) + (data.costEstimate || 0);
    }

    if (event.event_type === 'agent_trace_complete') {
      const agentId = data.agentId;
      const trace = traces.get(agentId);
      if (!trace) return;
      trace.status = data.status === 'failed' ? 'failed' : 'success';
      trace.endTime = data.timestamp || event.timestamp;
      trace.duration = data.duration || trace.duration;
      trace.totalTokens = data.totalTokens || trace.totalTokens;
    }
  });

  return traces;
}

export default function HistoryReplay() {
  const { sessionId = '' } = useParams();
  const navigate = useNavigate();
  const [events, setEvents] = useState<HistoryEvent[]>([]);
  const [playIndex, setPlayIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

  useEffect(() => {
    historyApi.getSessionEvents(sessionId).then((data) => {
      setEvents(data);
      setPlayIndex(data.length > 0 ? data.length - 1 : 0);
    });
  }, [sessionId]);

  useEffect(() => {
    if (!playing) return;
    if (playIndex >= events.length - 1) {
      setPlaying(false);
      return;
    }

    const timer = setTimeout(() => setPlayIndex((idx) => Math.min(idx + 1, events.length - 1)), 700);
    return () => clearTimeout(timer);
  }, [playing, playIndex, events.length]);

  const traces = useMemo(() => buildTraceMap(events, playIndex), [events, playIndex]);
  const rootAgentIds = useMemo(() => Array.from(traces.values()).filter((t) => !t.parentId).map((t) => t.id), [traces]);

  useEffect(() => {
    if (!selectedAgentId && rootAgentIds.length > 0) {
      setSelectedAgentId(rootAgentIds[0]);
    }
  }, [rootAgentIds, selectedAgentId]);

  const selectedTrace = selectedAgentId ? traces.get(selectedAgentId) || null : null;
  const confirmationPoints = useMemo(
    () =>
      events
        .slice(0, Math.max(0, playIndex + 1))
        .filter((event) => ['confirmation_required', 'confirmation_gate_decision', 'confirmation_received'].includes(event.event_type))
        .map((event) => {
          const data = event.event_data || {};
          return {
            sequence: event.sequence,
            type: event.event_type,
            risk: formatRiskLevel((data.riskLevel || data.risk_level) as 'R0' | 'R1' | 'R2' | 'R3' | undefined),
            impactScope: data.impactScope || data.impact_scope || '-',
            rollbackPlan: data.rollbackPlan || data.rollback_plan || '-',
          };
        }),
    [events, playIndex],
  );

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-border-subtle bg-bg-surface flex items-center justify-between">
        <div>
          <button onClick={() => navigate('/history')} className="text-sm text-primary mb-2">← 返回历史列表</button>
          <h1 className="text-xl font-semibold text-text-main">回放视图</h1>
          <p className="text-xs text-text-muted font-mono">{sessionId}</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setPlaying((v) => !v)} className="px-3 py-2 bg-primary text-white rounded-lg">
            {playing ? '暂停' : '播放'}
          </button>
          <button onClick={() => setPlayIndex(0)} className="px-3 py-2 bg-bg-elevated rounded-lg">跳到开头</button>
          <button onClick={() => setPlayIndex(Math.max(events.length - 1, 0))} className="px-3 py-2 bg-bg-elevated rounded-lg">跳到末尾</button>
        </div>
      </div>

      <div className="px-4 py-3 border-b border-border-subtle bg-bg-surface/50">
        <input
          type="range"
          min={0}
          max={Math.max(events.length - 1, 0)}
          value={playIndex}
          onChange={(e) => setPlayIndex(Number(e.target.value))}
          className="w-full"
        />
        <div className="text-xs text-text-muted mt-1">节点 {Math.min(playIndex + 1, events.length)} / {events.length}</div>
      </div>


      <div className="px-4 py-3 border-b border-border-subtle bg-bg-surface/50">
        <h2 className="text-sm font-semibold mb-2">确认点信息（风险/影响范围/回滚方案）</h2>
        <div className="space-y-2 max-h-48 overflow-auto">
          {confirmationPoints.length === 0 && <div className="text-xs text-text-muted">当前进度暂无确认点</div>}
          {confirmationPoints.map((point) => (
            <div key={`${point.sequence}-${point.type}`} className="border rounded p-2 text-xs">
              <div className="font-medium">#{point.sequence} · {point.type} · 风险 {point.risk}</div>
              <div>影响范围：{point.impactScope}</div>
              <div>回滚方案：{point.rollbackPlan}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex-1 min-h-0 grid grid-cols-1 xl:grid-cols-3">
        <div className="border-r border-border-subtle">
          <AgentHierarchyTree traces={traces} rootAgentIds={rootAgentIds} selectedAgentId={selectedAgentId} onSelectAgent={setSelectedAgentId} />
        </div>
        <div className="xl:col-span-2 grid grid-rows-2 min-h-0">
          <div className="border-b border-border-subtle min-h-0 overflow-hidden">
            <ExecutionTimeline trace={selectedTrace} />
          </div>
          <div className="min-h-0 overflow-auto">
            <GlobalTimeline traces={traces} />
          </div>
        </div>
      </div>
    </div>
  );
}
