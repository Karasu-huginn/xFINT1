import { useContext } from "react";

import { AuthContext } from "./AuthContext";
import type { AuthState } from "./AuthContext";

export function useAuth(): AuthState {
  const state = useContext(AuthContext);
  if (state === null) {
    throw new Error("useAuth must be used inside an AuthProvider");
  }
  return state;
}
