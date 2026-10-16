import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  loginApi,
  registerFarmerApi,
  getMeApi,
  type UserSummary,
  type LoginPayload,
  type FarmerRegisterPayload,
} from '../services/api';

interface AuthContextType {
  user: UserSummary | null;
  token: string | null;
  role: 'farmer' | 'staff' | null;
  isAuthenticated: boolean;
  isLoadingAuth: boolean;
  login: (credentials: LoginPayload) => Promise<UserSummary>;
  register: (payload: FarmerRegisterPayload) => Promise<UserSummary>;
  logout: () => void;
  updateUser: (partial: Partial<UserSummary>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_STORAGE_KEY = 'namma_vivasayi_auth_token';
const USER_STORAGE_KEY = 'namma_vivasayi_auth_user';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [user, setUser] = useState<UserSummary | null>(() => {
    const saved = localStorage.getItem(USER_STORAGE_KEY);
    try {
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [isLoadingAuth, setIsLoadingAuth] = useState<boolean>(true);

  // Validate session on load
  useEffect(() => {
    let isMounted = true;
    async function validateToken() {
      const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY);
      if (!storedToken) {
        if (isMounted) setIsLoadingAuth(false);
        return;
      }

      try {
        const verifiedUser = await getMeApi(storedToken);
        if (isMounted) {
          setUser(verifiedUser);
          setToken(storedToken);
          localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(verifiedUser));
        }
      } catch {
        // Token expired or invalid
        if (isMounted) {
          setUser(null);
          setToken(null);
          localStorage.removeItem(TOKEN_STORAGE_KEY);
          localStorage.removeItem(USER_STORAGE_KEY);
        }
      } finally {
        if (isMounted) setIsLoadingAuth(false);
      }
    }

    validateToken();
    return () => {
      isMounted = false;
    };
  }, []);

  const login = async (credentials: LoginPayload): Promise<UserSummary> => {
    const authResult = await loginApi(credentials);
    const receivedToken = authResult.accessToken;
    const receivedUser = authResult.user;

    setToken(receivedToken);
    setUser(receivedUser);
    localStorage.setItem(TOKEN_STORAGE_KEY, receivedToken);
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(receivedUser));

    return receivedUser;
  };

  const register = async (payload: FarmerRegisterPayload): Promise<UserSummary> => {
    const authResult = await registerFarmerApi(payload);
    const receivedToken = authResult.accessToken;
    const receivedUser = authResult.user;

    setToken(receivedToken);
    setUser(receivedUser);
    localStorage.setItem(TOKEN_STORAGE_KEY, receivedToken);
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(receivedUser));

    return receivedUser;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
  };

  const updateUser = (partial: Partial<UserSummary>) => {
    setUser((prev) => {
      if (!prev) return null;
      const updated = { ...prev, ...partial };
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        role: user ? user.role : null,
        isAuthenticated: !!token && !!user,
        isLoadingAuth,
        login,
        register,
        logout,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
