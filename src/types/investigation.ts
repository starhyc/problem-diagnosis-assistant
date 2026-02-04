export interface AgentMessage {
  id: string;
  agent: string;
  timestamp: string;
  content: string;
  type: 'info' | 'hypothesis' | 'action' | 'evidence' | 'decision' | 'error';
}

export interface TimelineStep {
  id: number;
  step: string;
  status: 'pending' | 'active' | 'completed' | 'failed';
  duration: string;
  agent: string;
  output: string;
}

export interface DiagnosisCase {
  id: string;
  symptom: string;
  description: string;
  status: 'pending' | 'investigating' | 'resolved' | 'failed';
  leadAgent: string;
  confidence: number;
  messages: AgentMessage[];
  timeline: TimelineStep[];
  createdAt: string;
}

export interface TopologyNode {
  id: string;
  label: string;
  type: string;
  status: string;
}

export interface TopologyEdge {
  source: string;
  target: string;
}

export interface HypothesisNode {
  id: string;
  label: string;
  type: string;
  probability?: number;
  status?: string;
  evidence?: string[];
}

export interface HypothesisTree {
  root: HypothesisNode;
}

export interface InvestigationData {
  agents: Agent[];
  sample_logs: string;
  topology_nodes: TopologyNode[];
  topology_edges: TopologyEdge[];
  hypothesis_tree: HypothesisTree;
}
