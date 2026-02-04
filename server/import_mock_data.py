import sqlite3
from datetime import datetime

def import_mock_data():
    conn = sqlite3.connect('aiops.db')
    cursor = conn.cursor()
    
    try:
        # Dashboard Stats
        cursor.execute('''
            INSERT OR REPLACE INTO dashboard_stats 
            (id, active_tasks, success_rate, avg_resolution_time, total_cases, updated_at)
            VALUES (1, 12, 94.2, '18min', 1247, ?)
        ''', (datetime.now(),))
        
        # Agents
        agents_data = [
            ('coordinator', '协调Agent', 'Coordinator', '#3b82f6', '统筹全局任务分发与结果综合', 1),
            ('log', '日志分析Agent', 'Log Analyst', '#f59e0b', '专注ELK日志解析与异常检测', 1),
            ('code', '代码分析Agent', 'Code Analyst', '#10b981', '专注AST解析与调用链追踪', 1),
            ('knowledge', '架构审查Agent', 'Architecture Reviewer', '#8b5cf6', '专注知识图谱与架构模式匹配', 1),
        ]
        for agent_id, name, role, color, description, is_active in agents_data:
            cursor.execute('''
                INSERT OR REPLACE INTO agents 
                (agent_id, name, role, color, description, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (agent_id, name, role, color, description, is_active, datetime.now()))
        
        # System Health
        system_health_data = [
            ('elk', 'ELK Stack', 'healthy', '12ms', 'https://elk.internal:9200'),
            ('git', 'GitLab', 'healthy', '45ms', 'https://gitlab.internal'),
            ('k8s', 'Kubernetes', 'warning', '180ms', 'https://k8s.internal:6443'),
            ('neo4j', 'Neo4j', 'healthy', '28ms', 'bolt://neo4j.internal:7687'),
            ('milvus', 'Milvus', 'healthy', '35ms', None),
        ]
        for tool_id, name, status, latency, url in system_health_data:
            cursor.execute('''
                INSERT OR REPLACE INTO system_health 
                (tool_id, name, status, latency, url, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (tool_id, name, status, latency, url, datetime.now()))
        
        # Recent Cases
        cases_data = [
            ('CASE-2024-001', 'MySQL连接池耗尽导致服务不可用', 'resolved', 'coordinator', 95, '2024-01-05 15:30:00'),
            ('CASE-2024-002', 'Kafka消费者组Rebalance频繁触发', 'investigating', 'log', 72, '2024-01-05 14:22:00'),
            ('CASE-2024-003', 'Redis集群分片数据不一致', 'pending', 'code', 0, '2024-01-05 13:15:00'),
            ('CASE-2024-004', 'gRPC服务间调用超时增加', 'resolved', 'knowledge', 88, '2024-01-05 11:08:00'),
            ('CASE-2024-005', 'K8s Pod OOMKilled重启循环', 'investigating', 'coordinator', 65, '2024-01-05 10:45:00'),
        ]
        for case_id, symptom, status, lead_agent, confidence, created_at in cases_data:
            cursor.execute('''
                INSERT OR REPLACE INTO cases 
                (case_id, symptom, status, lead_agent, confidence, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (case_id, symptom, status, lead_agent, confidence, created_at, datetime.now()))
        
        # Knowledge Graph Nodes
        nodes_data = [
            ('1', '连接池耗尽', 'symptom', 100, 200),
            ('2', '请求超时', 'symptom', 100, 300),
            ('3', '配置不当', 'rootCause', 300, 150),
            ('4', '连接泄漏', 'rootCause', 300, 250),
            ('5', '慢查询', 'rootCause', 300, 350),
            ('6', '增加连接池大小', 'solution', 500, 100),
            ('7', '修复泄漏代码', 'solution', 500, 200),
            ('8', '优化SQL索引', 'solution', 500, 300),
            ('9', 'HikariConfig.java', 'code', 500, 400),
        ]
        for node_id, label, node_type, x, y in nodes_data:
            cursor.execute('''
                INSERT OR REPLACE INTO knowledge_nodes 
                (node_id, label, node_type, x, y, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (node_id, label, node_type, x, y, datetime.now()))
        
        # Knowledge Graph Edges
        edges_data = [
            ('edge-1-3', '1', '3', '可能导致'),
            ('edge-1-4', '1', '4', '可能导致'),
            ('edge-2-5', '2', '5', '可能导致'),
            ('edge-3-6', '3', '6', '解决方案'),
            ('edge-4-7', '4', '7', '解决方案'),
            ('edge-5-8', '5', '8', '解决方案'),
            ('edge-6-9', '6', '9', '涉及代码'),
        ]
        for edge_id, source, target, label in edges_data:
            cursor.execute('''
                INSERT OR REPLACE INTO knowledge_edges 
                (edge_id, source, target, label, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (edge_id, source, target, label, datetime.now()))
        
        # Historical Cases
        historical_data = [
            ('KB-001', 'MySQL连接池耗尽问题', 'Connection pool exhausted, 请求超时', '连接池配置过小', '增加maximum-pool-size到300', 95, 127, '2024-01-05 00:00:00'),
            ('KB-002', 'Kafka消费者Rebalance', 'Consumer group rebalance, 消息堆积', '心跳超时配置不当', '调整session.timeout.ms', 88, 89, '2024-01-04 00:00:00'),
            ('KB-003', 'Redis集群数据不一致', 'Cache miss增加, 数据过期异常', '主从同步延迟', '检查网络延迟并优化', 72, 45, '2024-01-03 00:00:00'),
        ]
        for case_id, title, symptoms, root_cause, solution, confidence, hits, last_used in historical_data:
            cursor.execute('''
                INSERT OR REPLACE INTO historical_cases 
                (case_id, title, symptoms, root_cause, solution, confidence, hits, last_used, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (case_id, title, symptoms, root_cause, solution, confidence, hits, last_used, datetime.now()))
        
        # Settings - Redlines
        redlines_data = [
            ('write-ops', '禁止写入操作', '禁止任何数据库写入、文件修改操作', 1),
            ('auto-exec', '自动执行阈值', '置信度>95%时自动执行修复建议', 0),
            ('prod-access', '生产环境访问', '允许直接访问生产环境数据', 0),
            ('pii-mask', 'PII数据脱敏', '自动脱敏身份证、手机号等敏感信息', 1),
        ]
        for setting_id, name, description, enabled in redlines_data:
            cursor.execute('''
                INSERT OR REPLACE INTO settings 
                (setting_type, setting_id, name, description, enabled, config, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('redline', setting_id, name, description, enabled, None, datetime.now(), datetime.now()))
        
        # Settings - Tools
        tools_data = [
            ('elk', 'ELK Stack', 'ELK Stack日志分析工具', 1, '{"url": "https://elk.internal:9200", "connected": true}'),
            ('gitlab', 'GitLab', 'GitLab代码仓库', 1, '{"url": "https://gitlab.internal", "connected": true}'),
            ('k8s', 'Kubernetes', 'Kubernetes容器编排', 1, '{"url": "https://k8s.internal:6443", "connected": true}'),
            ('neo4j', 'Neo4j', 'Neo4j图数据库', 1, '{"url": "bolt://neo4j.internal:7687", "connected": true}'),
        ]
        for setting_id, name, description, enabled, config in tools_data:
            cursor.execute('''
                INSERT OR REPLACE INTO settings 
                (setting_type, setting_id, name, description, enabled, config, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('tool', setting_id, name, description, enabled, config, datetime.now(), datetime.now()))
        
        # Settings - Masking Rules
        masking_data = [
            ('id-card', '身份证号', '脱敏身份证号', 1, '{"pattern": "\\\\b\\\\d{18}\\\\b", "replacement": "***"}'),
            ('phone', '手机号', '脱敏手机号', 1, '{"pattern": "\\\\b1[3-9]\\\\d{9}\\\\b", "replacement": "***"}'),
            ('email', '邮箱', '脱敏邮箱地址', 1, '{"pattern": "[\\\\w.-]+@[\\\\w.-]+\\\\.\\\\w+", "replacement": "***@***.***"}'),
        ]
        for setting_id, name, description, enabled, config in masking_data:
            cursor.execute('''
                INSERT OR REPLACE INTO settings 
                (setting_type, setting_id, name, description, enabled, config, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('masking', setting_id, name, description, enabled, config, datetime.now(), datetime.now()))
        
        conn.commit()
        print("Mock data imported successfully!")
        
        # Print summary
        cursor.execute("SELECT COUNT(*) FROM agents")
        print(f"Agents: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM cases")
        print(f"Cases: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM system_health")
        print(f"System Health: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM knowledge_nodes")
        print(f"Knowledge Nodes: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM knowledge_edges")
        print(f"Knowledge Edges: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM historical_cases")
        print(f"Historical Cases: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM settings")
        print(f"Settings: {cursor.fetchone()[0]}")
        
    except Exception as e:
        conn.rollback()
        print(f"Error importing data: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    import_mock_data()
