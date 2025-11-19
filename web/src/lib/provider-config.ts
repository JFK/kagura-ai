export interface ProviderConfig {
  id: string;
  name: string;
  keyNames: string[];
  placeholder: string;
  docsUrl: string;
  validation?: RegExp;
}

export const PROVIDERS: Record<string, ProviderConfig> = {
  openai: {
    id: 'openai',
    name: 'OpenAI',
    keyNames: ['OPENAI_API_KEY'],
    placeholder: 'sk-proj-...',
    docsUrl: 'https://platform.openai.com/api-keys',
    validation: /^sk-/
  },
  anthropic: {
    id: 'anthropic',
    name: 'Anthropic',
    keyNames: ['ANTHROPIC_API_KEY'],
    placeholder: 'sk-ant-...',
    docsUrl: 'https://console.anthropic.com/',
    validation: /^sk-ant-/
  },
  google: {
    id: 'google',
    name: 'Google (Gemini)',
    keyNames: ['GOOGLE_API_KEY'],
    placeholder: 'AIza...',
    docsUrl: 'https://aistudio.google.com/app/apikey',
    validation: /^AIza/
  },
  brave: {
    id: 'brave',
    name: 'Brave Search',
    keyNames: ['BRAVE_SEARCH_API_KEY'],
    placeholder: 'BSA...',
    docsUrl: 'https://brave.com/search/api/',
    validation: /^BSA/
  },
  cohere: {
    id: 'cohere',
    name: 'Cohere',
    keyNames: ['COHERE_API_KEY'],
    placeholder: 'co-...',
    docsUrl: 'https://dashboard.cohere.com/api-keys'
  }
};

/**
 * Get provider config by ID
 */
export function getProviderConfig(providerId: string): ProviderConfig | undefined {
  return PROVIDERS[providerId];
}

/**
 * Get all provider IDs
 */
export function getProviderIds(): string[] {
  return Object.keys(PROVIDERS);
}

/**
 * Get provider name by ID
 */
export function getProviderName(providerId: string): string {
  return PROVIDERS[providerId]?.name || providerId;
}
