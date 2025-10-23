import string
from abc import ABC, abstractmethod

from core.models import TaskDefinition


class Dojo(ABC):
    @abstractmethod
    def get_id(self) -> string:
        pass

    @abstractmethod
    def get_tasks_list(self) -> list[TaskDefinition]:
        pass
