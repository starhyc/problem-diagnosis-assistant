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
      <button onClick={toggleExpanded} className="w-full flex items-center justify-between p-4 hover:bg-bg-elevated/30 transition-colors">
        <h2 className="text-lg font-semibold text-text-main">{title}</h2>
        {isExpanded ? <ChevronDown className="w-5 h-5 text-text-muted" /> : <ChevronRight className="w-5 h-5 text-text-muted" />}
      </button>
      {isExpanded && <div className="p-4 pt-0 space-y-3">{children}</div>}
    </div>
  );
}

function ModuleAudit({ module }: { module: string }) {
  const { moduleAuditLogs, moduleRecentChanges, loadModuleAuditLogs, loadModuleRecentChanges } = useSettingsStore();

  useEffect(() => {
    loadModuleAuditLogs(module);
    loadModuleRecentChanges(module);
  }, [module]);

  const logs = moduleAuditLogs[module] || [];
  const changes = moduleRecentChanges[module] || [];

  return (
    <div className="grid grid-cols-2 gap-3">
      <div className="border rounded p-2">
        <div className="text-sm font-medium mb-2">最近变更</div>
        <div className="space-y-1 text-xs">
          {changes.slice(0, 5).map(c => <div key={c.id}>{c.action} · {c.target_id}</div>)}
        </div>
      </div>
      <div className="border rounded p-2">
        <div className="text-sm font-medium mb-2">操作日志</div>
        <div className="space-y-1 text-xs max-h-36 overflow-auto">
          {logs.slice(0, 10).map(l => <div key={l.id}>{l.actor} · {l.action}</div>)}
        </div>
      </div>
    </div>
  );
}

export default function Settings() {
  const {
    loadLLMProviders, loadTools, loadMCPServers, saveMCPServer, toggleMCPServer, testMCPServer,
    loadSkills, uploadSkill, toggleSkill, executeSkill, testSkill,
    loadUsers, createUser, updateUserRole, updateUserStatus,
    logSystemParamsChange,
    mcpServers, skills, users, loading, error,
  } = useSettingsStore();
  const { user } = useAuthStore();

  const [newMcp, setNewMcp] = useState({ id: '', name: '', transport: 'http', endpoint: '', enabled: true, version: 'latest' });
  const [newUser, setNewUser] = useState({ username: '', email: '', password: '', display_name: '', role: 'viewer' });

  useEffect(() => {
    if (user?.role !== 'admin') {
      alert('仅管理员可访问设置页面');
      return;
    }
    loadLLMProviders();
    loadTools();
    loadMCPServers();
    loadSkills();
    loadUsers();
  }, [user]);

  if (user?.role !== 'admin') return <div className="h-full flex items-center justify-center"><p className="text-text-muted">权限不足</p></div>;
  if (loading) return <div className="h-full flex items-center justify-center"><p className="text-text-muted">加载中...</p></div>;

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-text-main">设置中心</h1>
      {error && <div className="p-4 bg-semantic-danger/10 border border-semantic-danger/30 rounded-lg text-sm">{error}</div>}

      <CollapsibleSection title="用户管理" sectionKey="users">
        <div className="grid grid-cols-6 gap-2">
          <input className="border rounded px-2 py-1" placeholder="用户名" value={newUser.username} onChange={(e) => setNewUser({ ...newUser, username: e.target.value })} />
          <input className="border rounded px-2 py-1" placeholder="邮箱" value={newUser.email} onChange={(e) => setNewUser({ ...newUser, email: e.target.value })} />
          <input className="border rounded px-2 py-1" placeholder="显示名" value={newUser.display_name} onChange={(e) => setNewUser({ ...newUser, display_name: e.target.value })} />
          <input className="border rounded px-2 py-1" placeholder="密码" type="password" value={newUser.password} onChange={(e) => setNewUser({ ...newUser, password: e.target.value })} />
          <select className="border rounded px-2 py-1" value={newUser.role} onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}><option>viewer</option><option>operator</option><option>admin</option></select>
          <button className="border rounded px-2 py-1" onClick={async () => { await createUser(newUser); setNewUser({ username: '', email: '', password: '', display_name: '', role: 'viewer' }); }}>创建用户</button>
        </div>
        {users.map(u => (
          <div key={u.id} className="border rounded p-2 flex justify-between items-center">
            <div>{u.username} · {u.role} · {u.is_active ? '启用' : '禁用'}</div>
            <div className="flex gap-2">
              <button className="border rounded px-2" onClick={() => updateUserStatus(u.id, !u.is_active)}>{u.is_active ? '禁用' : '启用'}</button>
              <select className="border rounded px-2" value={u.role} onChange={(e) => updateUserRole(u.id, e.target.value)}><option>viewer</option><option>operator</option><option>admin</option></select>
            </div>
          </div>
        ))}
        <ModuleAudit module="user-management" />
      </CollapsibleSection>

      <CollapsibleSection title="LLM 配置" sectionKey="llm"><LLMProviderList /><ModuleAudit module="llm" /></CollapsibleSection>

      <CollapsibleSection title="MCP 配置" sectionKey="mcp">
        <div className="grid grid-cols-6 gap-2">
          <input className="col-span-1 border rounded px-2 py-1" placeholder="ID" value={newMcp.id} onChange={(e) => setNewMcp({ ...newMcp, id: e.target.value })} />
          <input className="col-span-1 border rounded px-2 py-1" placeholder="名称" value={newMcp.name} onChange={(e) => setNewMcp({ ...newMcp, name: e.target.value })} />
          <input className="col-span-1 border rounded px-2 py-1" placeholder="传输" value={newMcp.transport} onChange={(e) => setNewMcp({ ...newMcp, transport: e.target.value })} />
          <input className="col-span-2 border rounded px-2 py-1" placeholder="Endpoint" value={newMcp.endpoint} onChange={(e) => setNewMcp({ ...newMcp, endpoint: e.target.value })} />
          <button className="border rounded px-2 py-1" onClick={() => saveMCPServer(newMcp)}>保存</button>
        </div>
        {mcpServers.map((server) => <div key={server.id} className="border rounded p-2 flex justify-between"><div>{server.name} · {server.status} · {server.last_test_status || '未测试'}</div><div className="flex gap-2"><button className="border rounded px-2" onClick={() => toggleMCPServer(server.id, !server.enabled)}>{server.enabled ? '停用' : '启用'}</button><button className="border rounded px-2" onClick={async () => alert((await testMCPServer(server.id)).message)}>测试连接</button></div></div>)}
        <ModuleAudit module="mcp" />
      </CollapsibleSection>

      <CollapsibleSection title="Skill 配置" sectionKey="skills">
        <input type="file" accept=".zip,.tar,.tgz,.tar.gz" onChange={async (e) => { const file = e.target.files?.[0]; if (!file) return; await uploadSkill(file); }} />
        {skills.map((skill) => <div key={skill.id} className="border rounded p-2 flex justify-between"><div>{skill.name} · {skill.status} · {skill.last_test_status || '未测试'}</div><div className="flex gap-2"><button className="border rounded px-2" onClick={() => toggleSkill(skill.id, !skill.enabled)}>{skill.enabled ? '停用' : '启用'}</button><button className="border rounded px-2" onClick={async () => alert((await testSkill(skill.id)).message)}>连通性测试</button><button className="border rounded px-2" onClick={() => executeSkill(skill.id, false)}>沙盒测试</button></div></div>)}
        <ModuleAudit module="skill" />
      </CollapsibleSection>

      <CollapsibleSection title="外部工具" sectionKey="tools"><ToolList /><ModuleAudit module="external-tools" /></CollapsibleSection>

      <CollapsibleSection title="系统参数" sectionKey="system-params">
        <button className="border rounded px-3 py-1" onClick={() => logSystemParamsChange('update-threshold', { key: 'risk_threshold', value: 0.8 })}>记录系统参数变更示例</button>
        <ModuleAudit module="system-params" />
      </CollapsibleSection>
    </div>
  );
}
