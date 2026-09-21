"use client";

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiClient } from "@/lib/api-client";
import type { Document, DocumentSearchResult, Project } from "@/types";
import {
  BookOpen,
  Plus,
  Search,
  FileText,
  Trash2,
  Loader2,
  Sparkles,
  Database,
  Layers,
  CheckCircle2,
  AlertCircle,
  Eye,
  FileCode,
} from "lucide-react";
import { toast } from "sonner";

export default function KnowledgePage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  // Ingest Modal State
  const [ingestOpen, setIngestOpen] = useState(false);
  const [newFilename, setNewFilename] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newProjectId, setNewProjectId] = useState("");
  const [isIngesting, setIsIngesting] = useState(false);

  // Search Playground State
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<DocumentSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // Chunks Inspector Modal State
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [loadingDocDetail, setLoadingDocDetail] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [docs, projs] = await Promise.all([
        apiClient.get<Document[]>("/api/v1/documents").catch(() => []),
        apiClient.get<Project[]>("/api/v1/projects").catch(() => []),
      ]);
      setDocuments(docs || []);
      setProjects(projs || []);
    } catch (err) {
      console.error("Failed to load knowledge base:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleIngest = async () => {
    if (!newFilename.trim() || !newContent.trim()) {
      toast.error("Filename and content are required.");
      return;
    }

    setIsIngesting(true);
    try {
      await apiClient.post("/api/v1/documents", {
        filename: newFilename.trim(),
        content: newContent.trim(),
        file_type: newFilename.endsWith(".md") ? "text/markdown" : "text/plain",
        project_id: newProjectId || undefined,
      });
      toast.success(`Ingested '${newFilename}' and created semantic chunks.`);
      setIngestOpen(false);
      setNewFilename("");
      setNewContent("");
      setNewProjectId("");
      fetchData();
    } catch (err: any) {
      toast.error(err?.message || "Failed to ingest document");
    } finally {
      setIsIngesting(false);
    }
  };

  const handleDelete = async (docId: string, filename: string) => {
    try {
      await apiClient.delete(`/api/v1/documents/${docId}`);
      toast.success(`Removed '${filename}' from knowledge base.`);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (err: any) {
      toast.error(err?.message || "Failed to delete document");
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    try {
      const results = await apiClient.post<DocumentSearchResult[]>("/api/v1/documents/search", {
        query: searchQuery.trim(),
        top_k: 5,
      });
      setSearchResults(results || []);
    } catch (err: any) {
      toast.error(err?.message || "Semantic search failed");
    } finally {
      setIsSearching(false);
    }
  };

  const handleViewChunks = async (doc: Document) => {
    setSelectedDoc(doc);
    setLoadingDocDetail(true);
    try {
      const detailed = await apiClient.get<Document>(`/api/v1/documents/${doc.id}`);
      setSelectedDoc(detailed);
    } catch (err: any) {
      toast.error("Failed to load chunk details");
    } finally {
      setLoadingDocDetail(false);
    }
  };

  const totalChunks = documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0);
  const totalBytes = documents.reduce((acc, d) => acc + (d.file_size || 0), 0);

  return (
    <>
      <Header title="Knowledge Base & RAG" />
      <div className="flex-1 space-y-6 overflow-auto p-6">
        {/* Top Header & Actions */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight">Project & Domain Knowledge</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Ingest technical documentation, architecture blueprints, and API specs into 1536-dim semantic embeddings.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              onClick={() => setIngestOpen(true)}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              <Plus className="mr-1.5 h-4 w-4" /> Ingest Document
            </Button>
          </div>
        </div>

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-600">
                <BookOpen className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Indexed Documents</p>
                <p className="text-lg font-bold">{documents.length}</p>
              </div>
            </div>
          </Card>
          <Card className="p-4 border-emerald-500/30 bg-emerald-500/5">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600">
                <Layers className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Semantic Chunks</p>
                <p className="text-lg font-bold font-mono text-emerald-600 dark:text-emerald-400">
                  {totalChunks}
                </p>
              </div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-500/10 text-blue-600">
                <Database className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Vector Store Volume</p>
                <p className="text-lg font-bold font-mono">
                  {(totalBytes / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Semantic Search Playground */}
        <Card className="border-border/60 bg-muted/20">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-indigo-500" />
                <CardTitle className="text-sm font-semibold">Semantic Vector Search Playground</CardTitle>
              </div>
              <Badge variant="outline" className="text-[10px] font-mono">
                Cosine Similarity Ranking
              </Badge>
            </div>
            <CardDescription className="text-xs">
              Query your indexed documents in natural language to inspect matched semantic passages.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  placeholder="e.g. How does token authentication and password hashing work?"
                  className="pl-8 text-xs font-mono"
                  disabled={isSearching}
                />
              </div>
              <Button
                size="sm"
                onClick={handleSearch}
                disabled={isSearching || !searchQuery.trim()}
                className="shrink-0"
              >
                {isSearching ? (
                  <>
                    <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> Searching...
                  </>
                ) : (
                  <>
                    <Search className="mr-1.5 h-3.5 w-3.5" /> Query Vectors
                  </>
                )}
              </Button>
            </div>

            {/* Results Grid */}
            {searchResults.length > 0 && (
              <div className="space-y-2 pt-2">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Top Relevant Passages ({searchResults.length})
                </p>
                <div className="space-y-2">
                  {searchResults.map((res) => (
                    <div
                      key={res.chunk_id}
                      className="rounded-lg border border-border/50 bg-background/90 p-3 text-xs shadow-xs"
                    >
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <div className="flex items-center gap-2">
                          <FileText className="h-3.5 w-3.5 text-indigo-500" />
                          <span className="font-semibold font-mono">{res.filename}</span>
                          <span className="text-[11px] text-muted-foreground font-mono">
                            (chunk #{res.chunk_index + 1})
                          </span>
                        </div>
                        <Badge
                          className={`text-[10px] font-mono ${
                            res.similarity_score > 0.6
                              ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                              : "bg-indigo-500/10 text-indigo-600 border-indigo-500/20"
                          }`}
                        >
                          Score: {(res.similarity_score * 100).toFixed(1)}%
                        </Badge>
                      </div>
                      <p className="text-muted-foreground font-mono text-[11px] leading-relaxed bg-muted/40 p-2 rounded">
                        {res.content}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Documents Grid */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
            Ingested Knowledge Documents
          </h3>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : documents.length === 0 ? (
            <Card className="p-8 text-center text-xs text-muted-foreground">
              No documents ingested yet. Click &quot;Ingest Document&quot; above to add your first architecture doc or spec.
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {documents.map((doc) => (
                <Card key={doc.id} className="relative flex flex-col justify-between hover:shadow-md transition-all">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2.5">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-600">
                          <FileCode className="h-4 w-4" />
                        </div>
                        <div className="min-w-0">
                          <CardTitle className="text-sm font-semibold truncate">
                            {doc.filename}
                          </CardTitle>
                          <p className="text-[11px] text-muted-foreground font-mono">
                            {(doc.file_size / 1024).toFixed(1)} KB &bull; {doc.file_type}
                          </p>
                        </div>
                      </div>
                      <Badge variant="outline" className="text-[10px] font-mono shrink-0">
                        {doc.chunk_count} chunks
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="flex items-center justify-between pt-0 border-t border-border/40 py-2.5">
                    <span className="text-[11px] text-muted-foreground">
                      {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : "-"}
                    </span>
                    <div className="flex items-center gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-7 px-2 text-xs"
                        onClick={() => handleViewChunks(doc)}
                      >
                        <Eye className="mr-1 h-3.5 w-3.5" /> Chunks
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-7 w-7 p-0 text-destructive hover:bg-destructive/10"
                        onClick={() => handleDelete(doc.id, doc.filename)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Ingest Document Modal */}
      <Dialog open={ingestOpen} onOpenChange={setIngestOpen}>
        <DialogContent className="max-w-xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Ingest Document into Knowledge Base</DialogTitle>
            <DialogDescription>
              DAI partitions the text into overlapping semantic windows and computes vector embeddings.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Filename / Title
              </label>
              <Input
                value={newFilename}
                onChange={(e) => setNewFilename(e.target.value)}
                placeholder="e.g. system_architecture.md or api_contracts.txt"
                disabled={isIngesting}
                className="font-mono text-xs"
              />
            </div>

            {projects.length > 0 && (
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Associated Project (Optional)
                </label>
                <select
                  value={newProjectId}
                  onChange={(e) => setNewProjectId(e.target.value)}
                  disabled={isIngesting}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value="">Global (All Projects)</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Document Contents (Markdown / Text)
              </label>
              <textarea
                rows={8}
                value={newContent}
                onChange={(e) => setNewContent(e.target.value)}
                placeholder="Paste technical requirements, database schemas, or API docs here..."
                disabled={isIngesting}
                className="w-full rounded-md border border-input bg-background p-2 font-mono text-xs shadow-sm focus:outline-none focus:ring-1 focus:ring-ring resize-none"
              />
            </div>

            <Button
              onClick={handleIngest}
              disabled={isIngesting || !newFilename.trim() || !newContent.trim()}
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              {isIngesting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Chunking & Computing Embeddings...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" /> Partition & Ingest
                </>
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Chunks Inspector Modal */}
      <Dialog open={Boolean(selectedDoc)} onOpenChange={(open) => !open && setSelectedDoc(null)}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-indigo-500" />
              <span>Chunks for {selectedDoc?.filename}</span>
            </DialogTitle>
            <DialogDescription>
              Inspect partitioned passages stored with vector embeddings for semantic recall.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            {loadingDocDetail ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : selectedDoc?.chunks && selectedDoc.chunks.length > 0 ? (
              selectedDoc.chunks.map((chunk) => (
                <div
                  key={chunk.id}
                  className="rounded-lg border border-border/50 bg-muted/20 p-3 text-xs font-mono space-y-1"
                >
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                    <span>Chunk #{chunk.chunk_index + 1}</span>
                    <span>{chunk.content.length} characters</span>
                  </div>
                  <p className="text-foreground leading-relaxed whitespace-pre-wrap">
                    {chunk.content}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-xs text-muted-foreground text-center py-6">
                No chunks available for this document.
              </p>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
