import typing
import uuid
from datetime import datetime, timedelta

import simplejson as json
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils import timezone

from task_processor.exceptions import TaskQueueFullError
from task_processor.managers import RecurringTaskManager, TaskManager
from task_processor.task_registry import get_task, registered_tasks
from task_processor.types import TaskCallable

_django_json_encoder_default = DjangoJSONEncoder().default


class TaskPriority(models.IntegerChoices):
    LOWER = 100
    LOW = 75
    NORMAL = 50
    HIGH = 25
    HIGHEST = 0


class AbstractBaseTask(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    task_identifier = models.CharField(max_length=200)
    serialized_args = models.TextField(blank=True, null=True)
    serialized_kwargs = models.TextField(blank=True, null=True)
    is_locked = models.BooleanField(default=False)
    timeout = models.DurationField(blank=True, null=True)

    class Meta:
        abstract = True

    @property
    def args(self) -> tuple[typing.Any, ...]:
        if self.serialized_args:
            args = self.deserialize_data(self.serialized_args)
            return tuple(args)
        return ()

    @property
    def kwargs(self) -> typing.Dict[str, typing.Any]:
        if self.serialized_kwargs:
            kwargs = self.deserialize_data(self.serialized_kwargs)
            if typing.TYPE_CHECKING:
                assert isinstance(kwargs, dict)
            return kwargs
        return {}

    @staticmethod
    def serialize_data(data: typing.Any) -> str:
        return json.dumps(data, default=_django_json_encoder_default)

    @staticmethod
    def deserialize_data(data: str) -> typing.Any:
        return json.loads(data)

    def mark_failure(self) -> None:
        self.unlock()

    def mark_success(self) -> None:
        self.unlock()

    def unlock(self) -> None:
        self.is_locked = False

    def run(self) -> None:
        return self.callable(*self.args, **self.kwargs)

    @property
    def callable(self) -> TaskCallable[typing.Any]:
        task = get_task(self.task_identifier)
        return task.task_function


class Task(AbstractBaseTask):
    scheduled_for = models.DateTimeField(blank=True, null=True, default=timezone.now)

    timeout = models.DurationField(blank=True, null=True)

    # denormalise failures and completion so that we can use select_for_update
    num_failures = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    objects: TaskManager = TaskManager()
    priority = models.SmallIntegerField(
        default=None, null=True, choices=TaskPriority.choices
    )

    class Meta:
        # We have customised the migration in 0004 to only apply this change to postgres databases
        # TODO: work out how to index the taskprocessor_task table for Oracle and MySQL
        indexes = [
            models.Index(
                name="incomplete_tasks_idx",
                fields=["scheduled_for"],
                condition=models.Q(completed=False, num_failures__lt=3),
            )
        ]

    @classmethod
    def create(
        cls,
        task_identifier: str,
        scheduled_for: datetime,
        priority: TaskPriority = TaskPriority.NORMAL,
        queue_size: int | None = None,
        *,
        args: typing.Tuple[typing.Any, ...] | None = None,
        kwargs: typing.Dict[str, typing.Any] | None = None,
        timeout: timedelta | None = timedelta(seconds=60),
    ) -> "Task":
        if queue_size and cls._is_queue_full(task_identifier, queue_size):
            raise TaskQueueFullError(
                f"Queue for task {task_identifier} is full. "
                f"Max queue size is {queue_size}"
            )
        return Task(
            task_identifier=task_identifier,
            scheduled_for=scheduled_for,
            priority=priority,
            serialized_args=cls.serialize_data(args or tuple()),
            serialized_kwargs=cls.serialize_data(kwargs or dict()),
            timeout=timeout,
        )

    @classmethod
    def _is_queue_full(cls, task_identifier: str, queue_size: int) -> bool:
        return (
            cls.objects.filter(
                task_identifier=task_identifier,
                completed=False,
                num_failures__lt=3,
            ).count()
            > queue_size
        )

    def mark_failure(self) -> None:
        super().mark_failure()
        self.num_failures += 1

    def mark_success(self) -> None:
        super().mark_success()
        self.completed = True


class RecurringTask(AbstractBaseTask):
    run_every = models.DurationField()
    first_run_time = models.TimeField(blank=True, null=True)

    locked_at = models.DateTimeField(blank=True, null=True)
    timeout = models.DurationField(default=timedelta(minutes=30))

    last_picked_at = models.DateTimeField(blank=True, null=True)
    objects: RecurringTaskManager = RecurringTaskManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["task_identifier", "run_every"],
                name="unique_run_every_tasks",
            ),
        ]

    def unlock(self) -> None:
        self.is_locked = False
        self.locked_at = None

    @property
    def should_execute(self) -> bool:
        now = timezone.now()
        last_task_run = (
            self.task_runs.order_by("-started_at").first() if self.pk else None
        )

        if not last_task_run:
            # If we have never run this task, then we should execute it only if
            # the time has passed after which we want to ensure this task runs.
            # This allows us to control when intensive tasks should be run.
            return not (self.first_run_time and self.first_run_time > now.time())

        # if the last run was at t- run_every, then we should execute it
        if (timezone.now() - last_task_run.started_at) >= self.run_every:
            return True

        # if the last run was not a success and we do not have
        # more than 3 failures in t- run_every, then we should execute it
        if (
            last_task_run.result != TaskResult.SUCCESS.name
            and self.task_runs.filter(started_at__gte=(now - self.run_every)).count()
            <= 3
        ):
            return True
        # otherwise, we should not execute it
        return False

    @property
    def is_task_registered(self) -> bool:
        return self.task_identifier in registered_tasks


class TaskResult(models.Choices):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class AbstractTaskRun(models.Model):
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(blank=True, null=True)
    result = models.CharField(
        max_length=50, choices=TaskResult.choices, blank=True, null=True, db_index=True
    )
    error_details = models.TextField(blank=True, null=True)
    task = models.ForeignKey(
        AbstractBaseTask, on_delete=models.CASCADE, related_name="task_runs"
    )

    class Meta:
        abstract = True


class TaskRun(AbstractTaskRun):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="task_runs")


class RecurringTaskRun(AbstractTaskRun):
    task = models.ForeignKey(
        RecurringTask, on_delete=models.CASCADE, related_name="task_runs"
    )


class HealthCheckModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, blank=False, null=False)
