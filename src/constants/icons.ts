import {
  CheckCircle,
  XCircle,
  Loader2,
  Clock,
  Server,
  GitBranch,
  Cloud,
  Database,
} from 'lucide-react';

export const toolIcons = {
  elk: Server,
  git: GitBranch,
  k8s: Cloud,
  neo4j: Database,
  milvus: Database,
} as const;

export const statusIcons = {
  completed: CheckCircle,
  active: Loader2,
  pending: Clock,
  failed: XCircle,
} as const;
