import { useState } from 'react';
import { Server, GitBranch, Cloud, Database, RefreshCw, X } from 'lucide-react';
import { Card, Button } from '../common';
import { cn } from '../../lib/utils';
import { useSettingsStore } from '@/store/settingsStore';
import { toolIcons } from '../../constants';

export default function ToolList() {
  const { tools, testTool } = useSettingsStore();
  const [testingId, setTestingId] = useState<string | null>(null);

  const handleTest = async (id: string) => {
    setTestingId(id);
    try {
      const result = await testTool(id);
      alert(result.success ? '连接成功' : `连接失败: ${result.message}`);
    } catch (error: any) {
      alert(`测试失败: ${error.message}`);
    } finally {
      setTestingId(null);
    }
  };

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-text-main mb-4">外部工具</h3>
      <div className="space-y-3">
        {tools.map((tool) => {
          const Icon = toolIcons[tool.name as keyof typeof toolIcons] || Server;

          return (
            <div
              key={tool.id}
              className="flex items-center justify-between p-4 bg-bg-elevated/30 rounded-lg"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className={cn(
                      'p-2 rounded-lg',
                      tool.connected ? 'bg-semantic-success' : 'bg-bg-elevated'
                    )}
                  >
                    <Icon
                      className={cn(
                        'w-5 h-5',
                        tool.connected ? 'text-white' : 'text-text-muted'
                      )}
                    />
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-text-main">{tool.name}</h4>
                    <p className="text-xs text-text-muted">{tool.url}</p>
                  </div>
                </div>
                <div
                  className={cn(
                    'text-xs px-2 py-1 rounded',
                    tool.connected
                      ? 'bg-semantic-success/10 text-semantic-success'
                      : 'bg-semantic-danger/10 text-semantic-danger'
                  )}
                >
                  {tool.connected ? '已连接' : '未连接'}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  onClick={() => handleTest(tool.id)}
                  variant="secondary"
                  icon={<RefreshCw className="w-4 h-4" />}
                  disabled={testingId === tool.id}
                >
                  {testingId === tool.id ? '测试中...' : '测试连接'}
                </Button>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
