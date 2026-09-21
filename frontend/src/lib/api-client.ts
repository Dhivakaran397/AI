import { API_URL } from "./constants";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("dai_token");
  }

  private resolveUrl(endpoint: string): string {
    if (endpoint.startsWith("http://") || endpoint.startsWith("https://")) {
      return endpoint;
    }
    const base = this.baseUrl.replace(/\/+$/, "");
    let path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    if (base.endsWith("/api/v1") && path.startsWith("/api/v1/")) {
      path = path.slice(7);
    } else if (base.endsWith("/api/v1") && path === "/api/v1") {
      path = "";
    }
    return `${base}${path}`;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (token) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(this.resolveUrl(endpoint), {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: "An unexpected error occurred",
      }));
      throw new ApiError(
        error.detail || "Request failed",
        response.status
      );
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "GET" });
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PATCH",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE" });
  }

  async postForm<T>(endpoint: string, data: FormData): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(this.resolveUrl(endpoint), {
      method: "POST",
      headers,
      body: data,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: "An unexpected error occurred",
      }));
      throw new ApiError(error.detail || "Request failed", response.status);
    }

    return response.json();
  }

  createSSEConnection(
    endpoint: string,
    onMessage: (data: string) => void,
    onError?: (error: Event) => void,
    onOpen?: () => void
  ): EventSource {
    const token = this.getToken();
    const url = new URL(this.resolveUrl(endpoint));
    if (token) {
      url.searchParams.set("token", token);
    }

    const eventSource = new EventSource(url.toString());

    eventSource.onmessage = (event) => {
      onMessage(event.data);
    };

    eventSource.onerror = (error) => {
      if (onError) onError(error);
    };

    if (onOpen) {
      eventSource.onopen = onOpen;
    }

    return eventSource;
  }

  async downloadFile(endpoint: string, fallbackFilename: string = "project.zip"): Promise<void> {
    const token = this.getToken();
    const headers: HeadersInit = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(this.resolveUrl(endpoint), {
      method: "GET",
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: "Failed to download project archive",
      }));
      throw new ApiError(error.detail || "Download failed", response.status);
    }

    let filename = fallbackFilename;
    const disposition = response.headers.get("Content-Disposition");
    if (disposition && disposition.includes("filename=")) {
      const match = disposition.match(/filename=["']?([^"';]+)["']?/);
      if (match && match[1]) {
        filename = match[1].trim();
      }
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export const apiClient = new ApiClient();
