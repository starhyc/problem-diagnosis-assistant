import { useState, useEffect, useRef } from 'react';
import { useSettingsStore } from '@/store/settingsStore';
import { LLMProvider } from '@/types/settings';
import { Button, Modal } from '@/components/common';

interface LLMProviderFormProps {
  provider: LLMProvider | null;
  onClose: () => void;
}

export function LLMProviderForm({ provider, onClose }: LLMProviderFormProps) {
  const { addLLMProvider, updateLLMProvider, fetchModels, discoverModels } = useSettingsStore();
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
  const [discoverError, setDiscoverError] = useState<string | null>(null);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [showModelDropdown, setShowModelDropdown] = useState(false);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Load initial data when editing
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

  // Debounced auto-discovery for existing providers
  useEffect(() => {
    // Clean up previous timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Check if auto-discovery should trigger
    const shouldAutoDiscover = shouldTriggerAutoDiscover();

    if (shouldAutoDiscover) {
      debounceTimerRef.current = setTimeout(() => {
        autoDiscoverModels();
      }, 800);
    }

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [formData.api_key, formData.base_url, formData.provider, provider]);

  // Determine if base URL field is needed
  const needsBaseUrl = formData.provider === 'azure' || formData.provider === 'custom';
  const baseUrlLabel = formData.provider === 'azure' ? 'Azure Endpoint' : 'Base URL';
  const baseUrlPlaceholder = formData.provider === 'azure'
    ? 'https://your-resource.openai.azure.com'
    : 'https://api.openai.com/v1';

  // Check if auto-discovery should be triggered
  const shouldTriggerAutoDiscover = (): boolean => {
    // API key is required
    if (!formData.api_key.trim()) return false;

    // Check by provider type
    if (formData.provider === 'openai') {
      return true;
    } else if (formData.provider === 'anthropic') {
      return true; // Anthropic returns predefined models
    } else if (formData.provider === 'azure' || formData.provider === 'custom') {
      return formData.base_url.trim().length > 0;
    }

    return false;
  };

  // Auto-discover models
  const autoDiscoverModels = async () => {
    setDiscovering(true);
    setDiscoverError(null);
    setAvailableModels([]);

    try {
      let models: string[];

      if (provider?.id) {
        // Existing provider: use saved config
        models = await fetchModels(provider.id);
      } else {
        // New provider: use current form data
        models = await discoverModels({
          provider: formData.provider,
          api_key: formData.api_key,
          base_url: formData.base_url || undefined,
        });
      }

      setAvailableModels(models);
      if (models.length > 0) {
        setShowModelDropdown(true);
      }
    } catch (error: any) {
      setDiscoverError(`模型发现失败: ${error.message}`);
      setShowModelDropdown(false);
    } finally {
      setDiscovering(false);
    }
  };

  // Manual trigger for model discovery
  const handleDiscoverModels = async () => {
    await autoDiscoverModels();
  };

  // Add model from dropdown or manual input
  const handleAddModelFromDropdown = (model: string) => {
    if (!formData.models.includes(model)) {
      setFormData(prev => ({
        ...prev,
        models: [...prev.models, model]
      }));
    }
    setShowModelDropdown(false);
  };

  const handleManualAddModel = () => {
    if (manualModel && !formData.models.includes(manualModel)) {
      setFormData(prev => ({
        ...prev,
        models: [...prev.models, manualModel]
      }));
      setManualModel('');
    }
  };

  const handleRemoveModel = (model: string) => {
    setFormData(prev => ({
      ...prev,
      models: prev.models.filter(m => m !== model)
    }));
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

  // Return a boolean indicating if auto-discovery is available
  const canAutoDiscover = provider?.id && shouldTriggerAutoDiscover();

  return (
    <Modal
      isOpen
      onClose={onClose}
      title={provider ? '编辑 LLM 提供商' : '添加 LLM 提供商'}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-text-main mb-1">名称</label>
          <input
            type="text"
            value={formData.name}
            onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
            className="w-full px-3 py-2 border border-border-subtle rounded text-text-main bg-bg-surface focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
            placeholder="例如: My OpenAI Provider"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-text-main mb-1">提供商类型</label>
          <select
            value={formData.provider}
            onChange={e => setFormData(prev => ({ ...prev, provider: e.target.value }))}
            className="w-full px-3 py-2 border border-border-subtle rounded text-text-main bg-bg-surface"
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="azure">Azure OpenAI</option>
            <option value="custom">自定义 (OpenAI Compatible)</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-text-main mb-1">API Key</label>
          <input
            type="password"
            value={formData.api_key}
            onChange={e => setFormData(prev => ({ ...prev, api_key: e.target.value }))}
            className="w-full px-3 py-2 border border-border-subtle rounded text-text-main bg-bg-surface focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
            placeholder="sk-..."
            required
          />
        </div>

        {needsBaseUrl && (
          <div>
            <label className="block text-sm font-medium text-text-main mb-1">
              {baseUrlLabel} {formData.provider === 'custom' && '(可选)'}
            </label>
            <input
              type="text"
              value={formData.base_url}
              onChange={e => setFormData(prev => ({ ...prev, base_url: e.target.value }))}
              className="w-full px-3 py-2 border border-border-subtle rounded text-text-main bg-bg-surface"
              placeholder={baseUrlPlaceholder}
              required={formData.provider === 'azure'}
            />
          </div>
        )}

        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="block text-sm font-medium text-text-main">模型列表</label>
            <div className="flex gap-2 items-center">
              <Button
                type="button"
                size="sm"
                variant="secondary"
                onClick={handleDiscoverModels}
                disabled={discovering || !shouldTriggerAutoDiscover()}
              >
                {discovering ? '发现中...' : '自动发现'}
              </Button>
            </div>
          </div>

          {/* Auto-discovery progress indicator */}
          {discovering && (
            <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded text-sm text-blue-700">
              正在发现可用模型...
            </div>
          )}

          {/* Auto-discovery error */}
          {discoverError && (
            <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
              {discoverError}
              <button
                type="button"
                onClick={autoDiscoverModels}
                className="ml-2 underline font-medium"
              >
                重试
              </button>
            </div>
          )}

          {/* Available Models Dropdown */}
          {availableModels.length > 0 && (
            <div className="mb-3 relative">
              <label className="block text-sm font-medium text-text-main mb-2">
                可用模型 (点击添加到列表)
              </label>
              <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto border border-border-subtle rounded p-2 bg-bg-surface">
                {availableModels.map((model) => (
                  <button
                    key={model}
                    type="button"
                    onClick={() => handleAddModelFromDropdown(model)}
                    className={`px-2 py-1 text-sm border rounded ${
                      formData.models.includes(model)
                        ? 'bg-green-100 border-green-300 text-green-800 cursor-default'
                        : 'bg-white border-gray-300 hover:bg-blue-50 hover:border-blue-400 text-text-main'
                    }`}
                    disabled={formData.models.includes(model)}
                  >
                    {model}
                    {formData.models.includes(model) && ' ✓'}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Manual add */}
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={manualModel}
              onChange={e => setManualModel(e.target.value)}
              onFocus={() => {
                if (shouldTriggerAutoDiscover() && !discovering && availableModels.length === 0) {
                  autoDiscoverModels();
                }
              }}
              className="flex-1 px-3 py-2 border border-border-subtle rounded text-text-main bg-bg-surface"
              placeholder="手动添加模型 (如: gpt-4, claude-3...)"
            />
            <Button type="button" onClick={handleManualAddModel}>添加</Button>
          </div>

          {/* Current Models */}
          {formData.models.length > 0 && (
            <>
              <div className="text-sm text-text-secondary mb-1">已添加的模型:</div>
              <div className="flex flex-wrap gap-2">
                {formData.models.map(model => (
                  <span
                    key={model}
                    className="px-2 py-1 bg-bg-elevated border border-border-subtle rounded text-sm flex items-center gap-1 text-text-main"
                  >
                    {model}
                    <button
                      type="button"
                      onClick={() => handleRemoveModel(model)}
                      className="text-semantic-danger hover:text-semantic-danger/80 font-bold px-1"
                      title="移除"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </>
          )}
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
