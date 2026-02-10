import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { historyApi, HistorySession } from '../lib/api';

export default function History() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<HistorySession[]>([]);
  const [loading, setLoading] = useState(true);
  const [service, setService] = useState('');
  const [problemType, setProblemType] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [sortBy, setSortBy] = useState<'updated_at' | 'created_at' | 'confidence' | 'event_count'>('updated_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const loadSessions = useCallback(async () => {
    setLoading(true);
    try {
      const data = await historyApi.getSessions({
        service: service || undefined,
        problem_type: problemType || undefined,
        start_time: startTime || undefined,
        end_time: endTime || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setSessions(data);
    } finally {
      setLoading(false);
    }
  }, [service, problemType, startTime, endTime, sortBy, sortOrder]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const availableServices = useMemo(
    () => Array.from(new Set(sessions.map((s) => s.service).filter(Boolean))) as string[],
    [sessions],
  );

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-text-main">历史记录</h1>
        <button onClick={loadSessions} className="px-4 py-2 bg-primary text-white rounded-lg">刷新</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-6 gap-3 bg-bg-surface p-4 rounded-lg border border-border-subtle">
        <input value={startTime} onChange={(e) => setStartTime(e.target.value)} type="datetime-local" className="bg-bg-input p-2 rounded border border-border-subtle text-sm" />
        <input value={endTime} onChange={(e) => setEndTime(e.target.value)} type="datetime-local" className="bg-bg-input p-2 rounded border border-border-subtle text-sm" />
        <input value={problemType} onChange={(e) => setProblemType(e.target.value)} placeholder="问题类型" className="bg-bg-input p-2 rounded border border-border-subtle text-sm" />
        <select value={service} onChange={(e) => setService(e.target.value)} className="bg-bg-input p-2 rounded border border-border-subtle text-sm">
          <option value="">全部服务</option>
          {availableServices.map((item) => <option key={item} value={item}>{item}</option>)}
        </select>
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value as any)} className="bg-bg-input p-2 rounded border border-border-subtle text-sm">
          <option value="updated_at">更新时间</option>
          <option value="created_at">创建时间</option>
          <option value="confidence">置信度</option>
          <option value="event_count">事件数</option>
        </select>
        <div className="flex gap-2">
          <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')} className="bg-bg-input flex-1 p-2 rounded border border-border-subtle text-sm">
            <option value="desc">降序</option>
            <option value="asc">升序</option>
          </select>
          <button onClick={loadSessions} className="px-3 bg-bg-elevated rounded">检索</button>
        </div>
      </div>

      <div className="bg-bg-surface rounded-lg border border-border-subtle overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-bg-elevated text-text-muted">
            <tr>
              <th className="text-left p-3">会话</th>
              <th className="text-left p-3">服务</th>
              <th className="text-left p-3">问题类型</th>
              <th className="text-left p-3">阶段</th>
              <th className="text-left p-3">置信度</th>
              <th className="text-left p-3">事件数</th>
              <th className="text-left p-3">更新时间</th>
            </tr>
          </thead>
          <tbody>
            {!loading && sessions.length === 0 && <tr><td colSpan={7} className="p-6 text-center text-text-muted">暂无历史记录</td></tr>}
            {sessions.map((session) => (
              <tr key={session.session_id} className="border-t border-border-subtle hover:bg-bg-elevated/40 cursor-pointer" onClick={() => navigate(`/history/${session.session_id}`)}>
                <td className="p-3 font-mono">{session.session_id}</td>
                <td className="p-3">{session.service || '-'}</td>
                <td className="p-3">{session.problem_type || '-'}</td>
                <td className="p-3">{session.current_phase}</td>
                <td className="p-3">{session.confidence}%</td>
                <td className="p-3">{session.event_count}</td>
                <td className="p-3">{new Date(session.updated_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
