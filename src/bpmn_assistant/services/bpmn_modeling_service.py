import json
import traceback
import os

from bpmn_assistant.config import logger
from bpmn_assistant.core import LLMFacade, MessageItem
from bpmn_assistant.prompts import PromptTemplateProcessor
from bpmn_assistant.services.process_editing import (
    BpmnEditingService,
    define_change_request,
)
from bpmn_assistant.utils import message_history_to_string

from .validate_bpmn import validate_bpmn

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel


class JudgeRelevanceResponse(BaseModel):
    intent: str


def _validate_judge_relevance(response: dict) -> None:
    """
    Validate the response from the judge_relevance function.
    Args:
        response: The response to validate
    Raises:
        ValueError: If the response is invalid
    """
    if "relevant" not in response:
        raise ValueError("Invalid response: 'relevant' key not found")

    if response["relevant"] not in ["True", "False"]:
        raise ValueError("Invalid response: 'intent' must be 'True' or 'False'")


class BpmnModelingService:
    """
    Service for creating and editing BPMN processes.
    """

    def __init__(self):
        self.prompt_processor = PromptTemplateProcessor()

    def create_bpmn(
        self,
        llm_facade: LLMFacade,
        message_history: list[MessageItem],
        max_retries: int = 3,
    ) -> list:
        """
        Create a BPMN process.
        Args:
            llm_facade: The LLMFacade object.
            message_history: The message history.
            max_retries: The maximum number of retries in case of failure.
        Returns:
            list: The BPMN process.
        """

        if os.path.exists("./vector_dataset") and os.path.exists("./bge-large-zh"):

            # 1. 加载模型
            model_path = "./bge-large-zh"
            embeddings = HuggingFaceEmbeddings(
                model_name=model_path,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )

            # 2. 加载数据库
            vector_db = FAISS.load_local(
                folder_path="./vector_dataset",
                embeddings=embeddings,
                allow_dangerous_deserialization=True
            )

            # 3. 执行检索
            results = vector_db.similarity_search(
                message_history_to_string(message_history),
                k=1,  # 返回前3个最相关场景
                score_threshold=0.5  # BGE相似度阈值建议0.2~0.3
            )

            knowledge = ''

            # 4. 格式化输出（带元数据）
            if not results:
                print("⚠️ 未找到相关场景")
            else:
                print(f"🔍 找到 {len(results)} 个相关场景：")
                for i, doc in enumerate(results, 1):
                    knowledge += "检索场景：" + str(i)
                    knowledge += doc.page_content + "\n"


            relevant_prompt = self.prompt_processor.render_template(
                "judge_relevance.jinja2",
                message_history=message_history_to_string(message_history),
                knowledge=knowledge,
            )

            attempts = 0

            while attempts < max_retries and knowledge != '':

                attempts += 1

                try:
                    json_object = llm_facade.call(
                        relevant_prompt,
                        max_tokens=20,
                        temperature=0.3,
                        structured_output=JudgeRelevanceResponse,
                    )
                    _validate_judge_relevance(json_object)
                    logger.info(f"Relevance: {json_object}")

                except Exception as e:
                    logger.warning(
                        f"Validation error (attempt {attempts}): {str(e)}\n"
                        f"Traceback: {traceback.format_exc()}"
                    )

                    relevant_prompt = f"Error: {str(e)}. Try again."

            if knowledge != '':
                if json_object['relevant'] == "False":
                    knowledge = ''
        else:
            knowledge = ''

        prompt = self.prompt_processor.render_template(
            "create_bpmn.jinja2",
            message_history=message_history_to_string(message_history),
            knowledge=knowledge,
        )

        attempts = 0

        while attempts < max_retries:
            attempts += 1
            try:
                response = llm_facade.call(prompt)
                process = response["process"]
                validate_bpmn(process)
                logger.debug(
                    f"Generated BPMN process:\n{json.dumps(process, indent=2)}"
                )
                return process  # Return the process if it's valid
            except (ValueError, Exception) as e:
                logger.warning(
                    f"Error (attempt {attempts}): {str(e)}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                prompt = f"Error: {str(e)}. Try again."

        raise Exception(
            "Max number of retries reached. Could not create the BPMN process."
        )

    def edit_bpmn(
        self,
        llm_facade: LLMFacade,
        text_llm_facade: LLMFacade,
        process: list[dict],
        message_history: list[MessageItem],
    ) -> list:
        change_request = define_change_request(
            text_llm_facade, process, message_history
        )

        bpmn_editor_service = BpmnEditingService(llm_facade, process, change_request)

        return bpmn_editor_service.edit_bpmn()
