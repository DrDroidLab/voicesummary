export type LLMProvider = 'openai' | 'anthropic' | 'grok' | 'custom';

export type LLMModel = 
  // OpenAI models
  | 'gpt-4o'
  | 'gpt-4-turbo'
  | 'gpt-4'
  | 'gpt-3.5-turbo'
  // Anthropic models
  | 'claude-3-5-sonnet-20241022'
  | 'claude-3-opus-20240229'
  | 'claude-3-sonnet-20240229'
  | 'claude-3-haiku-20240307'
  // Grok models
  | 'grok-beta'
  | 'grok-2'
  // Custom
  | 'custom';

export interface LLMModelOption {
  value: LLMModel;
  label: string;
  provider: LLMProvider;
  description?: string;
}

export interface PromptConfig {
  id: string;
  name: string;
  description?: string;
  prompt: string;
  model: LLMModel;
  provider: LLMProvider;
  taskType: 'extraction' | 'classification' | 'labeling' | 'summarization' | 'sentiment' | 'custom';
  enabled: boolean;
  temperature?: number;
  maxTokens?: number;
}

export interface LLMConfiguration {
  prompts: PromptConfig[];
  defaultModel: LLMModel;
  defaultProvider: LLMProvider;
}

