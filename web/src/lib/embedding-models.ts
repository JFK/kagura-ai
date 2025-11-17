export interface EmbeddingModel {
  id: string;
  name: string;
  dimensions: number;
  cost?: string;  // For API models
  ram?: string;   // For local models
}

export const EMBEDDING_MODELS: Record<string, EmbeddingModel[]> = {
  openai: [
    { id: 'text-embedding-3-small', name: 'Small (1536D)', dimensions: 1536, cost: '$0.02/1M tokens' },
    { id: 'text-embedding-3-large', name: 'Large (3072D)', dimensions: 3072, cost: '$0.13/1M tokens' },
    { id: 'text-embedding-ada-002', name: 'Ada-002 (Legacy)', dimensions: 1536, cost: '$0.10/1M tokens' }
  ],
  local: [
    { id: 'intfloat/multilingual-e5-large', name: 'E5 Large (1024D)', dimensions: 1024, ram: '8GB+ RAM' },
    { id: 'intfloat/multilingual-e5-base', name: 'E5 Base (768D)', dimensions: 768, ram: '4GB+ RAM' },
    { id: 'all-MiniLM-L6-v2', name: 'MiniLM (384D)', dimensions: 384, ram: '2GB+ RAM' }
  ]
};

/**
 * Get embedding models for a specific provider
 */
export function getEmbeddingModels(provider: string): EmbeddingModel[] {
  return EMBEDDING_MODELS[provider] || [];
}

/**
 * Get embedding model details by ID
 */
export function getEmbeddingModel(provider: string, modelId: string): EmbeddingModel | undefined {
  const models = EMBEDDING_MODELS[provider] || [];
  return models.find(m => m.id === modelId);
}

/**
 * Get all supported embedding providers
 */
export function getEmbeddingProviders(): string[] {
  return Object.keys(EMBEDDING_MODELS);
}
