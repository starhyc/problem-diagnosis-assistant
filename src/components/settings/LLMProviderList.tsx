import { useState } from 'react';
import { useSettingsStore } from '@/store/settingsStore';
import { LLMProvider } from '@/types/settings';
import { Button, Card, Badge } from '@/components/common';
import { LLMProviderForm } from './LLMProviderForm';

export function LLMProviderList() {
  const { llmProviders, deleteLLMProvider, testLLMProvider, loading } = useSettingsStore();
  const [showForm, setShowForm] = useState(false);
  const [editingProvider, setEditingProvider] = useState<LLMProvider | null>(null);
  const [testingId, setTestingId] = useState<string | null>(null);

  const handleTest = async (id: string) => {
    setTestingId(id);
    try {
      const result = await testLLMProvider(id);
      alert(result.success ? '连接成功' : `连接失败: ${result.message}`);
    } catch (error: any) {
      alert(`测试失败: ${error.message}`);
    } finally {
      setTestingId(null);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('确定删除此 LLM 提供商？')) {
      await deleteLLMProvider(id);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">LLM 提供商</h2>
        <Button onClick={() => setShowForm(true)}>添加提供商</Button>
      </div>

      <div className="grid gap-4">
        {llmProviders.map(provider => (
          <Card key={provider.id} className="p-4">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="font-medium text-text-main">{provider.name}</h3>
                  {provider.is_default && <Badge variant="primary">默认</Badge>}
                  {!provider.enabled && <Badge variant="error">已禁用</Badge>}
                </div>
                <p className="text-sm text-text-muted">提供商: {provider.provider}</p>
                {provider.base_url && <p className="text-sm text-text-muted">URL: {provider.base_url}</p>}
                <p className="text-sm text-text-muted">模型: {provider.models.join(', ')}</p>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleTest(provider.id)}
                  disabled={testingId === provider.id}
                >
                  {testingId === provider.id ? '测试中...' : '测试'}
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => {
                    setEditingProvider(provider);
                    setShowForm(true);
                  }}
                >
                  编辑
                </Button>
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => handleDelete(provider.id)}
                >
                  删除
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {showForm && (
        <LLMProviderForm
          provider={editingProvider}
          onClose={() => {
            setShowForm(false);
            setEditingProvider(null);
          }}
        />
      )}
    </div>
  );
}
