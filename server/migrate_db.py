from app.core.database import SessionLocal, engine
from sqlalchemy import text

def migrate_add_agent_type():
    print("正在迁移数据库：添加 agent_type 字段...")
    
    db = SessionLocal()
    try:
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE agents ADD COLUMN agent_type VARCHAR(50) DEFAULT 'diagnosis'"))
                print("✓ 成功添加 agents.agent_type 字段")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("✓ agents.agent_type 字段已存在，跳过")
                else:
                    raise
            
            try:
                conn.execute(text("ALTER TABLE agents ADD COLUMN description TEXT NOT NULL DEFAULT ''"))
                print("✓ 成功添加 agents.description 字段")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("✓ agents.description 字段已存在，跳过")
                else:
                    raise
        
        print("数据库迁移完成！")
    except Exception as e:
        print(f"数据库迁移失败: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_add_agent_type()
