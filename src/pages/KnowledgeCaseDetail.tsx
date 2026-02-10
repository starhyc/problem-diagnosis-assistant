import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { knowledgeApi, HistoricalCase } from '../lib/api';

export default function KnowledgeCaseDetail() {
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [caseDetail, setCaseDetail] = useState<HistoricalCase | null>(null);
  const [isNotFound, setIsNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setLoading(false);
      setIsNotFound(true);
      return;
    }

    const loadCase = async () => {
      try {
        setLoading(true);
        setError(null);
        setIsNotFound(false);
        const result = await knowledgeApi.getCaseById(id);
        setCaseDetail(result);
      } catch (err) {
        if (typeof err === 'object' && err && 'status' in err && (err as { status?: number }).status === 404) {
          setIsNotFound(true);
          return;
        }
        setError(err instanceof Error ? err.message : '加载案例详情失败');
      } finally {
        setLoading(false);
      }
    };

    loadCase();
  }, [id]);

  const relatedEvidence = useMemo(() => {
    if (!caseDetail) {
      return [];
    }

    if (Array.isArray(caseDetail.evidence) && caseDetail.evidence.length > 0) {
      return caseDetail.evidence;
    }

    return ['暂无关联证据'];
  }, [caseDetail]);

  if (loading) {
    return <div className="h-full flex items-center justify-center"><div className="animate-spin w-12 h-12 border-4 border-primary border-t-transparent rounded-full" /></div>;
  }

  if (isNotFound) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center space-y-3">
          <h1 className="text-xl font-semibold text-text-main">案例不存在或已删除</h1>
          <p className="text-text-muted text-sm">请返回历史案例列表重新选择。</p>
          <Link to="/knowledge" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-white">
            <ArrowLeft className="w-4 h-4" />
            返回知识库
          </Link>
        </div>
      </div>
    );
  }

  if (error || !caseDetail) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center space-y-3">
          <h1 className="text-xl font-semibold text-semantic-danger">加载失败</h1>
          <p className="text-text-muted text-sm">{error || '案例详情为空'}</p>
          <Link to="/knowledge" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-bg-elevated text-text-main">
            <ArrowLeft className="w-4 h-4" />
            返回知识库
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <Link to="/knowledge" className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-main">
        <ArrowLeft className="w-4 h-4" />
        返回历史案例
      </Link>

      <div className="bg-bg-surface rounded-xl border border-border-subtle p-6 space-y-6">
        <div className="space-y-2">
          <p className="text-xs text-text-muted">案例 ID: {caseDetail.id}</p>
          <h1 className="text-2xl font-bold text-text-main">{caseDetail.title}</h1>
        </div>

        <section className="space-y-2">
          <h2 className="text-sm font-semibold text-text-main">症状</h2>
          <div className="flex flex-wrap gap-2">
            {caseDetail.symptoms.map((symptom, index) => (
              <span key={`${symptom}-${index}`} className="px-3 py-1 rounded-full bg-primary/10 text-primary text-sm">
                {symptom}
              </span>
            ))}
          </div>
        </section>

        <section className="space-y-2">
          <h2 className="text-sm font-semibold text-text-main">根因</h2>
          <p className="text-sm text-text-main leading-relaxed">{caseDetail.root_cause}</p>
        </section>

        <section className="space-y-2">
          <h2 className="text-sm font-semibold text-text-main">方案</h2>
          <p className="text-sm text-text-main leading-relaxed">{caseDetail.solution}</p>
        </section>

        <section className="space-y-2">
          <h2 className="text-sm font-semibold text-text-main">关联证据</h2>
          <ul className="list-disc pl-5 space-y-1 text-sm text-text-main">
            {relatedEvidence.map((item, index) => (
              <li key={`${item}-${index}`}>{item}</li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
