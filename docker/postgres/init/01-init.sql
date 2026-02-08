-- Initialize pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create function for similarity search
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(384),
  match_threshold float,
  match_count int
)
RETURNS TABLE(
  id uuid,
  content text,
  document_id uuid,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id,
    dc.content,
    dc.document_id,
    1 - (dc.embedding <=> query_embedding) AS similarity
  FROM document_chunks dc
  WHERE dc.embedding IS NOT NULL
    AND 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
