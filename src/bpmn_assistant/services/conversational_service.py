from typing import Any, Generator, Optional

from bpmn_assistant.core import MessageItem
from bpmn_assistant.core.enums import OutputMode
from bpmn_assistant.prompts import PromptTemplateProcessor
from bpmn_assistant.utils import get_llm_facade, message_history_to_string


class ConversationalService:

    def __init__(self, model: str):
        self.llm_facade = get_llm_facade(model, output_mode=OutputMode.TEXT)
        self.prompt_processor = PromptTemplateProcessor()

    def respond_to_query(
        self, message_history: list[MessageItem], process: Optional[list[dict[str, Any]]]
    ) -> Generator:
        """
        Respond to the user query based on the message history and BPMN process.
        Args:
            llm_facade: The LLM facade object (needs to have 'text' output mode)
            message_history: The message history
            process: The BPMN process
        Returns:
            Generator: A generator that yields the response
        """
        template_vars = {"message_history": message_history_to_string(message_history)}

        if process:
            template_vars["process"] = str(process)

        prompt = self.prompt_processor.render_template(
            "respond_to_query.jinja2", **template_vars
        )

        yield from self.llm_facade.stream(prompt, max_tokens=1000, temperature=0.5)

    def make_final_comment(
        self, message_history: list[MessageItem], process: Optional[list[dict[str, Any]]]
    ) -> Generator:
        """
        Make a final comment after the process is created/edited.
        Args:
            message_history: The message history
            process: The BPMN process in JSON format
        Returns:
            Generator: A generator that yields the final comment
        """
        prompt = self.prompt_processor.render_template(
            "make_final_comment.jinja2",
            message_history=message_history_to_string(message_history),
            process=str(process),
        )

        yield from self.llm_facade.stream(prompt, max_tokens=500, temperature=0.5)
