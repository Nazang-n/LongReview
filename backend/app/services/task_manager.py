import uuid
from typing import Dict, Any, Optional

# Global in-memory task registry
# Format: { "task_id": { "id": "...", "name": "...", "status": "processing"|"success"|"error", "result": {...}, "error": "..." } }
active_tasks: Dict[str, Dict[str, Any]] = {}

class TaskManager:
    @staticmethod
    def create_task(name: str) -> str:
        """Create a new task and return its ID"""
        task_id = str(uuid.uuid4())
        active_tasks[task_id] = {
            "id": task_id,
            "name": name,
            "status": "processing",
            "result": None,
            "error": None
        }
        return task_id

    @staticmethod
    def update_task_success(task_id: str, result: Dict[str, Any] = None):
        """Mark a task as completed successfully"""
        if task_id in active_tasks:
            active_tasks[task_id]["status"] = "success"
            active_tasks[task_id]["result"] = result or {}

    @staticmethod
    def update_task_error(task_id: str, error_message: str):
        """Mark a task as failed"""
        if task_id in active_tasks:
            active_tasks[task_id]["status"] = "error"
            active_tasks[task_id]["error"] = error_message

    @staticmethod
    def get_all_tasks() -> list:
        """Return a list of all current tasks"""
        return list(active_tasks.values())
        
    @staticmethod
    def remove_task(task_id: str) -> bool:
        """Remove a task from the registry"""
        if task_id in active_tasks:
            del active_tasks[task_id]
            return True
        return False
