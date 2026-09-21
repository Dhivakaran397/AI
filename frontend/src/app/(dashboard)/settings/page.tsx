"use client";

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { useAuthStore } from "@/stores/auth-store";
import { useTheme } from "next-themes";
import { apiClient } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import { Save, Loader2, Key, Eye, EyeOff, Sparkles, Cpu, Sliders, Palette, Sun, Moon, Monitor } from "lucide-react";
import { toast } from "sonner";

interface SettingsData {
  ai_provider: string;
  ai_model: string;
  theme: string;
  preferences?: {
    openai_api_key?: string;
    anthropic_api_key?: string;
    google_api_key?: string;
    ollama_base_url?: string;
    temperature?: number;
    custom_system_prompt?: string;
  } | null;
}

const PROVIDER_MODELS: Record<string, string[]> = {
  openai: ["gpt-4o", "gpt-4o-mini", "o1-preview", "o3-mini"],
  anthropic: ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
  google: ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash-exp"],
  ollama: ["llama3.3:latest", "qwen2.5-coder:32b", "deepseek-r1:14b", "mistral:latest"],
};

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [mounted, setMounted] = useState(false);
  const { theme, resolvedTheme, setTheme } = useTheme();
  const [selectedTheme, setSelectedTheme] = useState<string>("dark");

  useEffect(() => {
    setMounted(true);
  }, []);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Settings fields
  const [aiProvider, setAiProvider] = useState<string>("openai");
  const [aiModel, setAiModel] = useState<string>("gpt-4o");
  const [temperature, setTemperature] = useState<number>(0.7);
  const [customPrompt, setCustomPrompt] = useState<string>("");

  // API Keys
  const [openaiKey, setOpenaiKey] = useState<string>("");
  const [anthropicKey, setAnthropicKey] = useState<string>("");
  const [googleKey, setGoogleKey] = useState<string>("");
  const [ollamaUrl, setOllamaUrl] = useState<string>("http://localhost:11434");

  // Show/hide key masks
  const [showOpenai, setShowOpenai] = useState(false);
  const [showAnthropic, setShowAnthropic] = useState(false);
  const [showGoogle, setShowGoogle] = useState(false);

  const fetchSettings = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiClient.get<SettingsData>("/api/v1/settings");
      if (data) {
        setAiProvider(data.ai_provider || "openai");
        setAiModel(data.ai_model || "gpt-4o");
        if (data.theme) {
          setSelectedTheme(data.theme);
          setTheme(data.theme);
        }
        if (data.preferences) {
          setOpenaiKey(data.preferences.openai_api_key || "");
          setAnthropicKey(data.preferences.anthropic_api_key || "");
          setGoogleKey(data.preferences.google_api_key || "");
          setOllamaUrl(data.preferences.ollama_base_url || "http://localhost:11434");
          if (typeof data.preferences.temperature === "number") {
            setTemperature(data.preferences.temperature);
          }
          setCustomPrompt(data.preferences.custom_system_prompt || "");
        }
      }
    } catch (err) {
      console.error("Failed to load settings:", err);
    } finally {
      setLoading(false);
    }
  }, [setTheme]);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const handleProviderChange = (newProvider: string) => {
    setAiProvider(newProvider);
    const available = PROVIDER_MODELS[newProvider];
    if (available && available.length > 0) {
      setAiModel(available[0]);
    }
  };

  const handleThemeChange = (newTheme: string) => {
    setSelectedTheme(newTheme);
    setTheme(newTheme);
    apiClient.put("/api/v1/settings", { theme: newTheme }).catch(() => {});
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiClient.put("/api/v1/settings", {
        ai_provider: aiProvider,
        ai_model: aiModel,
        theme: selectedTheme || theme || "dark",
        preferences: {
          openai_api_key: openaiKey.trim() || undefined,
          anthropic_api_key: anthropicKey.trim() || undefined,
          google_api_key: googleKey.trim() || undefined,
          ollama_base_url: ollamaUrl.trim() || undefined,
          temperature,
          custom_system_prompt: customPrompt.trim() || undefined,
        },
      });
      toast.success("Settings and API keys saved successfully.");
    } catch (err: any) {
      toast.error(err?.message || "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Header title="Settings" />
      <div className="flex-1 overflow-auto">
        <div className="max-w-3xl mx-auto p-6 space-y-6">
          {/* User Profile */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold">User Profile</CardTitle>
              <CardDescription className="text-xs">Your account identifier and credentials</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="space-y-1.5">
                <label className="font-medium text-muted-foreground">Email Address</label>
                <Input value={user?.email || "user@dai.local"} disabled className="text-xs font-mono" />
              </div>
              <div className="space-y-1.5">
                <label className="font-medium text-muted-foreground">Full Name</label>
                <Input value={user?.full_name || "DAI Developer"} disabled className="text-xs" />
              </div>
            </CardContent>
          </Card>

          {/* AI Provider & Models */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Cpu className="h-4 w-4 text-indigo-500" />
                <CardTitle className="text-base font-semibold">AI Intelligence Engine</CardTitle>
              </div>
              <CardDescription className="text-xs">
                Select your primary model provider and default reasoning architecture
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="font-medium text-muted-foreground">Provider</label>
                  <Select value={aiProvider} onValueChange={(val) => { if (val) handleProviderChange(val); }}>
                    <SelectTrigger className="text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="openai">OpenAI (GPT-4o, o1, o3)</SelectItem>
                      <SelectItem value="anthropic">Anthropic (Claude 3.5 Sonnet)</SelectItem>
                      <SelectItem value="google">Google Gemini (Gemini 1.5/2.0)</SelectItem>
                      <SelectItem value="ollama">Ollama (Local Open Weights)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-1.5">
                  <label className="font-medium text-muted-foreground">Model Name</label>
                  <Select value={aiModel} onValueChange={(val) => { if (val) setAiModel(val); }}>
                    <SelectTrigger className="text-xs font-mono">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {(PROVIDER_MODELS[aiProvider] || [aiModel]).map((m) => (
                        <SelectItem key={m} value={m} className="font-mono text-xs">
                          {m}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Temperature */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="font-medium text-muted-foreground">Generation Temperature</label>
                  <span className="font-mono text-xs font-bold">{temperature}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-muted rounded-lg appearance-none cursor-pointer accent-indigo-600"
                />
              </div>

              {/* Custom System Prompt */}
              <div className="space-y-1.5">
                <label className="font-medium text-muted-foreground">
                  Custom System Instructions (Developer Prompt)
                </label>
                <textarea
                  rows={3}
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  placeholder="e.g. Always write clean TypeScript code with strict types and prefer Tailwind CSS."
                  className="w-full rounded-md border border-input bg-background p-2 text-xs shadow-xs focus:outline-none focus:ring-1 focus:ring-ring resize-none"
                />
              </div>
            </CardContent>
          </Card>

          {/* API Keys Configuration */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Key className="h-4 w-4 text-amber-500" />
                <CardTitle className="text-base font-semibold">API Credentials & Endpoints</CardTitle>
              </div>
              <CardDescription className="text-xs">
                Credentials are encrypted and used for direct API streaming
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              {/* OpenAI Key */}
              <div className="space-y-1.5">
                <label className="font-medium text-muted-foreground">OpenAI API Key</label>
                <div className="relative">
                  <Input
                    type={showOpenai ? "text" : "password"}
                    value={openaiKey}
                    onChange={(e) => setOpenaiKey(e.target.value)}
                    placeholder="sk-proj-..."
                    className="pr-9 text-xs font-mono"
                  />
                  <button
                    type="button"
                    onClick={() => setShowOpenai(!showOpenai)}
                    className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
                  >
                    {showOpenai ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* Anthropic Key */}
              <div className="space-y-1.5">
                <label className="font-medium text-muted-foreground">Anthropic API Key</label>
                <div className="relative">
                  <Input
                    type={showAnthropic ? "text" : "password"}
                    value={anthropicKey}
                    onChange={(e) => setAnthropicKey(e.target.value)}
                    placeholder="sk-ant-..."
                    className="pr-9 text-xs font-mono"
                  />
                  <button
                    type="button"
                    onClick={() => setShowAnthropic(!showAnthropic)}
                    className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
                  >
                    {showAnthropic ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* Google AI Key */}
              <div className="space-y-1.5">
                <label className="font-medium text-muted-foreground">Google AI API Key</label>
                <div className="relative">
                  <Input
                    type={showGoogle ? "text" : "password"}
                    value={googleKey}
                    onChange={(e) => setGoogleKey(e.target.value)}
                    placeholder="AIzaSy..."
                    className="pr-9 text-xs font-mono"
                  />
                  <button
                    type="button"
                    onClick={() => setShowGoogle(!showGoogle)}
                    className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
                  >
                    {showGoogle ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* Ollama URL */}
              {aiProvider === "ollama" && (
                <div className="space-y-1.5">
                  <label className="font-medium text-muted-foreground">Ollama Server Base URL</label>
                  <Input
                    value={ollamaUrl}
                    onChange={(e) => setOllamaUrl(e.target.value)}
                    placeholder="http://localhost:11434"
                    className="text-xs font-mono"
                  />
                </div>
              )}
            </CardContent>
          </Card>

          {/* Appearance & Theme */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Palette className="h-4 w-4 text-cyan-500" />
                <CardTitle className="text-base font-semibold">Appearance & UI Theme</CardTitle>
              </div>
              <CardDescription className="text-xs">
                Customize the interface color theme with instant switching
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {/* Dark Card */}
                <button
                  type="button"
                  onClick={() => handleThemeChange("dark")}
                  className={cn(
                    "flex flex-col items-center gap-2 p-4 rounded-xl border text-center transition-all cursor-pointer",
                    (selectedTheme === "dark" || (selectedTheme === "system" && resolvedTheme === "dark"))
                      ? "border-primary bg-primary/10 shadow-sm ring-2 ring-primary"
                      : "border-border/60 hover:border-border hover:bg-muted/40"
                  )}
                >
                  <div className="h-10 w-10 rounded-lg bg-zinc-900 border border-zinc-700 flex items-center justify-center text-amber-400 shadow-inner">
                    <Moon className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="font-semibold text-xs text-foreground">Dark Mode</div>
                    <div className="text-[11px] text-muted-foreground">Cyberpunk Studio</div>
                  </div>
                </button>

                {/* Light Card */}
                <button
                  type="button"
                  onClick={() => handleThemeChange("light")}
                  className={cn(
                    "flex flex-col items-center gap-2 p-4 rounded-xl border text-center transition-all cursor-pointer",
                    selectedTheme === "light"
                      ? "border-primary bg-primary/10 shadow-sm ring-2 ring-primary"
                      : "border-border/60 hover:border-border hover:bg-muted/40"
                  )}
                >
                  <div className="h-10 w-10 rounded-lg bg-zinc-100 border border-zinc-300 flex items-center justify-center text-amber-500 shadow-sm">
                    <Sun className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="font-semibold text-xs text-foreground">Light Mode</div>
                    <div className="text-[11px] text-muted-foreground">Clean Studio</div>
                  </div>
                </button>

                {/* System Default Card */}
                <button
                  type="button"
                  onClick={() => handleThemeChange("system")}
                  className={cn(
                    "flex flex-col items-center gap-2 p-4 rounded-xl border text-center transition-all cursor-pointer",
                    selectedTheme === "system"
                      ? "border-primary bg-primary/10 shadow-sm ring-2 ring-primary"
                      : "border-border/60 hover:border-border hover:bg-muted/40"
                  )}
                >
                  <div className="h-10 w-10 rounded-lg bg-muted border border-border flex items-center justify-center text-indigo-400">
                    <Monitor className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="font-semibold text-xs text-foreground">System Default</div>
                    <div className="text-[11px] text-muted-foreground">Match OS Setting</div>
                  </div>
                </button>
              </div>
            </CardContent>
          </Card>

          {/* Action Button */}
          <div className="flex justify-end pt-2">
            <Button
              onClick={handleSave}
              disabled={saving}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              {saving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving Configuration...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" /> Save Settings
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </>
  );
}
