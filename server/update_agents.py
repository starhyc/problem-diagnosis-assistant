from app.core.database import SessionLocal
from app.models.case import Agent

def update_existing_agents():
    print("正在更新现有Agent记录...")
    
    db = SessionLocal()
    try:
        agents = db.query(Agent).all()
        
        for agent in agents:
            if not agent.agent_type or agent.agent_type == "diagnosis":
                if agent.role == "Coordinator":
                    agent.agent_type = "diagnosis"
                elif agent.role == "Log Analyst":
                    agent.agent_type = "diagnosis"
                elif agent.role == "Code Analyst":
                    agent.agent_type = "diagnosis"
                elif agent.role == "Architecture Reviewer":
                    agent.agent_type = "diagnosis"
                else:
                    agent.agent_type = "diagnosis"
                
                print(f"✓ 更新 Agent {agent.name}: agent_type = {agent.agent_type}")
        
        db.commit()
        print(f"成功更新 {len(agents)} 个Agent记录！")
    except Exception as e:
        print(f"更新失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    update_existing_agents()
