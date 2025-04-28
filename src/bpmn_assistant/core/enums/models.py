from enum import Enum


class OpenAIModels(Enum):
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1 = "gpt-4.1"
    O4_MINI = "o4-mini"


class AnthropicModels(Enum):
    HAIKU_3_5 = "claude-3-5-haiku-20241022"
    SONNET_3_7 = "claude-3-7-sonnet-20250219"


class GoogleModels(Enum):
    GEMINI_2_5_FLASH = "gemini/gemini-2.5-flash-preview-04-17"
    GEMINI_2_5_PRO = "gemini/gemini-2.5-pro-preview-03-25"


class FireworksAIModels(Enum):
    LLAMA_4_MAVERICK = "fireworks_ai/accounts/fireworks/models/llama4-maverick-instruct-basic"
    QWEN_2_5_72B = "fireworks_ai/accounts/fireworks/models/qwen2p5-72b-instruct"
    DEEPSEEK_V3 = "fireworks_ai/accounts/fireworks/models/deepseek-v3"
    DEEPSEEK_R1 = "fireworks_ai/accounts/fireworks/models/deepseek-r1"

class AliModels(Enum):
    QWEN_PLUS = "qwen-plus"
    QWEN_MAX  = "qwen-max"