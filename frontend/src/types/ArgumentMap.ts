/**
 * TypeScript interfaces for the Argument Cartographer
 * Defines the data structure contract between Flask backend and React frontend
 */

// Element types that can appear in an argument map
export type ArgumentElementType = 
  | 'Thesis'
  | 'Supporting Claim'
  | 'Evidence'
  | 'Counterclaim'
  | 'Logical Fallacy';

// Individual element in the argument map
export interface ArgumentElement {
  id: string;
  type: ArgumentElementType;
  parentId: string | null;
  content: string;
  sourceText: string | null;
}

// Complete argument map structure from backend
export interface ArgumentMap {
  title: string;
  elements: ArgumentElement[];
}

// API response from Flask backend
export interface BackendResponse {
  data: string; // JSON string containing the argument map
  argument_map: ArgumentMap; // Parsed argument map for validation
  sources: string[]; // Array of source URLs
}

// Error response from backend
export interface BackendError {
  error: string;
  raw_response?: string;
  sources?: string[];
}

// Visualization styles available in the UI
export type VisualizationStyle = 'Classic Tree' | 'Org Chart' | 'Pillar View';

// Input methods supported by the application
export type InputMethod = 'text' | 'url' | 'document';

// Form data for analysis request
export interface AnalysisRequest {
  question: string;
  inputMethod: InputMethod;
  content?: string; // For text input
  url?: string; // For URL input
  file?: File; // For document upload
}

// Node data for React Flow visualization
export interface FlowNodeData {
  label: string;
  type: ArgumentElementType;
  content: string;
  sourceText?: string;
  sources?: string[];
}

// Edge data for React Flow connections
export interface FlowEdgeData {
  label?: string;
}

// Position interface for node positioning
export interface NodePosition {
  x: number;
  y: number;
}

// Layout configuration for different visualization styles
export interface LayoutConfig {
  nodeSpacing: {
    horizontal: number;
    vertical: number;
  };
  levelHeight: number;
  nodeWidth: number;
  nodeHeight: number;
}

// UI state management
export interface AppState {
  isLoading: boolean;
  argumentMap: ArgumentMap | null;
  sources: string[];
  error: string | null;
  currentStyle: VisualizationStyle;
  inputMethod: InputMethod;
}