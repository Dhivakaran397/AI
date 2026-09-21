export interface DocumentChunk {
  id: string;
  chunk_index: number;
  content: string;
  metadata_?: Record<string, any>;
  created_at?: string;
}

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  storage_path: string;
  project_id?: string;
  created_at?: string;
  chunk_count: number;
  chunks: DocumentChunk[];
}

export interface DocumentCreate {
  filename: string;
  content: string;
  file_type?: string;
  project_id?: string;
  metadata?: Record<string, any>;
}

export interface DocumentSearchResult {
  chunk_id: string;
  document_id: string;
  filename: string;
  chunk_index: number;
  content: string;
  similarity_score: number;
  metadata_?: Record<string, any>;
}
