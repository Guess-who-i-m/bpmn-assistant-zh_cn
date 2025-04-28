from typing import Any

from pydantic import BaseModel, model_validator

from bpmn_assistant.core import MessageItem

# 用途：处理 BPMN XML → JSON 的转换请求
# 场景：前端传入原始 BPMN XML，后端返回结构化 JSON
# 请求体示例
# {
#   "bpmn_xml": "<bpmn:definitions>...</bpmn:definitions>"
# }
class BpmnToJsonRequest(BaseModel):
    bpmn_xml: str  # The BPMN XML to be converted to JSON

# 用途：确定用户意图的请求
# 字段解析：
#   message_history：包含对话上下文（用户消息、助手回复等）
#   model：指定使用的 LLM 模型（如 gpt-4）
class DetermineIntentRequest(BaseModel):
    message_history: list[MessageItem]  # The message history
    model: str  # The model to be used

# 用途：创建/修改 BPMN 流程的请求
class ModifyBpmnRequest(BaseModel):
    message_history: list[MessageItem]  # The message history
    process: list[dict[str, Any]] | None  # The process to be updated (if it exists)
    model: str  # The model to be used


class ConversationalRequest(BaseModel):
    message_history: list[MessageItem]  # The message history
    process: list[dict[str, Any]] | None  # The current process (if it exists)
    model: str  # The model to be used
    needs_to_be_final_comment: bool  # Whether the response needs to be a comment after the process is created/edited

    @model_validator(mode="before")
    @classmethod
    def ensure_bpmn_json_presence(cls, data: dict[str, Any]) -> dict[str, Any]:
        if data.get("needs_to_be_final_comment") and not data.get("process"):
            raise ValueError(
                "Process must be present when needs_to_be_final_comment is True"
            )
        return data
