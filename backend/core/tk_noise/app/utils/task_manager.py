#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共享的任务管理器
用于在不同的API端点之间共享任务状态
"""

from datetime import datetime
from typing import Optional, Dict, Any

class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.tasks = {}
    
    def create_task(self, task_id: str, filename: str, strength: int) -> Dict[str, Any]:
        """创建新任务"""
        task = {
            "task_id": task_id,
            "filename": filename,
            "strength": strength,
            "status": "pending",
            "progress": 0,
            "message": "任务已创建，等待处理",
            "created_at": datetime.now().isoformat(),
            "result_url": None,
            "error": None
        }
        self.tasks[task_id] = task
        return task
    
    def update_task(self, task_id: str, **kwargs):
        """更新任务状态"""
        if task_id in self.tasks:
            self.tasks[task_id].update(kwargs)
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        return self.tasks.get(task_id)
    
    def delete_task(self, task_id: str):
        """删除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]

# 全局任务管理器实例
global_task_manager = TaskManager()
