import { useEffect } from 'react';
import { useDashboard } from '../hooks/useDashboard';
import { StatCard, CaseList, SystemHealthCard } from '../components/dashboard';

export default function Dashboard() {
  const { data, loading, error, refreshData } = useDashboard();

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-12 h-12 mx-auto mb-4 border-4 border-primary border-t-transparent rounded-full" />
          <p className="text-text-muted">加载中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-semantic-danger mb-2">加载失败</p>
          <p className="text-sm text-text-muted">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text-main">仪表盘</h1>
        <button
          onClick={refreshData}
          className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors"
        >
          刷新数据
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="活跃任务"
          value={data?.stats.active_tasks || 0}
          icon={<div className="w-6 h-6 text-semantic-warning">📊</div>}
        />
        <StatCard
          title="成功率"
          value={`${data?.stats.success_rate || 0}%`}
          icon={<div className="w-6 h-6 text-semantic-success">✓</div>}
          trend={{ value: 5, isPositive: true }}
        />
        <StatCard
          title="平均解决时间"
          value={data?.stats.avg_resolution_time || '0s'}
          icon={<div className="w-6 h-6 text-primary">⏱</div>}
        />
        <StatCard
          title="总案例数"
          value={data?.stats.total_cases || 0}
          icon={<div className="w-6 h-6 text-text-muted">📁</div>}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CaseList cases={data?.recent_cases || []} />
        <SystemHealthCard health={data?.system_health?.elk || { name: 'ELK', status: 'healthy', latency: '15ms' }} />
        <SystemHealthCard health={data?.system_health?.gitlab || { name: 'GitLab', status: 'healthy', latency: '20ms' }} />
        <SystemHealthCard health={data?.system_health?.k8s || { name: 'K8s', status: 'warning', latency: '45ms' }} />
        <SystemHealthCard health={data?.system_health?.neo4j || { name: 'Neo4j', status: 'healthy', latency: '12ms' }} />
      </div>
    </div>
  );
}
