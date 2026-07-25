"""
Multitask Orchestrator Engine for Goby Framework.
Provides concurrent task dispatching, dependency tracking, worker pooling,
retry policies, event callback hooks, and balanced execution.
"""

import concurrent.futures
import enum
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any


class TaskStatus(enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class TaskSpec:
    task_id: str
    name: str
    func: Callable[..., Any]
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    priority: int = 1  # 1 = Highest, 10 = Lowest
    max_retries: int = 0
    retry_delay: float = 0.0
    retries_taken: int = 0
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    duration: float = 0.0


class MultitaskOrchestrator:
    """
    Concurrent Task Orchestrator managing parallel worker pools, dependency trees,
    retries, and execution callbacks.
    """

    def __init__(
        self,
        max_workers: int = 4,
        on_task_start: Optional[Callable[[TaskSpec], None]] = None,
        on_task_success: Optional[Callable[[TaskSpec], None]] = None,
        on_task_failed: Optional[Callable[[TaskSpec], None]] = None,
    ):
        self.max_workers = max_workers
        self.on_task_start = on_task_start
        self.on_task_success = on_task_success
        self.on_task_failed = on_task_failed
        self.tasks: Dict[str, TaskSpec] = {}
        self.completed_tasks: Dict[str, TaskSpec] = {}

    def add_task(
        self,
        task_id: str,
        name: str,
        func: Callable[..., Any],
        args: tuple = (),
        kwargs: Optional[dict] = None,
        depends_on: Optional[List[str]] = None,
        priority: int = 1,
        max_retries: int = 0,
        retry_delay: float = 0.0,
    ) -> TaskSpec:
        """Registers a task in the orchestrator queue."""
        task = TaskSpec(
            task_id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs or {},
            depends_on=depends_on or [],
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
        self.tasks[task_id] = task
        return task

    def _execute_single_task(self, task: TaskSpec) -> TaskSpec:
        """Executes a single task with retries and timing."""
        task.status = TaskStatus.RUNNING
        if self.on_task_start:
            try:
                self.on_task_start(task)
            except Exception:
                pass

        start_time = time.time()
        attempt = 0

        while attempt <= task.max_retries:
            try:
                res = task.func(*task.args, **task.kwargs)
                task.result = res
                task.status = TaskStatus.SUCCESS
                task.error = None
                task.retries_taken = attempt
                if self.on_task_success:
                    try:
                        self.on_task_success(task)
                    except Exception:
                        pass
                break
            except Exception as e:
                task.error = e
                attempt += 1
                if attempt <= task.max_retries:
                    if task.retry_delay > 0:
                        time.sleep(task.retry_delay)
                else:
                    task.retries_taken = attempt - 1
                    task.status = TaskStatus.FAILED
                    if self.on_task_failed:
                        try:
                            self.on_task_failed(task)
                        except Exception:
                            pass

        task.duration = round(time.time() - start_time, 3)
        return task

    def execute_all(self) -> Dict[str, TaskSpec]:
        """
        Executes all queued tasks concurrently while respecting dependencies and priority ordering.
        """
        remaining_tasks = dict(self.tasks)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while remaining_tasks:
                # Find tasks whose dependencies are fully resolved and successful
                ready_tasks: List[TaskSpec] = []
                for tid, task in list(remaining_tasks.items()):
                    deps_satisfied = all(
                        dep_id in self.completed_tasks and self.completed_tasks[dep_id].status == TaskStatus.SUCCESS
                        for dep_id in task.depends_on
                    )

                    # Check if any dependency failed or cancelled
                    dep_failed = any(
                        dep_id in self.completed_tasks and self.completed_tasks[dep_id].status in (TaskStatus.FAILED, TaskStatus.CANCELLED)
                        for dep_id in task.depends_on
                    )

                    if dep_failed:
                        task.status = TaskStatus.CANCELLED
                        task.error = RuntimeError(f"Task cancelled due to failed dependency in {task.depends_on}")
                        self.completed_tasks[tid] = task
                        del remaining_tasks[tid]
                    elif deps_satisfied:
                        ready_tasks.append(task)

                if not ready_tasks and remaining_tasks:
                    # Circular dependency or unresolvable deadlock
                    for tid, task in list(remaining_tasks.items()):
                        task.status = TaskStatus.FAILED
                        task.error = RuntimeError("Deadlock detected: unresolvable circular dependency")
                        self.completed_tasks[tid] = task
                    break

                # Sort ready tasks by priority (1 is highest priority)
                ready_tasks.sort(key=lambda t: t.priority)

                # Dispatch ready tasks to ThreadPoolExecutor
                future_to_task = {
                    executor.submit(self._execute_single_task, task): task
                    for task in ready_tasks
                }

                for future in concurrent.futures.as_completed(future_to_task):
                    completed_task = future.result()
                    self.completed_tasks[completed_task.task_id] = completed_task
                    if completed_task.task_id in remaining_tasks:
                        del remaining_tasks[completed_task.task_id]

        return self.completed_tasks
