from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.core.security import get_password_hash


def init_db():
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成！")
    
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            admin_user = User(
                username="admin",
                email="admin@aiops.com",
                hashed_password=get_password_hash("admin123"),
                display_name="系统管理员",
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            print("创建管理员账号: admin / admin123")
        
        if not db.query(User).filter(User.username == "engineer").first():
            engineer_user = User(
                username="engineer",
                email="engineer@aiops.com",
                hashed_password=get_password_hash("engineer123"),
                display_name="运维工程师",
                role="engineer",
                is_active=True
            )
            db.add(engineer_user)
            print("创建工程师账号: engineer / engineer123")
        
        if not db.query(User).filter(User.username == "viewer").first():
            viewer_user = User(
                username="viewer",
                email="viewer@aiops.com",
                hashed_password=get_password_hash("viewer123"),
                display_name="观察者",
                role="viewer",
                is_active=True
            )
            db.add(viewer_user)
            print("创建观察者账号: viewer / viewer123")
        
        db.commit()
        print("数据库初始化完成！")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
