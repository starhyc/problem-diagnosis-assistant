export const dashboardStats = {
  activeTasks: 12,
  successRate: 94.2,
  avgResolutionTime: '18min',
  totalCases: 1247,
};

export const recentCases = [
  {
    id: 'CASE-2024-001',
    symptom: 'MySQL连接池耗尽导致服务不可用',
    status: 'resolved',
    leadAgent: 'coordinator',
    timestamp: '2024-01-05 15:30',
    confidence: 95,
  },
  {
    id: 'CASE-2024-002',
    symptom: 'Kafka消费者组Rebalance频繁触发',
    status: 'investigating',
    leadAgent: 'log',
    timestamp: '2024-01-05 14:22',
    confidence: 72,
  },
  {
    id: 'CASE-2024-003',
    symptom: 'Redis集群分片数据不一致',
    status: 'pending',
    leadAgent: 'code',
    timestamp: '2024-01-05 13:15',
    confidence: 0,
  },
  {
    id: 'CASE-2024-004',
    symptom: 'gRPC服务间调用超时增加',
    status: 'resolved',
    leadAgent: 'knowledge',
    timestamp: '2024-01-05 11:08',
    confidence: 88,
  },
  {
    id: 'CASE-2024-005',
    symptom: 'K8s Pod OOMKilled重启循环',
    status: 'investigating',
    leadAgent: 'coordinator',
    timestamp: '2024-01-05 10:45',
    confidence: 65,
  },
];

export const systemHealth = {
  elk: { name: 'ELK Stack', status: 'healthy', latency: '12ms' },
  git: { name: 'GitLab', status: 'healthy', latency: '45ms' },
  k8s: { name: 'Kubernetes', status: 'warning', latency: '180ms' },
  neo4j: { name: 'Neo4j', status: 'healthy', latency: '28ms' },
  milvus: { name: 'Milvus', status: 'healthy', latency: '35ms' },
};

export const agents = [
  {
    id: 'coordinator',
    name: '协调Agent',
    role: 'Coordinator',
    color: '#3b82f6',
    description: '统筹全局任务分发与结果综合',
  },
  {
    id: 'log',
    name: '日志分析Agent',
    role: 'Log Analyst',
    color: '#f59e0b',
    description: '专注ELK日志解析与异常检测',
  },
  {
    id: 'code',
    name: '代码分析Agent',
    role: 'Code Analyst',
    color: '#10b981',
    description: '专注AST解析与调用链追踪',
  },
  {
    id: 'knowledge',
    name: '架构审查Agent',
    role: 'Architecture Reviewer',
    color: '#8b5cf6',
    description: '专注知识图谱与架构模式匹配',
  },
];

export const diagnosisTimeline = [
  {
    id: 1,
    step: '问题接收',
    status: 'completed',
    duration: '0.5s',
    agent: 'coordinator',
    output: '接收用户问题描述，提取关键症状特征',
  },
  {
    id: 2,
    step: '假设生成',
    status: 'completed',
    duration: '2.3s',
    agent: 'coordinator',
    output: '生成3个根因假设：1)连接池配置问题 2)数据库负载过高 3)网络延迟',
  },
  {
    id: 3,
    step: '日志分析',
    status: 'completed',
    duration: '5.8s',
    agent: 'log',
    output: '发现ERROR级别日志：Connection pool exhausted, max_connections=100',
  },
  {
    id: 4,
    step: '代码审查',
    status: 'active',
    duration: '进行中...',
    agent: 'code',
    output: '正在分析数据库连接获取代码路径...',
  },
  {
    id: 5,
    step: '知识匹配',
    status: 'pending',
    duration: '-',
    agent: 'knowledge',
    output: '等待前置步骤完成',
  },
  {
    id: 6,
    step: '结论综合',
    status: 'pending',
    duration: '-',
    agent: 'coordinator',
    output: '等待所有分析完成',
  },
];

export const agentMessages = [
  {
    id: 1,
    agent: 'coordinator',
    timestamp: '15:30:01',
    content: '收到问题报告：MySQL连接池耗尽。开始分析...',
    type: 'info',
  },
  {
    id: 2,
    agent: 'coordinator',
    timestamp: '15:30:03',
    content: '基于症状特征，生成以下假设：\n1. 连接池最大连接数配置过小 (概率: 45%)\n2. 存在连接泄漏未正确释放 (概率: 35%)\n3. 数据库查询阻塞导致连接占用 (概率: 20%)',
    type: 'hypothesis',
  },
  {
    id: 3,
    agent: 'log',
    timestamp: '15:30:05',
    content: '开始扫描ELK日志，时间范围: 最近1小时...',
    type: 'action',
  },
  {
    id: 4,
    agent: 'log',
    timestamp: '15:30:11',
    content: '发现关键日志:\n```\n[ERROR] HikariPool-1 - Connection is not available, request timed out after 30000ms.\nActive: 100, Idle: 0, Waiting: 47\n```',
    type: 'evidence',
  },
  {
    id: 5,
    agent: 'coordinator',
    timestamp: '15:30:12',
    content: '证据支持假设1。请求Code Agent分析连接池配置...',
    type: 'decision',
  },
  {
    id: 6,
    agent: 'code',
    timestamp: '15:30:14',
    content: '正在解析 application.yml 配置文件...',
    type: 'action',
  },
  {
    id: 7,
    agent: 'code',
    timestamp: '15:30:18',
    content: '配置分析完成:\n```yaml\nspring.datasource.hikari:\n  maximum-pool-size: 100\n  connection-timeout: 30000\n  idle-timeout: 600000\n```\n建议: 当前配置在高并发场景下不足',
    type: 'evidence',
  },
];

export const knowledgeGraphNodes = [
  { id: '1', type: 'symptom', label: '连接池耗尽', x: 100, y: 200 },
  { id: '2', type: 'symptom', label: '请求超时', x: 100, y: 300 },
  { id: '3', type: 'rootCause', label: '配置不当', x: 300, y: 150 },
  { id: '4', type: 'rootCause', label: '连接泄漏', x: 300, y: 250 },
  { id: '5', type: 'rootCause', label: '慢查询', x: 300, y: 350 },
  { id: '6', type: 'solution', label: '增加连接池大小', x: 500, y: 100 },
  { id: '7', type: 'solution', label: '修复泄漏代码', x: 500, y: 200 },
  { id: '8', type: 'solution', label: '优化SQL索引', x: 500, y: 300 },
  { id: '9', type: 'code', label: 'HikariConfig.java', x: 500, y: 400 },
];

export const knowledgeGraphEdges = [
  { source: '1', target: '3', label: '可能导致' },
  { source: '1', target: '4', label: '可能导致' },
  { source: '2', target: '5', label: '可能导致' },
  { source: '3', target: '6', label: '解决方案' },
  { source: '4', target: '7', label: '解决方案' },
  { source: '5', target: '8', label: '解决方案' },
  { source: '6', target: '9', label: '涉及代码' },
];

export const topologyNodes = [
  { id: 'gateway', label: 'API Gateway', type: 'service', status: 'healthy' },
  { id: 'user-svc', label: 'User Service', type: 'service', status: 'healthy' },
  { id: 'order-svc', label: 'Order Service', type: 'service', status: 'error' },
  { id: 'payment-svc', label: 'Payment Service', type: 'service', status: 'healthy' },
  { id: 'mysql', label: 'MySQL', type: 'database', status: 'warning' },
  { id: 'redis', label: 'Redis', type: 'cache', status: 'healthy' },
  { id: 'kafka', label: 'Kafka', type: 'queue', status: 'healthy' },
];

export const topologyEdges = [
  { source: 'gateway', target: 'user-svc' },
  { source: 'gateway', target: 'order-svc' },
  { source: 'order-svc', target: 'payment-svc' },
  { source: 'user-svc', target: 'mysql' },
  { source: 'order-svc', target: 'mysql' },
  { source: 'payment-svc', target: 'mysql' },
  { source: 'user-svc', target: 'redis' },
  { source: 'order-svc', target: 'kafka' },
];

export const sampleLogs = `2024-01-05 15:29:45.123 [http-nio-8080-exec-42] ERROR c.e.s.OrderService - Failed to process order
com.zaxxer.hikari.pool.HikariPool$PoolEntryCreator - Connection is not available, request timed out after 30000ms.
    at com.zaxxer.hikari.pool.HikariPool.createTimeoutException(HikariPool.java:696)
    at com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:197)
    at com.example.service.OrderService.createOrder(OrderService.java:89)
    at com.example.controller.OrderController.create(OrderController.java:45)

2024-01-05 15:29:46.234 [http-nio-8080-exec-43] WARN  c.z.h.p.HikariPool - HikariPool-1 - Thread starvation detected
Active connections: 100, Idle: 0, Waiting threads: 47

2024-01-05 15:29:47.456 [http-nio-8080-exec-44] ERROR c.e.s.OrderService - Database connection timeout
java.sql.SQLTransientConnectionException: HikariPool-1 - Connection is not available
    at com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:155)
    at com.example.repository.OrderRepository.save(OrderRepository.java:34)`;

export const settingsConfig = {
  redlines: [
    { id: 'write-ops', name: '禁止写入操作', enabled: true, description: '禁止任何数据库写入、文件修改操作' },
    { id: 'auto-exec', name: '自动执行阈值', enabled: false, description: '置信度>95%时自动执行修复建议' },
    { id: 'prod-access', name: '生产环境访问', enabled: false, description: '允许直接访问生产环境数据' },
    { id: 'pii-mask', name: 'PII数据脱敏', enabled: true, description: '自动脱敏身份证、手机号等敏感信息' },
  ],
  tools: [
    { id: 'elk', name: 'ELK Stack', connected: true, url: 'https://elk.internal:9200' },
    { id: 'gitlab', name: 'GitLab', connected: true, url: 'https://gitlab.internal' },
    { id: 'k8s', name: 'Kubernetes', connected: true, url: 'https://k8s.internal:6443' },
    { id: 'neo4j', name: 'Neo4j', connected: true, url: 'bolt://neo4j.internal:7687' },
  ],
  maskingRules: [
    { pattern: '\\b\\d{18}\\b', name: '身份证号', replacement: '***' },
    { pattern: '\\b1[3-9]\\d{9}\\b', name: '手机号', replacement: '***' },
    { pattern: '[\\w.-]+@[\\w.-]+\\.\\w+', name: '邮箱', replacement: '***@***.***' },
  ],
};

export const hypothesisTree = {
  root: {
    id: 'root',
    label: 'MySQL连接池耗尽',
    type: 'symptom',
    children: [
      {
        id: 'h1',
        label: '连接池配置不足',
        probability: 0.45,
        status: 'validated',
        evidence: ['HikariPool max=100', '并发请求>200'],
        children: [
          { id: 'h1-1', label: '增加pool-size到300', type: 'solution', status: 'recommended' },
        ],
      },
      {
        id: 'h2',
        label: '连接泄漏',
        probability: 0.35,
        status: 'investigating',
        evidence: ['检查中...'],
        children: [],
      },
      {
        id: 'h3',
        label: '慢查询阻塞',
        probability: 0.20,
        status: 'rejected',
        evidence: ['平均查询时间<50ms'],
        children: [],
      },
    ],
  },
};
