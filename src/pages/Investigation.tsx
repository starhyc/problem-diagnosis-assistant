import { useState, useEffect } from 'react';
import { PlayCircle, StopCircle, Bot } from 'lucide-react';
import { useDiagnosisStore } from '../store/diagnosisStore';
import { useAuthStore, hasPermission } from '../store/authStore';
import { AgentType, AGENT_TYPES, ModelType } from '../types/agent';
import {
  AgentTypeSelector,
  FileUploader,
  AgentCollaborationPanel,
  DiagnosisTimeline,
  EvidencePanel,
  HypothesisTree,
  ConfirmationDialog,
  ActionProposalBar,
  TopologyGraph,
} from '../components/investigation';
import { Tabs } from '../components/common';

export default function Investigation() {
  const [problemDescription, setProblemDescription] = useState('MySQL连接池耗尽导致服务不可用');
  const [selectedAgentType, setSelectedAgentType] = useState<AgentType>('diagnosis');
  const [selectedModel, setSelectedModel] = useState<ModelType>('gpt-4');
  const [uploadedFiles, setUploadedFiles] = useState<Record<string, File[]>>({});
  const [activeTab, setActiveTab] = useState<'agents' | 'timeline' | 'evidence'>('agents');
  const [rightTab, setRightTab] = useState<'topology' | 'hypothesis'>('topology');
  const { user } = useAuthStore();
  
  const {
    currentCase,
    isRunning,
    proposedAction,
    wsConnected,
    pendingConfirmation,
    startDiagnosis,
    stopDiagnosis,
    approveAction,
    rejectAction,
    respondToConfirmation,
    initializeWebSocket,
    disconnectWebSocket,
    currentAgentType: storeAgentType,
  } = useDiagnosisStore();

  const currentAgentConfig = AGENT_TYPES.find(t => t.id === selectedAgentType);

  useEffect(() => {
    initializeWebSocket();
    
    return () => {
      disconnectWebSocket();
    };
  }, []);

  const handleStartAnalysis = () => {
    if (!problemDescription.trim()) return;
    startDiagnosis(selectedAgentType, problemDescription, '');
  };

  const handleStopAnalysis = () => {
    stopDiagnosis();
  };

  const canApprove = hasPermission(user, 'engineer');

  const tabs = [
    { id: 'agents', label: 'Agent协同', badge: currentCase?.messages.length },
    { id: 'timeline', label: '诊断时间轴' },
    { id: 'evidence', label: '证据面板' },
  ];

  const rightTabs = [
    { id: 'topology', label: '调用链拓扑' },
    { id: 'hypothesis', label: '假设树' },
  ];

  return (
    <div className="h-full flex flex-col">
      <Header 
        title="诊断工作台"
        subtitle="Multi-Agent协同问题诊断"
        wsConnected={wsConnected}
        currentCase={currentCase}
      />

      <div className="flex-1 flex overflow-hidden">
        <LeftPanel
          selectedAgentType={selectedAgentType}
          onAgentTypeChange={setSelectedAgentType}
          selectedModel={selectedModel}
          onModelChange={setSelectedModel}
          problemDescription={problemDescription}
          onProblemDescriptionChange={setProblemDescription}
          uploadedFiles={uploadedFiles}
          onFilesChange={setUploadedFiles}
          agentConfig={currentAgentConfig}
          isRunning={isRunning}
          onStartAnalysis={handleStartAnalysis}
          onStopAnalysis={handleStopAnalysis}
        />

        <CenterPanel
          activeTab={activeTab}
          onTabChange={setActiveTab}
          tabs={tabs}
          currentCase={currentCase}
          agents={currentAgentConfig ? [currentAgentConfig].map(t => ({
            id: t.id,
            name: t.name,
            role: t.name,
            color: '#3b82f6',
            description: t.description,
          })) : []}
          isRunning={isRunning}
          sampleLogs={currentCase?.messages.find(m => m.type === 'evidence')?.content || ''}
        />

        <RightPanel
          activeTab={rightTab}
          onTabChange={setRightTab}
          tabs={rightTabs}
          topologyNodes={currentCase?.timeline.map((_, i) => ({
            id: `node-${i}`,
            label: `Node ${i}`,
            type: 'service',
            status: i % 3 === 0 ? 'healthy' : 'warning',
          })) || []}
          topologyEdges={currentCase?.timeline.slice(0, -1).map((_, i) => ({
            source: `node-${i}`,
            target: `node-${i + 1}`,
          })) || []}
          hypothesisTree={currentCase?.messages.find(m => m.type === 'hypothesis') ? {
            root: {
              id: 'root',
              label: 'MySQL连接池耗尽',
              type: 'symptom',
              probability: 0.8,
              status: 'investigating',
            },
          } : null}
        />
      </div>

      {pendingConfirmation && (
        <ConfirmationDialog 
          confirmation={pendingConfirmation}
          onConfirm={(response) => respondToConfirmation(pendingConfirmation.id, response)}
          onCancel={() => respondToConfirmation(pendingConfirmation.id, { action: 'cancel' })}
        />
      )}

      {proposedAction && (
        <ActionProposalBar
          title={proposedAction.title}
          confidence={proposedAction.confidence}
          description="基于日志分析和配置审查"
          onApprove={approveAction}
          onReject={rejectAction}
          onEdit={() => {}}
          canApprove={canApprove}
        />
      )}
    </div>
  );
}

function Header({ 
  title, 
  subtitle, 
  wsConnected, 
  currentCase 
}: { 
  title: string;
  subtitle: string;
  wsConnected: boolean;
  currentCase: any;
}) {
  return (
    <div className="p-4 border-b border-border-subtle bg-bg-surface flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-text-main">{title}</h1>
          <p className="text-sm text-text-muted mt-1">{subtitle}</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-bg-elevated/50">
          <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-semantic-success animate-pulse' : 'bg-semantic-danger'}`} />
          <span className="text-xs text-text-muted">
            {wsConnected ? '已连接' : '未连接'}
          </span>
        </div>
      </div>
      {currentCase && (
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-sm text-text-muted">案例编号</div>
            <div className="text-sm font-mono text-text-main">{currentCase.id}</div>
          </div>
          <div className="text-right">
            <div className="text-sm text-text-muted">置信度</div>
            <div className="text-2xl font-bold text-primary">{currentCase.confidence}%</div>
          </div>
        </div>
      )}
    </div>
  );
}

function LeftPanel({
  selectedAgentType,
  onAgentTypeChange,
  selectedModel,
  onModelChange,
  problemDescription,
  onProblemDescriptionChange,
  uploadedFiles,
  onFilesChange,
  agentConfig,
  isRunning,
  onStartAnalysis,
  onStopAnalysis,
}: {
  selectedAgentType: AgentType;
  onAgentTypeChange: (type: AgentType) => void;
  selectedModel: ModelType;
  onModelChange: (model: ModelType) => void;
  problemDescription: string;
  onProblemDescriptionChange: (desc: string) => void;
  uploadedFiles: Record<string, File[]>;
  onFilesChange: (files: Record<string, File[]>) => void;
  agentConfig: any;
  isRunning: boolean;
  onStartAnalysis: () => void;
  onStopAnalysis: () => void;
}) {
  return (
    <div className="w-80 border-r border-border-subtle flex flex-col bg-bg-surface/50">
      <AgentTypeSelector
        types={AGENT_TYPES}
        selectedType={selectedAgentType}
        onTypeChange={onAgentTypeChange}
        selectedModel={selectedModel}
        onModelChange={onModelChange}
        disabled={isRunning}
      />

      <div className="p-4 border-b border-border-subtle">
        <h3 className="text-sm font-semibold text-text-main mb-3">问题描述</h3>
        <textarea
          value={problemDescription}
          onChange={(e) => onProblemDescriptionChange(e.target.value)}
          placeholder="描述您遇到的问题现象..."
          disabled={isRunning}
          className="w-full h-24 bg-bg-input border border-border-subtle rounded-lg p-3 text-sm text-text-main placeholder-text-muted resize-none focus:outline-none focus:border-primary disabled:opacity-50"
        />

        {agentConfig && (
          <FileUploader
            fileInputs={agentConfig.fileInputs}
            disabled={isRunning}
            onFilesChange={onFilesChange}
          />
        )}

        {!isRunning ? (
          <button
            onClick={onStartAnalysis}
            disabled={!problemDescription.trim()}
            className="w-full mt-3 flex items-center justify-center gap-2 px-4 py-2.5 bg-primary hover:bg-primary-hover disabled:opacity-50 text-white rounded-lg transition-colors"
          >
            <PlayCircle className="w-4 h-4" />
            开始{agentConfig?.name}
          </button>
        ) : (
          <button
            onClick={onStopAnalysis}
            className="w-full mt-3 flex items-center justify-center gap-2 px-4 py-2.5 bg-semantic-danger hover:bg-semantic-danger/80 text-white rounded-lg transition-colors"
          >
            <StopCircle className="w-4 h-4" />
            停止{agentConfig?.name}
          </button>
        )}
      </div>

      <div className="flex-1 overflow-auto p-4">
        <h3 className="text-sm font-semibold text-text-main mb-3">相关资源</h3>
        <div className="space-y-2">
          <ResourceItem icon={Bot} name="error.log" type="日志文件" />
          <ResourceItem icon={Bot} name="OrderService.java" type="源代码" />
          <ResourceItem icon={Bot} name="application.yml" type="配置文件" />
        </div>
      </div>
    </div>
  );
}

function ResourceItem({ icon: Icon, name, type }: { icon: React.ComponentType<{ className?: string }>; name: string; type: string }) {
  return (
    <div className="flex items-center gap-3 p-3 bg-bg-elevated/50 rounded-lg hover:bg-bg-elevated transition-colors cursor-pointer">
      <Icon className="w-4 h-4 text-text-muted" />
      <div className="flex-1">
        <div className="text-sm text-text-main">{name}</div>
        <div className="text-xs text-text-muted">{type}</div>
      </div>
    </div>
  );
}

function CenterPanel({
  activeTab,
  onTabChange,
  tabs,
  currentCase,
  agents,
  isRunning,
  sampleLogs,
}: {
  activeTab: string;
  onTabChange: (tab: string) => void;
  tabs: Array<{ id: string; label: string; badge?: number }>;
  currentCase: any;
  agents: any[];
  isRunning: boolean;
  sampleLogs: string;
}) {
  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <Tabs tabs={tabs} activeTab={activeTab} onTabChange={onTabChange} />

      <div className="flex-1 overflow-auto">
        {activeTab === 'agents' && (
          <AgentCollaborationPanel 
            messages={currentCase?.messages || []} 
            agents={agents}
            isRunning={isRunning}
          />
        )}
        {activeTab === 'timeline' && (
          <DiagnosisTimeline 
            timeline={currentCase?.timeline || []} 
            agents={agents} 
          />
        )}
        {activeTab === 'evidence' && (
          <EvidencePanel logs={sampleLogs} />
        )}
      </div>
    </div>
  );
}

function RightPanel({
  activeTab,
  onTabChange,
  tabs,
  topologyNodes,
  topologyEdges,
  hypothesisTree,
}: {
  activeTab: string;
  onTabChange: (tab: string) => void;
  tabs: Array<{ id: string; label: string }>;
  topologyNodes: any[];
  topologyEdges: any[];
  hypothesisTree: any;
}) {
  return (
    <div className="w-96 border-l border-border-subtle flex flex-col">
      <Tabs tabs={tabs} activeTab={activeTab} onTabChange={onTabChange} />

      <div className="flex-1 overflow-hidden">
        {activeTab === 'topology' && (
          <TopologyGraph nodes={topologyNodes} edges={topologyEdges} />
        )}
        {activeTab === 'hypothesis' && (
          <HypothesisTree data={hypothesisTree} />
        )}
      </div>
    </div>
  );
}
