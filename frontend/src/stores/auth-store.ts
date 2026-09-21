import { create } from "zustand";
import { apiClient, ApiError } from "@/lib/api-client";
import type { User } from "@/types/user";
import type { Token } from "@/types/api";

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    fullName: string
  ) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token:
    typeof window !== "undefined"
      ? localStorage.getItem("dai_token")
      : null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const formData = new FormData();
      formData.append("username", email);
      formData.append("password", password);

      const data = await apiClient.postForm<Token>("/auth/login", formData);
      localStorage.setItem("dai_token", data.access_token);
      localStorage.setItem("dai_refresh_token", data.refresh_token);
      set({ token: data.access_token, isLoading: false });
      await get().checkAuth();
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Login failed. Please try again.";
      set({ isLoading: false, error: message });
      throw err;
    }
  },

  register: async (email: string, password: string, fullName: string) => {
    set({ isLoading: true, error: null });
    try {
      await apiClient.post("/auth/register", {
        email,
        password,
        full_name: fullName,
      });
      await get().login(email, password);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Registration failed. Please try again.";
      set({ isLoading: false, error: message });
      throw err;
    }
  },

  logout: () => {
    localStorage.removeItem("dai_token");
    localStorage.removeItem("dai_refresh_token");
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      error: null,
    });
  },

  checkAuth: async () => {
    const token = get().token;
    if (!token) {
      set({ isAuthenticated: false, user: null });
      return;
    }
    try {
      const user = await apiClient.get<User>("/auth/me");
      set({ user, isAuthenticated: true });
    } catch {
      set({ user: null, isAuthenticated: false, token: null });
      localStorage.removeItem("dai_token");
    }
  },

  clearError: () => set({ error: null }),
}));
