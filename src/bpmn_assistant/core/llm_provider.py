from abc import ABC, abstractmethod
from typing import Generator, Any
from pydantic import BaseModel

from bpmn_assistant.core.enums import MessageRole

# 这里只是一个抽象接口类
# 具体的实现在provider_impl里面
# 这里只规定参数类型和返回结果，具体实现在impl里面通过继承实现
class LLMProvider(ABC):
    @abstractmethod
    def call(
        self,
        model: str,
        prompt: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
        structured_output: BaseModel | None = None,
    ) -> str | dict[str, Any]:
        pass

    @abstractmethod
    def stream(
        self,
        model: str,
        prompt: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> Generator[str, None, None]:
        pass

    @abstractmethod
    def get_initial_messages(self) -> list[dict[str, str]]:
        pass

    @abstractmethod
    def add_message(
        self, messages: list[dict[str, str]], role: MessageRole, content: str
    ) -> None:
        pass

    @abstractmethod
    def check_model_compatibility(self, model: str) -> bool:
        pass
