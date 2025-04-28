import json
import os
import re
from typing import Any, Generator
from openai import OpenAI, beta
from pydantic import BaseModel

from bpmn_assistant.core.llm_provider import LLMProvider
from bpmn_assistant.core.enums.output_modes import OutputMode
from bpmn_assistant.core.enums.message_roles import MessageRole
from bpmn_assistant.config import logger
from bpmn_assistant.core.enums.models import AliModels

class AliProvider(LLMProvider):
    def __init__(self, api_key: str, output_mode: OutputMode = OutputMode.JSON):
        self.output_mode = output_mode
        os.environ["DASHSCOPE_API_KEY"]=api_key
        self.client = OpenAI(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    def call(
        self,
        model: str,
        prompt: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
        structured_output: BaseModel | None = None,
    ) -> str | dict[str, Any]:
        messages.append({"role": "user", "content": prompt})

        # print("model：\n" + str(model))
        # print("prompt：\n" + str(prompt))

        params: dict[str, Any] = {
            "model": model,                             # 设定模型
            "messages": messages,                       # 传入prompt
        }

        # Google's structured output does not support type unions
        # if structured_output is not None:
        #     params["response_format"] = structured_output
        # elif self.output_mode == OutputMode.JSON:
        #     params["response_format"] = {"type": "json_object"}

        # 通义千问专用路径
        if structured_output:
            # 生成JSON Schema描述
            schema_desc = structured_output.model_json_schema()
            print("schema_desc:" + str(schema_desc))
            messages.append({
                "role": "system",
                "content": f"请严格按以下JSON格式响应：\n```json\n{schema_desc}\n```"
            })


        # params["max_tokens"] = max_tokens
        # params["temperature"] = temperature
        # params["max_tokens"] = max_tokens * 10  # 因其token计算方式不同
        # print("tokens", max_tokens)
        params["max_tokens"] = 8192  # 因其token计算方式不同
        params["top_p"] = 0.8  # 推荐参数
        params["stream"] = False

        try:
            # response = completion(**params)
            # 替换为通义千问的问题逻辑
            response = self.client.chat.completions.create(
                **params
            )
        except Exception as e:
            logger.error(f"API调用失败: {str(e)}")
            raise
        raw_output = response.choices[0].message.content

        # 🗝️ 提取JSON内容
        json_match = re.search(r"```json\n(.*?)\n```", raw_output, re.DOTALL)
        if json_match:
            raw_output = json_match.group(1).strip()
            try:
                return json.loads(raw_output)
            except json.JSONDecodeError:
                logger.warning("通义千问JSON解析失败，尝试原始解析")

        return self._process_response(raw_output)
        #
        # return self._process_response(raw_output)


    def stream(
        self,
        model: str,
        prompt: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> Generator[str, None, None]:
        messages.append({"role": "user", "content": prompt})

        max_tokens = 2048

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )

        for chunk in response:
            yield chunk.choices[0].delta.content or ""

    def get_initial_messages(self) -> list[dict[str, str]]:
        return (
            [
                {
                    "role": "system",
                    "content": "You are a helpful assistant designed to output JSON.",
                }
            ]
            if self.output_mode == OutputMode.JSON
            else []
        )

    def add_message(
        self, messages: list[dict[str, str]], role: MessageRole, content: str
    ) -> None:
        message_role = "assistant" if role == MessageRole.ASSISTANT else "user"
        messages.append({"role": message_role, "content": content})

    def check_model_compatibility(self, model: str) -> bool:
        return model in [m.value for m in AliModels]

    def _process_response(self, raw_output: str) -> str | dict[str, Any]:
        """
        Process the raw output from the model. Returns the appropriate response based on the output mode.
        If the output mode is JSON, the raw output is parsed and returned as a dict.
        If the output mode is text, the raw output is returned as is.
        """
        if self.output_mode == OutputMode.JSON:
            try:
                result = json.loads(raw_output)

                if not isinstance(result, dict):
                    raise ValueError(
                        f"Invalid JSON response from LLM: {result}"
                    )

                return result
            except json.decoder.JSONDecodeError as e:
                logger.error(f"JSONDecodeError: {e}")
                logger.error(f"Raw output: {raw_output}")
                raise Exception("Invalid JSON response from LLM") from e
        elif self.output_mode == OutputMode.TEXT:
            return raw_output
        else:
            raise ValueError(f"Unsupported output mode: {self.output_mode}")
