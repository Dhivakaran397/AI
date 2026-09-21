"use client";

import { useEffect, useState, useMemo } from "react";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiClient } from "@/lib/api-client";
import { Brain, Plus, Trash2, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";

interface MemoryItem {
  id: string;
  user_id: string;
  type: "PREFERENCE" | "DECISION" | "KNOWLEDGE" | "PROJECT" | "SHORT_TERM";
  content: string;
  created_at: string;
}

const TYPE_COLORS: Record<string, string> = {
  PREFERENCE: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  DECISION: "bg-purple-500/10 text-purple-500 border-purple-500/20",
  KNOWLEDGE: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  PROJECT: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  SHORT_TERM: "bg-zinc-500/10 text-zinc-500 border-zinc-500/20",
};

export default function MemoryPage() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState("ALL");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newContent, setNewContent] = useState("");
  const [newType, setNewType] = useState<string>("PREFERENCE");
  const [submitting, setSubmitting] = useState(false);

  const fetchMemories = async () => {
    try {
      setLoading(true);
      const data = await apiClient.get<MemoryItem[]>("/memories");
      setMemories(data);
    } catch {
      toast.error("Failed to load memories");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, []);

  const handleCreate = async () => {
    if (!newContent.trim()) return;
    try {
      setSubmitting(true);
      const created = await apiClient.post<MemoryItem>("/memories", {
        content: newContent.trim(),
        type: newType,
      });
      setMemories([created, ...memories]);
      setNewContent("");
      setDialogOpen(false);
      toast.success("Memory saved successfully");
    } catch {
      toast.error("Failed to save memory");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiClient.delete(`/memories/${id}`);
      setMemories(memories.filter((m) => m.id !== id));
      toast.success("Memory deleted");
    } catch {
      toast.error("Failed to delete memory");
    }
  };

  const filteredMemories = useMemo(() => {
    if (selectedType === "ALL") return memories;
    return memories.filter((m) => m.type === selectedType);
  }, [memories, selectedType]);

  return (
    <>
      <Header title="Memory" />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-5xl mx-auto space-y-6">
          {/* Top Banner */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                <Brain className="h-6 w-6 text-primary" />
                Memory System
              </h1>
              <p className="text-muted-foreground mt-1 text-sm">
                DAI retains persistent user preferences, architectural decisions, and context across sessions.
              </p>
            </div>

            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger render={<Button className="gap-2 shrink-0" />}>
                <Plus className="h-4 w-4" />
                Add Memory
              </DialogTrigger>
              <DialogContent className="sm:max-w-[480px]">
                <DialogHeader>
                  <DialogTitle>Save to Long-Term Memory</DialogTitle>
                  <DialogDescription>
                    Store an explicit preference, decision, or project knowledge item that DAI will reference.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-3">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Memory Type</label>
                    <Select value={newType} onValueChange={(v) => v && setNewType(v)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="PREFERENCE">Preference (Style, frameworks, rules)</SelectItem>
                        <SelectItem value="DECISION">Decision (Architecture, choices made)</SelectItem>
                        <SelectItem value="KNOWLEDGE">Knowledge (Domain facts, specifications)</SelectItem>
                        <SelectItem value="PROJECT">Project (Goals, constraints)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Content</label>
                    <Textarea
                      placeholder="e.g. 'I prefer Tailwind CSS for styling and always use TypeScript strict mode.'"
                      value={newContent}
                      onChange={(e) => setNewContent(e.target.value)}
                      rows={4}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setDialogOpen(false)}
                    disabled={submitting}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleCreate}
                    disabled={!newContent.trim() || submitting}
                    className="gap-2"
                  >
                    {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                    Save Memory
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {/* Type Filter Tabs */}
          <Tabs value={selectedType} onValueChange={setSelectedType} className="w-full">
            <TabsList className="grid w-full grid-cols-5 max-w-xl">
              <TabsTrigger value="ALL">All ({memories.length})</TabsTrigger>
              <TabsTrigger value="PREFERENCE">Preferences</TabsTrigger>
              <TabsTrigger value="DECISION">Decisions</TabsTrigger>
              <TabsTrigger value="KNOWLEDGE">Knowledge</TabsTrigger>
              <TabsTrigger value="PROJECT">Project</TabsTrigger>
            </TabsList>
          </Tabs>

          {/* Memory List */}
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : filteredMemories.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center border border-dashed rounded-xl bg-muted/20">
              <Sparkles className="h-10 w-10 text-muted-foreground mb-3" />
              <h3 className="text-base font-semibold">No memories found</h3>
              <p className="text-sm text-muted-foreground max-w-sm mt-1 mb-4">
                {selectedType === "ALL"
                  ? "You haven't saved any long-term memories yet. Add your first preference or decision."
                  : `No memories categorized under ${selectedType.toLowerCase()}.`}
              </p>
              <Button
                variant="outline"
                size="sm"
                className="gap-2"
                onClick={() => setDialogOpen(true)}
              >
                <Plus className="h-4 w-4" />
                Add Memory
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {filteredMemories.map((mem) => (
                <Card key={mem.id} className="transition-shadow hover:shadow-sm">
                  <CardContent className="p-4 flex items-start justify-between gap-4">
                    <div className="space-y-1.5 flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant="outline"
                          className={`text-[10px] uppercase font-mono px-2 py-0.5 border ${
                            TYPE_COLORS[mem.type] || TYPE_COLORS.SHORT_TERM
                          }`}
                        >
                          {mem.type}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {new Date(mem.created_at).toLocaleDateString(undefined, {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })}
                        </span>
                      </div>
                      <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                        {mem.content}
                      </p>
                    </div>

                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-destructive shrink-0"
                      onClick={() => handleDelete(mem.id)}
                      title="Delete memory"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
