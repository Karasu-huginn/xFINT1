import { createContext, useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";

import { fetchCurrentUser, logIn, logOut } from "../api/auth";
import type { CurrentUser } from "../types/api";

export interface AuthState {
  currentUser: CurrentUser | null;
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  refresh: () => Promise<void>;
}

export const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(async () => {
    // The cookie is httpOnly, so the application cannot read a role out of it. The
    // server stays the only authority on who the caller is.
    try {
      setCurrentUser(await fetchCurrentUser());
    } catch {
      setCurrentUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const signIn = useCallback(
    async (email: string, password: string) => {
      await logIn(email, password);
      await refresh();
    },
    [refresh],
  );

  const signOut = useCallback(async () => {
    await logOut();
    setCurrentUser(null);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <AuthContext.Provider
      value={{ currentUser, isLoading, signIn, signOut, refresh }}
    >
      {children}
    </AuthContext.Provider>
  );
}
