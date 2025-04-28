import traceback

from pydantic import BaseModel

from bpmn_assistant.config import logger
from bpmn_assistant.core import LLMFacade, MessageItem
from bpmn_assistant.prompts import PromptTemplateProcessor
from bpmn_assistant.utils import message_history_to_string


def _validate_determine_intent(response: dict) -> None:
    """
    Validate the response from the determine_intent function.
    Args:
        response: The response to validate
    Raises:
        ValueError: If the response is invalid
    """
    if "intent" not in response:
        raise ValueError("Invalid response: 'intent' key not found")

    if response["intent"] not in ["modify", "talk"]:
        raise ValueError("Invalid response: 'intent' must be 'modify' or 'talk'")


class DetermineIntentResponse(BaseModel):
    intent: str


def determine_intent(
    llm_facade: LLMFacade,
    message_history: list[MessageItem],
    max_retries: int = 3,
) -> dict:
    """
    Determine the intent of the user based on the message history.
    The possible intents are "modify" and "talk".
    Args:
        llm_facade: The LLM facade
        message_history: The message history
        max_retries: The maximum number of retries in case of failure
    Returns:
        dict: The response containing the intent
    """
    prompt_processor = PromptTemplateProcessor()

    prompt = prompt_processor.render_template(
        "determine_intent.jinja2",
        message_history=message_history_to_string(message_history),
    )

    attempts = 0

    while attempts < max_retries:

        attempts += 1

        try:
            json_object = llm_facade.call(
                prompt,
                max_tokens=500,
                temperature=0.3,
                structured_output=DetermineIntentResponse,
            )
            _validate_determine_intent(json_object)
            logger.info(f"Intent: {json_object}")
            return json_object
        except Exception as e:
            logger.warning(
                f"Validation error (attempt {attempts}): {str(e)}\n"
                f"Traceback: {traceback.format_exc()}"
            )

            prompt = f"Error: {str(e)}. Try again."

    raise Exception("Maximum number of retries reached. Could not determine intent.")
