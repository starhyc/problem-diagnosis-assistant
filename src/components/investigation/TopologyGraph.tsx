import { ReactFlow, Background, Controls, MiniMap } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { TopologyNode, TopologyEdge } from '../../types/investigation';

interface TopologyGraphProps {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
}

export default function TopologyGraph({ nodes, edges }: TopologyGraphProps) {
  const initialNodes = nodes.map((node, index) => ({
    id: node.id,
    position: { x: (index % 3) * 200 + 50, y: Math.floor(index / 3) * 120 + 50 },
    data: {
      label: (
        <div className="p-2 text-center">
          <div className="text-sm font-medium text-text-main">{node.label}</div>
          <div
            className={`mt-1 w-2 h-2 rounded-full mx-auto ${
              node.status === 'healthy'
                ? 'bg-semantic-success'
                : node.status === 'error'
                ? 'bg-semantic-danger animate-pulse'
                : 'bg-semantic-warning'
            }`}
          />
        </div>
      ),
    },
    style: {
      background: '#1e293b',
      border: node.status === 'error' ? '2px solid #ef4444' : '2px solid rgba(148, 163, 184, 0.2)',
      borderRadius: '8px',
      padding: '4px',
    },
  }));

  const initialEdges = edges.map((edge, index) => ({
    id: `e${index}`,
    source: edge.source,
    target: edge.target,
    animated: edge.source === 'order-svc' || edge.target === 'order-svc',
    style: {
      stroke: edge.source === 'order-svc' ? '#ef4444' : 'rgba(148, 163, 184, 0.3)',
    },
  }));

  return (
    <div className="h-full">
      <ReactFlow
        nodes={initialNodes}
        edges={initialEdges}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#334155" gap={16} />
        <Controls />
        <MiniMap
          nodeColor="#3b82f6"
          maskColor="rgba(11, 17, 32, 0.8)"
          style={{ background: '#1e293b' }}
        />
      </ReactFlow>
    </div>
  );
}
