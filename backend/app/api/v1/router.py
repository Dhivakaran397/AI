from fastapi import APIRouter
from .endpoints import auth, chat, settings, activities, health, memory, projects, tasks, files, execution, agents, testing, documents

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(chat.router, prefix="", tags=["chat_alias"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(files.router, prefix="/projects", tags=["files"])
api_router.include_router(execution.router, prefix="/projects", tags=["execution"])
api_router.include_router(testing.router, prefix="/projects", tags=["testing"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(memory.router, prefix="/memories", tags=["memories"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])
api_router.include_router(health.router, tags=["health"])
