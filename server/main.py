import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "AIOps 智能诊断平台 API",
        "version": settings.app_version
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    print("=" * 50)
    print("AIOps 智能诊断平台启动")
    print(f"WebSocket 端点: ws://{settings.ip}:{settings.port}/api/v1/agent/ws")
    print(f"API 文档: http://{settings.ip}:{settings.port}/docs")
    print("=" * 50)


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.ip, port=settings.port, reload=True)
