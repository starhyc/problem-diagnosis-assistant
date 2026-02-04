import { ReactFlow, Background, Controls, MiniMap } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { KnowledgeGraph as KnowledgeGraphType } from '../../types/knowledge';
import { nodeTypeColors } from '../../constants';

interface KnowledgeGraphProps {
  graph: KnowledgeGraphType;
}

export default function KnowledgeGraph({ graph }: KnowledgeGraphProps) {
  const initialNodes = graph.nodes.map((node) => {
    const nodeStyle = nodeTypeColors[node.type] || nodeTypeColors.evidence;
    return {
      id: node.id,
      position: { x: node.x, y: node.y },
      data: {
        label: node.label,
      },
      style: {
        background: nodeStyle.bg,
        border: `2px solid ${nodeStyle.border}`,
        borderRadius: '8px',
        padding: '4px',
      },
    };
  });

  const initialEdges = graph.edges.map((edge, index) => ({
    id: `e${index}`,
    source: edge.source,
    target: edge.target,
    style: {
      stroke: '#64748b',
      strokeWidth: 2,
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
