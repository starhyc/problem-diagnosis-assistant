-- ============================================
-- Mock Data SQL Insert Statements
-- Generated from data.txt
-- ============================================

-- ============================================
-- Dashboard Stats
-- ============================================
INSERT OR REPLACE INTO dashboard_stats (id, active_tasks, success_rate, avg_resolution_time, total_cases, updated_at)
VALUES (1, 12, 94.2, '18min', 1247, datetime('now'));

-- ============================================
-- Agents
-- ============================================
INSERT OR REPLACE INTO agents (agent_id, name, role, color, description, is_active, created_at)
VALUES 
('coordinator', '协调Agent', 'Coordinator', '#3b82f6', '统筹全局任务分发与结果综合', 1, datetime('now')),
('log', '日志分析Agent', 'Log Analyst', '#f59e0b', '专注ELK日志解析与异常检测', 1, datetime('now')),
('code', '代码分析Agent', 'Code Analyst', '#10b981', '专注AST解析与调用链追踪', 1, datetime('now')),
('knowledge', '架构审查Agent', 'Architecture Reviewer', '#8b5cf6', '专注知识图谱与架构模式匹配', 1, datetime('now'));

-- ============================================
-- System Health
-- ============================================
INSERT OR REPLACE INTO system_health (tool_id, name, status, latency, url, updated_at)
VALUES 
('elk', 'ELK Stack', 'healthy', '12ms', 'https://elk.internal:9200', datetime('now')),
('git', 'GitLab', 'healthy', '45ms', 'https://gitlab.internal', datetime('now')),
('k8s', 'Kubernetes', 'warning', '180ms', 'https://k8s.internal:6443', datetime('now')),
('neo4j', 'Neo4j', 'healthy', '28ms', 'bolt://neo4j.internal:7687', datetime('now')),
('milvus', 'Milvus', 'healthy', '35ms', NULL, datetime('now'));

-- ============================================
-- Recent Cases
-- ============================================
INSERT OR REPLACE INTO cases (case_id, symptom, status, lead_agent, confidence, created_at, updated_at)
VALUES 
('CASE-2024-001', 'MySQL连接池耗尽导致服务不可用', 'resolved', 'coordinator', 95, '2024-01-05 15:30:00', '2025-01-05 15:30:00'),
('CASE-2024-002', 'Kafka消费者组Rebalance频繁触发', 'investigating', 'log', 72, '2024-01-05 14:22:00', '2025-01-05 15:30:00'),
('CASE-2024-003', 'Redis集群分片数据不一致', 'pending', 'code', 0, '2024-01-05 13:15:00', '2025-01-05 15:30:00'),
('CASE-2024-004', 'gRPC服务间调用超时增加', 'resolved', 'knowledge', 88, '2024-01-05 11:08:00', '2025-01-05 15:30:00'),
('CASE-2024-005', 'K8s Pod OOMKilled重启循环', 'investigating', 'coordinator', 65, '2024-01-05 10:45:00', '2025-01-05 15:30:00');

-- ============================================
-- Knowledge Graph Nodes
-- ============================================
INSERT OR REPLACE INTO knowledge_nodes (node_id, label, node_type, x, y, created_at)
VALUES 
('1', '连接池耗尽', 'symptom', 100, 200, datetime('now')),
('2', '请求超时', 'symptom', 100, 300, datetime('now')),
('3', '配置不当', 'rootCause', 300, 150, datetime('now')),
('4', '连接泄漏', 'rootCause', 300, 250, datetime('now')),
('5', '慢查询', 'rootCause', 300, 350, datetime('now')),
('6', '增加连接池大小', 'solution', 500, 100, datetime('now')),
('7', '修复泄漏代码', 'solution', 500, 200, datetime('now')),
('8', '优化SQL索引', 'solution', 500, 300, datetime('now')),
('9', 'HikariConfig.java', 'code', 500, 400, datetime('now'));

-- ============================================
-- Knowledge Graph Edges
-- ============================================
INSERT OR REPLACE INTO knowledge_edges (edge_id, source, target, label, created_at)
VALUES 
('edge-1-3', '1', '3', '可能导致', datetime('now')),
('edge-1-4', '1', '4', '可能导致', datetime('now')),
('edge-2-5', '2', '5', '可能导致', datetime('now')),
('edge-3-6', '3', '6', '解决方案', datetime('now')),
('edge-4-7', '4', '7', '解决方案', datetime('now')),
('edge-5-8', '5', '8', '解决方案', datetime('now')),
('edge-6-9', '6', '9', '涉及代码', datetime('now'));

-- ============================================
-- Historical Cases (Knowledge Base)
-- ============================================
INSERT OR REPLACE INTO historical_cases (case_id, title, symptoms, root_cause, solution, confidence, hits, last_used, created_at)
VALUES 
('KB-001', 'MySQL连接池耗尽问题', 'Connection pool exhausted, 请求超时', '连接池配置过小', '增加maximum-pool-size到300', 95, 127, '2024-01-05 00:00:00', datetime('now')),
('KB-002', 'Kafka消费者Rebalance', 'Consumer group rebalance, 消息堆积', '心跳超时配置不当', '调整session.timeout.ms', 88, 89, '2024-01-04 00:00:00', datetime('now')),
('KB-003', 'Redis集群数据不一致', 'Cache miss增加, 数据过期异常', '主从同步延迟', '检查网络延迟并优化', 72, 45, '2024-01-03 00:00:00', datetime('now'));

-- ============================================
-- Settings - Redlines
-- ============================================
INSERT OR REPLACE INTO settings (setting_type, setting_id, name, description, enabled, config, created_at, updated_at)
VALUES 
('redline', 'write-ops', '禁止写入操作', '禁止任何数据库写入、文件修改操作', 1, NULL, datetime('now'), datetime('now')),
('redline', 'auto-exec', '自动执行阈值', '置信度>95%时自动执行修复建议', 0, NULL, datetime('now'), datetime('now')),
('redline', 'prod-access', '生产环境访问', '允许直接访问生产环境数据', 0, NULL, datetime('now'), datetime('now')),
('redline', 'pii-mask', 'PII数据脱敏', '自动脱敏身份证、手机号等敏感信息', 1, NULL, datetime('now'), datetime('now'));

-- ============================================
-- Settings - Tools
-- ============================================
INSERT OR REPLACE INTO settings (setting_type, setting_id, name, description, enabled, config, created_at, updated_at)
VALUES 
('tool', 'elk', 'ELK Stack', 'ELK Stack日志分析工具', 1, '{"url": "https://elk.internal:9200", "connected": true}', datetime('now'), datetime('now')),
('tool', 'gitlab', 'GitLab', 'GitLab代码仓库', 1, '{"url": "https://gitlab.internal", "connected": true}', datetime('now'), datetime('now')),
('tool', 'k8s', 'Kubernetes', 'Kubernetes容器编排', 1, '{"url": "https://k8s.internal:6443", "connected": true}', datetime('now'), datetime('now')),
('tool', 'neo4j', 'Neo4j', 'Neo4j图数据库', 1, '{"url": "bolt://neo4j.internal:7687", "connected": true}', datetime('now'), datetime('now'));

-- ============================================
-- Settings - Masking Rules
-- ============================================
INSERT OR REPLACE INTO settings (setting_type, setting_id, name, description, enabled, config, created_at, updated_at)
VALUES 
('masking', 'id-card', '身份证号', '脱敏身份证号', 1, '{"pattern": "\\b\\d{18}\\b", "replacement": "***"}', datetime('now'), datetime('now')),
('masking', 'phone', '手机号', '脱敏手机号', 1, '{"pattern": "\\b1[3-9]\\d{9}\\b", "replacement": "***"}', datetime('now'), datetime('now')),
('masking', 'email', '邮箱', '脱敏邮箱地址', 1, '{"pattern": "[\\w.-]+@[\\w.-]+\\.\\w+", "replacement": "***@***.***"}', datetime('now'), datetime('now'));
