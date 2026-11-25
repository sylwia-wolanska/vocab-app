import { useQueryClient } from "@tanstack/react-query";
import {
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import { setUnauthorizedHandler, tokenStorage } from "../api/client";
import { AuthContext } from "./AuthContext";

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [token, setToken] = useState(() => tokenStorage.get());

  const logIn = useCallback((newToken: string) => {
    tokenStorage.set(newToken);
    setToken(newToken);
  }, []);

  const logOut = useCallback(() => {
    tokenStorage.clear();
    queryClient.clear();
    setToken(null);
  }, [queryClient]);

  useEffect(() => {
    setUnauthorizedHandler(logOut);
    return () => setUnauthorizedHandler(() => {});
  }, [logOut]);

  const value = useMemo(
    () => ({ token, logIn, logOut }),
    [token, logIn, logOut],
  );

  return <AuthContext value={value}>{children}</AuthContext>;
}
