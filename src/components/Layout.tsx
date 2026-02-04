import { ReactNode } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Search,
  BookOpen,
  Settings,
  Activity,
  Cpu,
  LogOut,
  User,
  Shield,
} from 'lucide-react';
import { useAuthStore, hasPermission } from '../store/authStore';

interface LayoutProps {
  children: ReactNode;
}

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, minRole: 'viewer' as const },
  { path: '/investigation', label: '诊断工作台', icon: Search, minRole: 'viewer' as const },
  { path: '/knowledge', label: '知识浏览器', icon: BookOpen, minRole: 'viewer' as const },
  { path: '/settings', label: '系统设置', icon: Settings, minRole: 'admin' as const },
];

const roleLabels: Record<string, { label: string; color: string }> = {
  admin: { label: '管理员', color: 'bg-semantic-danger/10 text-semantic-danger' },
  engineer: { label: '工程师', color: 'bg-primary/10 text-primary' },
  viewer: { label: '观察者', color: 'bg-text-muted/10 text-text-muted' },
};

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const filteredNavItems = navItems.filter((item) => hasPermission(user, item.minRole));

  return (
    <div className="flex h-screen bg-bg-deep">
      {/* Sidebar */}
      <aside className="w-64 bg-bg-surface border-r border-border-subtle flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-border-subtle">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
              <Cpu className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-text-main">AIOps</h1>
              <p className="text-xs text-text-muted">智能诊断平台</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {filteredNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname.startsWith(item.path);
              return (
                <li key={item.path}>
                  <NavLink
                    to={item.path}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                      isActive
                        ? 'bg-primary/10 text-primary border border-primary/30'
                        : 'text-text-muted hover:bg-bg-elevated hover:text-text-main'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="font-medium">{item.label}</span>
                    {item.minRole === 'admin' && (
                      <Shield className="w-3 h-3 ml-auto text-semantic-warning" />
                    )}
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* System Status */}
        <div className="p-4 border-t border-border-subtle">
          <div className="bg-bg-elevated rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <Activity className="w-4 h-4 text-semantic-success" />
              <span className="text-sm text-text-main font-medium">系统状态</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-text-muted">Agent集群</span>
                <span className="text-semantic-success">4/4 在线</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-text-muted">知识库</span>
                <span className="text-semantic-success">已同步</span>
              </div>
            </div>
          </div>
        </div>

        {/* User Info */}
        {user && (
          <div className="p-4 border-t border-border-subtle">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-bg-elevated rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-text-muted" />
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium text-text-main">
                  {user.displayName}
                </div>
                <span className={`text-xs px-2 py-0.5 rounded ${roleLabels[user.role].color}`}>
                  {roleLabels[user.role].label}
                </span>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-bg-elevated hover:bg-bg-elevated/70 text-text-muted hover:text-text-main rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              退出登录
            </button>
          </div>
        )}
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
