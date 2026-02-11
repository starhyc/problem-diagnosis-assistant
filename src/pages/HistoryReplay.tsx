import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import AgentHierarchyTree from '../components/investigation/AgentHierarchyTree';
import ExecutionTimeline from '../components/investigation/ExecutionTimeline';
import GlobalTimeline from '../components/investigation/GlobalTimeline';
import { historyApi, HistoryEvent } from '../lib/api';
import { formatRiskLevel } from '../lib/riskLevel';
import { createReplayState, mapHistoryEventToDiagnosisEvent } from '../store/diagnosisStore';

function buildReplayView(events: HistoryEvent[], maxIndex: number, caseId?: string) {
  const normalizedEvents = events.map((event) =>
    mapHistoryEventToDiagnosisEvent(event.event_type, event.timestamp, (event.event_data || {}) as Record<string, unknown>),
  );

  return createReplayState(normalizedEvents, maxIndex, caseId);
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

  const replayView = useMemo(() => buildReplayView(events, playIndex, sessionId), [events, playIndex, sessionId]);
  const traces = replayView.traceMap;
  const rootAgentIds = replayView.rootAgentIds;

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
