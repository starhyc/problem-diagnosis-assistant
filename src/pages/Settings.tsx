import { useState, useEffect } from 'react';
import { useSettingsStore } from '@/store/settingsStore';
import { useAuthStore } from '@/store/authStore';
import { LLMProviderList } from '@/components/settings/LLMProviderList';
import ToolList from '@/components/settings/ToolList';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface CollapsibleSectionProps {
  title: string;
  children: React.ReactNode;
  defaultExpanded?: boolean;
  sectionKey: string;
}

function CollapsibleSection({ title, children, defaultExpanded = true, sectionKey }: CollapsibleSectionProps) {
  const [isExpanded, setIsExpanded] = useState(() => {
    const saved = localStorage.getItem(`settings-section-${sectionKey}`);
    return saved !== null ? saved === 'true' : defaultExpanded;
  });

  const toggleExpanded = () => {
    const newState = !isExpanded;
    setIsExpanded(newState);
    localStorage.setItem(`settings-section-${sectionKey}`, String(newState));
  };

  return (
    <div className="border border-border-subtle rounded-lg bg-bg-surface">
      <button
        onClick={toggleExpanded}
        className="w-full flex items-center justify-between p-4 hover:bg-bg-elevated/30 transition-colors"
      >
        <h2 className="text-lg font-semibold text-text-main">{title}</h2>
        {isExpanded ? (
          <ChevronDown className="w-5 h-5 text-text-muted" />
        ) : (
          <ChevronRight className="w-5 h-5 text-text-muted" />
        )}
      </button>
      {isExpanded && (
        <div className="p-4 pt-0">
          {children}
        </div>
      )}
    </div>
  );
}

export default function Settings() {
  const {
    loadLLMProviders,
    loadTools,
    loadMCPServers,
    saveMCPServer,
    toggleMCPServer,
    testMCPServer,
    loadSkills,
    uploadSkill,
    toggleSkill,
    executeSkill,
    mcpServers,
    skills,
    loading,
    error,
  } = useSettingsStore();
  const { user } = useAuthStore();

  const [newMcp, setNewMcp] = useState({ id: '', name: '', transport: 'http', endpoint: '', enabled: true, version: 'latest' });

  useEffect(() => {
    if (user?.role !== 'admin') {
      alert('仅管理员可访问设置页面');
      return;
    }
    loadLLMProviders();
    loadTools();
    loadMCPServers();
    loadSkills();
  }, [user]);

  if (user?.role !== 'admin') {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-text-muted">权限不足</p>
        </div>
      </div>
    );
  }

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

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text-main">设置</h1>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-semantic-danger/10 border border-semantic-danger/30 rounded-lg">
          <p className="text-semantic-danger font-medium mb-1">⚠️ 错误</p>
          <p className="text-sm text-text-muted">{error}</p>
        </div>
      )}

      <div className="space-y-4">
        <CollapsibleSection title="LLM 提供商" sectionKey="llm-providers" defaultExpanded={true}>
          <LLMProviderList />
        </CollapsibleSection>

        <CollapsibleSection title="外部工具" sectionKey="external-tools" defaultExpanded={true}>
          <ToolList />
        </CollapsibleSection>

        <CollapsibleSection title="MCP 管理" sectionKey="mcp-management" defaultExpanded={true}>
          <div className="space-y-3">
            <div className="grid grid-cols-6 gap-2">
              <input className="col-span-1 border rounded px-2 py-1" placeholder="ID" value={newMcp.id} onChange={(e) => setNewMcp({ ...newMcp, id: e.target.value })} />
              <input className="col-span-1 border rounded px-2 py-1" placeholder="名称" value={newMcp.name} onChange={(e) => setNewMcp({ ...newMcp, name: e.target.value })} />
              <input className="col-span-1 border rounded px-2 py-1" placeholder="传输" value={newMcp.transport} onChange={(e) => setNewMcp({ ...newMcp, transport: e.target.value })} />
              <input className="col-span-2 border rounded px-2 py-1" placeholder="Endpoint" value={newMcp.endpoint} onChange={(e) => setNewMcp({ ...newMcp, endpoint: e.target.value })} />
              <button className="border rounded px-2 py-1" onClick={() => saveMCPServer(newMcp)}>保存</button>
            </div>

            {mcpServers.map((server) => (
              <div key={server.id} className="flex items-center justify-between border rounded p-3">
                <div>
                  <div className="font-medium">{server.name} ({server.version})</div>
                  <div className="text-xs text-text-muted">{server.transport} · {server.endpoint}</div>
                </div>
                <div className="flex gap-2">
                  <button className="border rounded px-2 py-1" onClick={() => toggleMCPServer(server.id, !server.enabled)}>{server.enabled ? '停用' : '启用'}</button>
                  <button className="border rounded px-2 py-1" onClick={async () => {
                    const result = await testMCPServer(server.id);
                    alert(result.success ? '连接成功' : `连接失败: ${result.message}`);
                  }}>测试连接</button>
                </div>
              </div>
            ))}
          </div>
        </CollapsibleSection>

        <CollapsibleSection title="Skill 管理" sectionKey="skill-management" defaultExpanded={true}>
          <div className="space-y-3">
            <input
              type="file"
              accept=".zip,.tar,.tgz,.tar.gz"
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                await uploadSkill(file);
                alert('Skill 上传成功');
              }}
            />

            {skills.map((skill) => (
              <div key={skill.id} className="flex items-center justify-between border rounded p-3">
                <div>
                  <div className="font-medium">{skill.name} ({skill.version})</div>
                  <div className="text-xs text-text-muted">{skill.id} · {skill.entrypoint}</div>
                </div>
                <div className="flex gap-2">
                  <button className="border rounded px-2 py-1" onClick={() => toggleSkill(skill.id, !skill.enabled)}>{skill.enabled ? '停用' : '启用'}</button>
                  <button className="border rounded px-2 py-1" onClick={async () => {
                    const result = await executeSkill(skill.id, false);
                    if (result.status === 'approval_required') {
                      const ok = confirm('此 Skill 需要权限审批，是否授权执行？');
                      if (ok) {
                        const rerun = await executeSkill(skill.id, true);
                        alert(rerun.returncode === 0 ? '执行成功' : `执行失败: ${rerun.stderr || rerun.stdout}`);
                      }
                    } else {
                      alert(result.returncode === 0 ? '执行成功' : `执行失败: ${result.stderr || result.stdout}`);
                    }
                  }}>沙盒测试</button>
                </div>
              </div>
            ))}
          </div>
        </CollapsibleSection>
      </div>
    </div>
  );
}
