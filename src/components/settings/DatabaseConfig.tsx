import { useState, useEffect } from 'react';
import { useSettingsStore } from '@/store/settingsStore';
import { Button } from '@/components/common/Button';
import { Card } from '@/components/common/Card';

export function DatabaseConfig() {
  const { databases, updateDatabase, testDatabase, loadDatabases } = useSettingsStore();
  const [testingId, setTestingId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<any>({});

  useEffect(() => {
    loadDatabases();
  }, [loadDatabases]);

  const handleTest = async (id: string) => {
    setTestingId(id);
    try {
      const result = await testDatabase(id);
      alert(result.success ? '连接成功' : `连接失败: ${result.message}`);
    } catch (error: any) {
      alert(`测试失败: ${error.message}`);
    } finally {
      setTestingId(null);
    }
  };

  const handleEdit = (db: any) => {
    setEditingId(db.id);
    setFormData(db);
  };

  const handleSave = async () => {
    if (!editingId) return;
    try {
      await updateDatabase(editingId, formData);
      setEditingId(null);
      setFormData({});
    } catch (error: any) {
      alert(`保存失败: ${error.message}`);
    }
  };

  const handleCancel = () => {
    setEditingId(null);
    setFormData({});
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">数据库配置</h2>

      <div className="grid gap-4">
        {databases.map(db => (
          <Card key={db.id} className="p-4">
            {editingId === db.id ? (
              <div className="space-y-4">
                <h3 className="font-medium">{db.type === 'postgresql' ? 'PostgreSQL' : 'Redis'}</h3>

                {db.type === 'postgresql' ? (
                  <>
                    <div>
                      <label className="block text-sm font-medium mb-1">主机</label>
                      <input
                        type="text"
                        value={formData.host || ''}
                        onChange={e => setFormData({ ...formData, host: e.target.value })}
                        className="w-full px-3 py-2 border rounded"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">端口</label>
                      <input
                        type="number"
                        value={formData.port || ''}
                        onChange={e => setFormData({ ...formData, port: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 border rounded"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">数据库名</label>
                      <input
                        type="text"
                        value={formData.database || ''}
                        onChange={e => setFormData({ ...formData, database: e.target.value })}
                        className="w-full px-3 py-2 border rounded"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">用户名</label>
                      <input
                        type="text"
                        value={formData.user || ''}
                        onChange={e => setFormData({ ...formData, user: e.target.value })}
                        className="w-full px-3 py-2 border rounded"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">密码</label>
                      <input
                        type="password"
                        value={formData.password || ''}
                        onChange={e => setFormData({ ...formData, password: e.target.value })}
                        className="w-full px-3 py-2 border rounded"
                      />
                    </div>
                  </>
                ) : (
                  <div>
                    <label className="block text-sm font-medium mb-1">连接 URL</label>
                    <input
                      type="text"
                      value={formData.url || ''}
                      onChange={e => setFormData({ ...formData, url: e.target.value })}
                      className="w-full px-3 py-2 border rounded"
                      placeholder="redis://localhost:6379/0"
                    />
                  </div>
                )}

                <div className="flex justify-end gap-2">
                  <Button variant="secondary" onClick={handleCancel}>取消</Button>
                  <Button onClick={handleSave}>保存</Button>
                </div>
              </div>
            ) : (
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-medium mb-2">{db.type === 'postgresql' ? 'PostgreSQL' : 'Redis'}</h3>
                  {db.type === 'postgresql' ? (
                    <>
                      <p className="text-sm text-gray-600">主机: {db.host}:{db.port}</p>
                      <p className="text-sm text-gray-600">数据库: {db.database}</p>
                      <p className="text-sm text-gray-600">用户: {db.user}</p>
                    </>
                  ) : (
                    <p className="text-sm text-gray-600">URL: {db.url}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleTest(db.id)}
                    disabled={testingId === db.id}
                  >
                    {testingId === db.id ? '测试中...' : '测试连接'}
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleEdit(db)}
                  >
                    编辑
                  </Button>
                </div>
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
