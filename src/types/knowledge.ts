export interface KnowledgeNode {
  id: string;
  type: string;
  label: string;
  x: number;
  y: number;
}

export interface KnowledgeEdge {
  source: string;
  target: string;
  label: string;
}

export interface KnowledgeGraph {
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
}

export interface HistoricalCase {
  id: string;
  title: string;
  symptoms: string[];
  root_cause: string;
  solution: string;
  confidence: number;
  hits: number;
  last_used: string;
}

export interface KnowledgeData {
  graph: KnowledgeGraph;
  historical_cases: HistoricalCase[];
}
