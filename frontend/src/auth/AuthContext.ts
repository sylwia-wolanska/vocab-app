import { createContext, useContext } from "react";

export type AuthState = {
  token: string | null;
  logIn: (token: string) => void;
  logOut: () => void;
};

export const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const auth = useContext(AuthContext);
  if (auth === null) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return auth;
}
