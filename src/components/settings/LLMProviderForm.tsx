import { useState, useEffect } from 'react';
import { useSettingsStore } from '@/store/settingsStore';
import { LLMProvider } from '@/types/settings';
import { Button, Modal } from '@/components/common';

interface LLMProviderFormProps {
  provider: LLMProvider | null;
  onClose: () => void;
}

export function LLMProviderForm({ provider, onClose }: LLMProviderFormProps) {
  const { addLLMProvider, updateLLMProvider, fetchModels } = useSettingsStore();
  const [formData, setFormData] = useState({
    name: '',
    provider: 'openai',
    api_key: '',
    base_url: '',
    models: [] as string[],
    is_default: false,
    enabled: true,
  });
  const [manualModel, setManualModel] = useState('');
  const [discovering, setDiscovering] = useState(false);

  useEffect(() => {
    if (provider) {
      setFormData({
        name: provider.name,
        provider: provider.provider,
        api_key: provider.api_key,
        base_url: provider.base_url || '',
        models: provider.models,
        is_default: provider.is_default,
        enabled: provider.enabled,
      });
    }
  }, [provider]);

  const handleDiscoverModels = async () => {
    if (!provider?.id) return;
    setDiscovering(true);
    try {
      const models = await fetchModels(provider.id);
      setFormData(prev => ({ ...prev, models }));
    } catch (error: any) {
      alert(`模型发现失败: ${error.message}`);
    } finally {
      setDiscovering(false);
    }
  };

  const handleAddModel = () => {
    if (manualModel && !formData.models.includes(manualModel)) {
      setFormData(prev => ({ ...prev, models: [...prev.models, manualModel] }));
      setManualModel('');
    }
  };

  const handleRemoveModel = (model: string) => {
    setFormData(prev => ({ ...prev, models: prev.models.filter(m => m !== model) }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (provider) {
        await updateLLMProvider(provider.id, formData);
      } else {
        await addLLMProvider(formData);
      }
      onClose();
    } catch (error: any) {
      alert(`保存失败: ${error.message}`);
    }
  };

  return (
    <Modal isOpen onClose={onClose} title={provider ? '编辑 LLM 提供商' : '添加 LLM 提供商'}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-text-main mb-1">名称</label>
          <input
            type="text"
            value={formData.name}
            onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
            className="w-full px-3 py-2 border rounded text-text-main bg-bg-surface"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-text-main mb-1">提供商类型</label>
          <select
            value={formData.provider}
            onChange={e => setFormData(prev => ({ ...prev, provider: e.target.value }))}
            className="w-full px-3 py-2 border rounded text-text-main bg-bg-surface"
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="azure">Azure OpenAI</option>
            <option value="custom">自定义</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-text-main mb-1">API Key</label>
          <input
            type="password"
            value={formData.api_key}
            onChange={e => setFormData(prev => ({ ...prev, api_key: e.target.value }))}
            className="w-full px-3 py-2 border rounded text-text-main bg-bg-surface"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-text-main mb-1">Base URL (可选)</label>
          <input
            type="text"
            value={formData.base_url}
            onChange={e => setFormData(prev => ({ ...prev, base_url: e.target.value }))}
            className="w-full px-3 py-2 border rounded text-text-main bg-bg-surface"
            placeholder="https://api.openai.com/v1"
          />
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="block text-sm font-medium text-text-main">模型列表</label>
            {provider && (
              <Button
                type="button"
                size="sm"
                variant="secondary"
                onClick={handleDiscoverModels}
                disabled={discovering}
              >
                {discovering ? '发现中...' : '自动发现'}
              </Button>
            )}
          </div>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={manualModel}
              onChange={e => setManualModel(e.target.value)}
              className="flex-1 px-3 py-2 border rounded text-text-main bg-bg-surface"
              placeholder="手动添加模型"
            />
            <Button type="button" onClick={handleAddModel}>添加</Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {formData.models.map(model => (
              <span key={model} className="px-2 py-1 bg-gray-100 rounded text-sm flex items-center gap-1">
                {model}
                <button type="button" onClick={() => handleRemoveModel(model)} className="text-red-500">×</button>
              </span>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.is_default}
              onChange={e => setFormData(prev => ({ ...prev, is_default: e.target.checked }))}
            />
            <span className="text-sm text-text-main">设为默认提供商</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.enabled}
              onChange={e => setFormData(prev => ({ ...prev, enabled: e.target.checked }))}
            />
            <span className="text-sm text-text-main">启用</span>
          </label>
        </div>

        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>取消</Button>
          <Button type="submit">保存</Button>
        </div>
      </form>
    </Modal>
  );
}
