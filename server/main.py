import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging_config import setup_logging, get_logger
from app.api.v1.api import api_router

setup_logging(settings.log_level, settings.log_file)
logger = get_logger(__name__)

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
    logger.info("Root endpoint accessed")
    return {
        "message": "AIOps 智能诊断平台 API",
        "version": settings.app_version
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 50)
    logger.info("AIOps 智能诊断平台启动")
    logger.info(f"WebSocket 端点: ws://{settings.ip}:{settings.port}/api/v1/agent/ws")
    logger.info(f"API 文档: http://{settings.ip}:{settings.port}/docs")
    logger.info(f"日志级别: {settings.log_level}")
    logger.info(f"日志文件: {settings.log_file}")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("AIOps 智能诊断平台关闭")


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.ip, port=settings.port, reload=True)
