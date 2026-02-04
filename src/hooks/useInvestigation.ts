import { useState, useEffect, useCallback } from 'react';
import { investigationApi, InvestigationData } from '../lib/api';

interface UseInvestigationReturn {
  data: InvestigationData | null;
  loading: boolean;
  error: string | null;
  refreshData: () => Promise<void>;
}

export function useInvestigation(): UseInvestigationReturn {
  const [data, setData] = useState<InvestigationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await investigationApi.getInvestigationData();
      setData(result);
    } catch (err) {
      console.error('[useInvestigation] Failed to load data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return {
    data,
    loading,
    error,
    refreshData: loadData,
  };
}
