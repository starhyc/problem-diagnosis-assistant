import { create } from 'zustand';
import { authApi, ApiError } from '../lib/api';

interface TokenPayload {
  userId: string;
  email: string;
  role: string;
  displayName: string;
}

function tokenFromPayload(payload: TokenPayload): User {
  return {
    id: payload.userId,
    email: payload.email,
    displayName: payload.displayName,
    role: payload.role as 'admin' | 'engineer' | 'viewer',
  };
}

// 用户类型
export interface User {
  id: string;
  email: string;
  displayName: string;
  role: 'admin' | 'engineer' | 'viewer';
  avatar?: string;
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  error: null,

  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await authApi.login({ username, password });
      localStorage.setItem('aiops_token', response.access_token);
      
      const user: User = {
        id: response.user.id.toString(),
        email: response.user.email,
        displayName: response.user.display_name,
        role: response.user.role as 'admin' | 'engineer' | 'viewer',
        avatar: response.user.avatar,
      };
      
      set({ user, isLoading: false });
      return true;
    } catch (error) {
      if (error instanceof ApiError) {
        set({ error: error.message, isLoading: false });
      } else {
        set({ error: '登录失败，请稍后重试', isLoading: false });
      }
      return false;
    }
  },

  logout: async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('aiops_token');
      set({ user: null });
    }
  },

  checkAuth: async () => {
    const token = localStorage.getItem('aiops_token');
    if (token) {
      try {
        const userData = await authApi.getCurrentUser();
        const user: User = {
          id: userData.id.toString(),
          email: userData.email,
          displayName: userData.display_name,
          role: userData.role as 'admin' | 'engineer' | 'viewer',
          avatar: userData.avatar,
        };
        set({ user, isLoading: false });
        return;
      } catch (error) {
        localStorage.removeItem('aiops_token');
      }
    }
    set({ isLoading: false });
  },
}));

// 权限检查工具函数
export function hasPermission(user: User | null, requiredRole: 'admin' | 'engineer' | 'viewer'): boolean {
  if (!user) return false;
  const roleHierarchy = { admin: 3, engineer: 2, viewer: 1 };
  return roleHierarchy[user.role] >= roleHierarchy[requiredRole];
}
