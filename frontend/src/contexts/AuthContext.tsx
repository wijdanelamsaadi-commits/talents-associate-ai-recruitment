import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";

import {
  AuthUser,
  clearStoredAuth,
  getCurrentRecruiter,
  getStoredToken,
  getStoredUser,
  loginRecruiter,
  registerRecruiter,
  storeAuth,
} from "../services/auth";

type LoginInput = {
  email: string;
  password: string;
};

type RegisterInput = LoginInput & {
  full_name: string;
};

type AuthContextValue = {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isCheckingAuth: boolean;
  login: (input: LoginInput) => Promise<void>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [user, setUser] = useState<AuthUser | null>(() => getStoredUser());
  const [isCheckingAuth, setIsCheckingAuth] = useState(Boolean(getStoredToken()));

  useEffect(() => {
    let isMounted = true;

    async function refreshUser() {
      if (!getStoredToken()) {
        setIsCheckingAuth(false);
        return;
      }

      try {
        const currentUser = await getCurrentRecruiter();
        if (isMounted) {
          setUser(currentUser);
          setToken(getStoredToken());
        }
      } catch {
        clearStoredAuth();
        if (isMounted) {
          setUser(null);
          setToken(null);
        }
      } finally {
        if (isMounted) {
          setIsCheckingAuth(false);
        }
      }
    }

    refreshUser();

    return () => {
      isMounted = false;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token && user),
      isCheckingAuth,
      login: async (input) => {
        const response = await loginRecruiter(input);
        setToken(response.access_token);
        setUser(response.user);
      },
      register: async (input) => {
        const response = await registerRecruiter(input);
        setToken(response.access_token);
        setUser(response.user);
      },
      logout: () => {
        clearStoredAuth();
        setToken(null);
        setUser(null);
      },
    }),
    [isCheckingAuth, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }
  return context;
}
