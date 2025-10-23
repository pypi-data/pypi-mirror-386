"""
Data models for the Paylm SDK.
"""

from dataclasses import dataclass
from typing import Dict

# Import constants
from .constants import (
    OpenAIModels,
    AnthropicModels,
    GoogleDeepMindModels,
    MetaModels,
    AWSModels,
    MistralAIModels,
    CohereModels,
    DeepSeekModels,
)


@dataclass
class UsageData:
    """Represents the usage data structure."""
    service_provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class UsageDataWithStrings:
    """Represents the usage data structure with prompt and output strings."""
    service_provider: str
    model: str
    prompt_string: str
    output_string: str


@dataclass
class APIRequest:
    """Represents the request body for the API call."""
    agent_id: str
    customer_id: str
    indicator: str
    amount: float


@dataclass
class ModelPricing:
    """Represents pricing information for different models."""
    prompt_tokens_cost: float
    completion_tokens_cost: float


# Default model pricing (cost per 1000 tokens in USD)
MODEL_PRICING: Dict[str, ModelPricing] = {
    # OpenAI Models (pricing per 1000 tokens)
    OpenAIModels.GPT_5: ModelPricing(
        prompt_tokens_cost=0.00125,  # $0.00125 per 1000 tokens
        completion_tokens_cost=0.01  # $0.01 per 1000 tokens
    ),
    OpenAIModels.GPT_5_MINI: ModelPricing(
        prompt_tokens_cost=0.00025,  # $0.00025 per 1000 tokens
        completion_tokens_cost=0.002  # $0.002 per 1000 tokens
    ),
    OpenAIModels.GPT_5_NANO: ModelPricing(
        prompt_tokens_cost=0.00005,  # $0.00005 per 1000 tokens
        completion_tokens_cost=0.0004  # $0.0004 per 1000 tokens
    ),
    OpenAIModels.GPT_5_CHAT_LATEST: ModelPricing(
        prompt_tokens_cost=0.00125,  # $0.00125 per 1000 tokens
        completion_tokens_cost=0.01  # $0.01 per 1000 tokens
    ),
    OpenAIModels.GPT_5_CODEX: ModelPricing(
        prompt_tokens_cost=0.00125,  # $0.00125 per 1000 tokens
        completion_tokens_cost=0.01  # $0.01 per 1000 tokens
    ),
    OpenAIModels.GPT_5_PRO: ModelPricing(
        prompt_tokens_cost=0.015,  # $0.015 per 1000 tokens
        completion_tokens_cost=0.12  # $0.12 per 1000 tokens
    ),
    OpenAIModels.GPT_5_SEARCH_API: ModelPricing(
        prompt_tokens_cost=0.00125,  # $0.00125 per 1000 tokens
        completion_tokens_cost=0.01  # $0.01 per 1000 tokens
    ),
    OpenAIModels.GPT_4_1: ModelPricing(
        prompt_tokens_cost=0.002,  # $0.002 per 1000 tokens
        completion_tokens_cost=0.008  # $0.008 per 1000 tokens
    ),
    OpenAIModels.GPT_4_1_MINI: ModelPricing(
        prompt_tokens_cost=0.0004,  # $0.0004 per 1000 tokens
        completion_tokens_cost=0.0016  # $0.0016 per 1000 tokens
    ),
    OpenAIModels.GPT_4_1_NANO: ModelPricing(
        prompt_tokens_cost=0.0001,  # $0.0001 per 1000 tokens
        completion_tokens_cost=0.0004  # $0.0004 per 1000 tokens
    ),
    OpenAIModels.GPT_4O: ModelPricing(
        prompt_tokens_cost=0.0025,  # $0.0025 per 1000 tokens
        completion_tokens_cost=0.01  # $0.01 per 1000 tokens
    ),
    OpenAIModels.GPT_4O_2024_05_13: ModelPricing(
        prompt_tokens_cost=0.005,  # $0.005 per 1000 tokens
        completion_tokens_cost=0.015  # $0.015 per 1000 tokens
    ),
    OpenAIModels.GPT_4O_MINI: ModelPricing(
        prompt_tokens_cost=0.00015,  # $0.00015 per 1000 tokens
        completion_tokens_cost=0.0006  # $0.0006 per 1000 tokens
    ),
    OpenAIModels.GPT_REALTIME: ModelPricing(
        prompt_tokens_cost=0.004,  # $0.004 per 1000 tokens
        completion_tokens_cost=0.016  # $0.016 per 1000 tokens
    ),
    OpenAIModels.GPT_REALTIME_MINI: ModelPricing(
        prompt_tokens_cost=0.0006,  # $0.0006 per 1000 tokens
        completion_tokens_cost=0.0024  # $0.0024 per 1000 tokens
    ),
    OpenAIModels.GPT_4O_REALTIME_PREVIEW: ModelPricing(
        prompt_tokens_cost=0.005,  # $0.005 per 1000 tokens
        completion_tokens_cost=0.02  # $0.02 per 1000 tokens
    ),
    OpenAIModels.GPT_4O_MINI_REALTIME_PREVIEW: ModelPricing(
        prompt_tokens_cost=0.0006,  # $0.0006 per 1000 tokens
        completion_tokens_cost=0.0024  # $0.0024 per 1000 tokens
    ),
    OpenAIModels.GPT_AUDIO: ModelPricing(
        prompt_tokens_cost=0.0025,  # $0.0025 per 1000 tokens
        completion_tokens_cost=0.01  # $0.01 per 1000 tokens
    ),
    OpenAIModels.GPT_AUDIO_MINI: ModelPricing(
        prompt_tokens_cost=0.0006,  # $0.0006 per 1000 tokens
        completion_tokens_cost=0.0024  # $0.0024 per 1000 tokens
    ),
    OpenAIModels.GPT_4O_AUDIO_PREVIEW: ModelPricing(
        prompt_tokens_cost=0.0025,  # $0.0025 per 1000 tokens
        completion_tokens_cost=0.01  # $0.01 per 1000 tokens
    ),
    OpenAIModels.GPT_4O_MINI_AUDIO_PREVIEW: ModelPricing(
        prompt_tokens_cost=0.00015,  # $0.00015 per 1000 tokens
        completion_tokens_cost=0.0006  # $0.0006 per 1000 tokens
    ),
    OpenAIModels.O1: ModelPricing(
        prompt_tokens_cost=0.015,  # $0.015 per 1000 tokens
        completion_tokens_cost=0.06  # $0.06 per 1000 tokens
    ),
    OpenAIModels.O1_PRO: ModelPricing(
        prompt_tokens_cost=0.15,  # $0.15 per 1000 tokens
        completion_tokens_cost=0.6  # $0.6 per 1000 tokens
    ),
    OpenAIModels.O3_PRO: ModelPricing(
        prompt_tokens_cost=0.02,  # $0.02 per 1000 tokens
        completion_tokens_cost=0.08  # $0.08 per 1000 tokens
    ),
    OpenAIModels.O3: ModelPricing(
        prompt_tokens_cost=0.002,  # $0.002 per 1000 tokens
        completion_tokens_cost=0.008  # $0.008 per 1000 tokens
    ),
    OpenAIModels.O3_DEEP_RESEARCH: ModelPricing(
        prompt_tokens_cost=0.01,  # $0.01 per 1000 tokens
        completion_tokens_cost=0.04  # $0.04 per 1000 tokens
    ),
    OpenAIModels.O4_MINI: ModelPricing(
        prompt_tokens_cost=0.0011,  # $0.0011 per 1000 tokens
        completion_tokens_cost=0.0044  # $0.0044 per 1000 tokens
    ),
    OpenAIModels.O4_MINI_DEEP_RESEARCH: ModelPricing(
        prompt_tokens_cost=0.002,  # $0.002 per 1000 tokens
        completion_tokens_cost=0.008  # $0.008 per 1000 tokens
    ),
    OpenAIModels.O3_MINI: ModelPricing(
        prompt_tokens_cost=0.0011,  # $0.0011 per 1000 tokens
        completion_tokens_cost=0.0044  # $0.0044 per 1000 tokens
    ),
    OpenAIModels.O1_MINI: ModelPricing(
        prompt_tokens_cost=0.0011,  # $0.0011 per 1000 tokens
        completion_tokens_cost=0.0044  # $0.0044 per 1000 tokens
    ),
    OpenAIModels.CODEX_MINI_LATEST: ModelPricing(
        prompt_tokens_cost=0.0015,  # $0.0015 per 1000 tokens
        completion_tokens_cost=0.006  # $0.006 per 1000 tokens
    ),
    OpenAIModels.GPT_4O_MINI_SEARCH_PREVIEW: ModelPricing(
        prompt_tokens_cost=0.00015,  # $0.00015 per 1000 tokens
        completion_tokens_cost=0.0006  # $0.0006 per 1000 tokens
    ),
    OpenAIModels.GPT_4O_SEARCH_PREVIEW: ModelPricing(
        prompt_tokens_cost=0.0025,  # $0.0025 per 1000 tokens
        completion_tokens_cost=0.01  # $0.01 per 1000 tokens
    ),
    OpenAIModels.COMPUTER_USE_PREVIEW: ModelPricing(
        prompt_tokens_cost=0.003,  # $0.003 per 1000 tokens
        completion_tokens_cost=0.012  # $0.012 per 1000 tokens
    ),
    OpenAIModels.CHATGPT_4O_LATEST: ModelPricing(
        prompt_tokens_cost=0.005,  # $0.005 per 1000 tokens
        completion_tokens_cost=0.015  # $0.015 per 1000 tokens
    ),
    OpenAIModels.GPT_4_TURBO_2024_04_09: ModelPricing(
        prompt_tokens_cost=0.01,  # $0.01 per 1000 tokens
        completion_tokens_cost=0.03  # $0.03 per 1000 tokens
    ),
    OpenAIModels.GPT_4_0125_PREVIEW: ModelPricing(
        prompt_tokens_cost=0.01,  # $0.01 per 1000 tokens
        completion_tokens_cost=0.03  # $0.03 per 1000 tokens
    ),
    OpenAIModels.GPT_4_1106_PREVIEW: ModelPricing(
        prompt_tokens_cost=0.01,  # $0.01 per 1000 tokens
        completion_tokens_cost=0.03  # $0.03 per 1000 tokens
    ),
    OpenAIModels.GPT_4_1106_VISION_PREVIEW: ModelPricing(
        prompt_tokens_cost=0.01,  # $0.01 per 1000 tokens
        completion_tokens_cost=0.03  # $0.03 per 1000 tokens
    ),
    OpenAIModels.GPT_4_0613: ModelPricing(
        prompt_tokens_cost=0.03,  # $0.03 per 1000 tokens
        completion_tokens_cost=0.06  # $0.06 per 1000 tokens
    ),
    OpenAIModels.GPT_4_0314: ModelPricing(
        prompt_tokens_cost=0.03,  # $0.03 per 1000 tokens
        completion_tokens_cost=0.06  # $0.06 per 1000 tokens
    ),
    OpenAIModels.GPT_4_32K: ModelPricing(
        prompt_tokens_cost=0.06,  # $0.06 per 1000 tokens
        completion_tokens_cost=0.12  # $0.12 per 1000 tokens
    ),
    OpenAIModels.GPT_3_5_TURBO: ModelPricing(
        prompt_tokens_cost=0.0005,  # $0.0005 per 1000 tokens
        completion_tokens_cost=0.0015  # $0.0015 per 1000 tokens
    ),
    OpenAIModels.GPT_3_5_TURBO_0125: ModelPricing(
        prompt_tokens_cost=0.0005,  # $0.0005 per 1000 tokens
        completion_tokens_cost=0.0015  # $0.0015 per 1000 tokens
    ),
    OpenAIModels.GPT_3_5_TURBO_1106: ModelPricing(
        prompt_tokens_cost=0.001,  # $0.001 per 1000 tokens
        completion_tokens_cost=0.002  # $0.002 per 1000 tokens
    ),
    OpenAIModels.GPT_3_5_TURBO_0613: ModelPricing(
        prompt_tokens_cost=0.0015,  # $0.0015 per 1000 tokens
        completion_tokens_cost=0.002  # $0.002 per 1000 tokens
    ),
    OpenAIModels.GPT_3_5_0301: ModelPricing(
        prompt_tokens_cost=0.0015,  # $0.0015 per 1000 tokens
        completion_tokens_cost=0.002  # $0.002 per 1000 tokens
    ),
    OpenAIModels.GPT_3_5_TURBO_INSTRUCT: ModelPricing(
        prompt_tokens_cost=0.0015,  # $0.0015 per 1000 tokens
        completion_tokens_cost=0.002  # $0.002 per 1000 tokens
    ),
    OpenAIModels.GPT_3_5_TURBO_16K_0613: ModelPricing(
        prompt_tokens_cost=0.003,  # $0.003 per 1000 tokens
        completion_tokens_cost=0.004  # $0.004 per 1000 tokens
    ),
    OpenAIModels.DAVINCI_002: ModelPricing(
        prompt_tokens_cost=0.002,  # $0.002 per 1000 tokens
        completion_tokens_cost=0.002  # $0.002 per 1000 tokens
    ),
    OpenAIModels.BABBAGE_002: ModelPricing(
        prompt_tokens_cost=0.0004,  # $0.0004 per 1000 tokens
        completion_tokens_cost=0.0004  # $0.0004 per 1000 tokens
    ),

    # Anthropic Models (pricing per 1000 tokens)
    AnthropicModels.SONNET_4_5: ModelPricing(
        prompt_tokens_cost=0.003,  # $0.003 per 1000 tokens
        completion_tokens_cost=0.015  # $0.015 per 1000 tokens
    ),
    AnthropicModels.HAIKU_4_5: ModelPricing(
        prompt_tokens_cost=0.001,  # $0.001 per 1000 tokens
        completion_tokens_cost=0.005  # $0.005 per 1000 tokens
    ),
    AnthropicModels.OPUS_4_1: ModelPricing(
        prompt_tokens_cost=0.015,  # $0.015 per 1000 tokens
        completion_tokens_cost=0.075  # $0.075 per 1000 tokens
    ),
    AnthropicModels.SONNET_4: ModelPricing(
        prompt_tokens_cost=0.003,  # $0.003 per 1000 tokens
        completion_tokens_cost=0.015  # $0.015 per 1000 tokens
    ),
    AnthropicModels.OPUS_4: ModelPricing(
        prompt_tokens_cost=0.015,  # $0.015 per 1000 tokens
        completion_tokens_cost=0.075  # $0.075 per 1000 tokens
    ),
    AnthropicModels.SONNET_3_7: ModelPricing(
        prompt_tokens_cost=0.003,  # $0.003 per 1000 tokens
        completion_tokens_cost=0.015  # $0.015 per 1000 tokens
    ),
    AnthropicModels.HAIKU_3_5: ModelPricing(
        prompt_tokens_cost=0.0008,  # $0.0008 per 1000 tokens
        completion_tokens_cost=0.004  # $0.004 per 1000 tokens
    ),
    AnthropicModels.OPUS_3: ModelPricing(
        prompt_tokens_cost=0.015,  # $0.015 per 1000 tokens
        completion_tokens_cost=0.075  # $0.075 per 1000 tokens
    ),
    AnthropicModels.HAIKU_3: ModelPricing(
        prompt_tokens_cost=0.00025,  # $0.00025 per 1000 tokens
        completion_tokens_cost=0.00125  # $0.00125 per 1000 tokens
    ),

    # Google DeepMind Models (pricing per 1000 tokens)
    GoogleDeepMindModels.GEMINI_2_5_PRO: ModelPricing(
        prompt_tokens_cost=0.00125,  # $0.00125 per 1000 tokens
        completion_tokens_cost=0.01  # $0.01 per 1000 tokens
    ),
    GoogleDeepMindModels.GEMINI_2_5_FLASH: ModelPricing(
        prompt_tokens_cost=0.00015,  # $0.00015 per 1000 tokens
        completion_tokens_cost=0.0006  # $0.0006 per 1000 tokens
    ),
    GoogleDeepMindModels.GEMINI_2_5_FLASH_PREVIEW: ModelPricing(
        prompt_tokens_cost=0.3,  # $0.30 per 1000 tokens
        completion_tokens_cost=2.5  # $2.50 per 1000 tokens
    ),
    GoogleDeepMindModels.GEMINI_2_5_FLASH_LITE: ModelPricing(
        prompt_tokens_cost=0.0001,  # $0.0001 per 1000 tokens
        completion_tokens_cost=0.0004  # $0.0004 per 1000 tokens
    ),
    GoogleDeepMindModels.GEMINI_2_5_FLASH_LITE_PREVIEW: ModelPricing(
        prompt_tokens_cost=0.0001,  # $0.0001 per 1000 tokens
        completion_tokens_cost=0.0004  # $0.0004 per 1000 tokens
    ),
    GoogleDeepMindModels.GEMINI_2_5_FLASH_NATIVE_AUDIO: ModelPricing(
        prompt_tokens_cost=0.0005,  # $0.0005 per 1000 tokens
        completion_tokens_cost=0.002  # $0.002 per 1000 tokens
    ),
    GoogleDeepMindModels.GEMINI_2_5_FLASH_IMAGE: ModelPricing(
        prompt_tokens_cost=0.0003,  # $0.0003 per 1000 tokens
        completion_tokens_cost=0.03  # $0.03 per 1000 tokens
    ),
    GoogleDeepMindModels.GEMINI_2_5_FLASH_PREVIEW_TTS: ModelPricing(
        prompt_tokens_cost=0.0005,  # $0.0005 per 1000 tokens
        completion_tokens_cost=0.01  # $0.01 per 1000 tokens
    ),
    GoogleDeepMindModels.GEMINI_2_5_PRO_PREVIEW_TTS: ModelPricing(
        prompt_tokens_cost=0.001,  # $0.001 per 1000 tokens
        completion_tokens_cost=0.02  # $0.02 per 1000 tokens
    ),
    GoogleDeepMindModels.GEMINI_2_5_COMPUTER_USE_PREVIEW: ModelPricing(
        prompt_tokens_cost=0.00125,  # $0.00125 per 1000 tokens
        completion_tokens_cost=0.01  # $0.01 per 1000 tokens
    ),

    # Meta Models (pricing per 1000 tokens)
    MetaModels.LLAMA_4_MAVERICK: ModelPricing(
        prompt_tokens_cost=0.00027,  # $0.00027 per 1000 tokens
        completion_tokens_cost=0.00085  # $0.00085 per 1000 tokens
    ),
    MetaModels.LLAMA_4_SCOUT: ModelPricing(
        prompt_tokens_cost=0.00018,  # $0.00018 per 1000 tokens
        completion_tokens_cost=0.00059  # $0.00059 per 1000 tokens
    ),
    MetaModels.LLAMA_3_3_70B_INSTRUCT_TURBO: ModelPricing(
        prompt_tokens_cost=0.00088,  # $0.00088 per 1000 tokens
        completion_tokens_cost=0.00088  # $0.00088 per 1000 tokens
    ),
    MetaModels.LLAMA_3_2_3B_INSTRUCT_TURBO: ModelPricing(
        prompt_tokens_cost=0.00006,  # $0.00006 per 1000 tokens
        completion_tokens_cost=0.00006  # $0.00006 per 1000 tokens
    ),
    MetaModels.LLAMA_3_1_405B_INSTRUCT_TURBO: ModelPricing(
        prompt_tokens_cost=0.0035,  # $0.0035 per 1000 tokens
        completion_tokens_cost=0.0035  # $0.0035 per 1000 tokens
    ),
    MetaModels.LLAMA_3_1_70B_INSTRUCT_TURBO: ModelPricing(
        prompt_tokens_cost=0.00088,  # $0.00088 per 1000 tokens
        completion_tokens_cost=0.00088  # $0.00088 per 1000 tokens
    ),
    MetaModels.LLAMA_3_1_8B_INSTRUCT_TURBO: ModelPricing(
        prompt_tokens_cost=0.00018,  # $0.00018 per 1000 tokens
        completion_tokens_cost=0.00018  # $0.00018 per 1000 tokens
    ),
    MetaModels.LLAMA_3_70B_INSTRUCT_TURBO: ModelPricing(
        prompt_tokens_cost=0.00088,  # $0.00088 per 1000 tokens
        completion_tokens_cost=0.00088  # $0.00088 per 1000 tokens
    ),
    MetaModels.LLAMA_3_70B_INSTRUCT_REFERENCE: ModelPricing(
        prompt_tokens_cost=0.00088,  # $0.00088 per 1000 tokens
        completion_tokens_cost=0.00088  # $0.00088 per 1000 tokens
    ),
    MetaModels.LLAMA_3_8B_INSTRUCT_LITE: ModelPricing(
        prompt_tokens_cost=0.0001,  # $0.0001 per 1000 tokens
        completion_tokens_cost=0.0001  # $0.0001 per 1000 tokens
    ),
    MetaModels.LLAMA_2: ModelPricing(
        prompt_tokens_cost=0.0009,  # $0.0009 per 1000 tokens
        completion_tokens_cost=0.0009  # $0.0009 per 1000 tokens
    ),
    MetaModels.LLAMA_GUARD_4_12B: ModelPricing(
        prompt_tokens_cost=0.0002,  # $0.0002 per 1000 tokens
        completion_tokens_cost=0.0002  # $0.0002 per 1000 tokens
    ),
    MetaModels.LLAMA_GUARD_3_11B_VISION_TURBO: ModelPricing(
        prompt_tokens_cost=0.00018,  # $0.00018 per 1000 tokens
        completion_tokens_cost=0.00018  # $0.00018 per 1000 tokens
    ),
    MetaModels.LLAMA_GUARD_3_8B: ModelPricing(
        prompt_tokens_cost=0.0002,  # $0.0002 per 1000 tokens
        completion_tokens_cost=0.0002  # $0.0002 per 1000 tokens
    ),
    MetaModels.LLAMA_GUARD_2_8B: ModelPricing(
        prompt_tokens_cost=0.0002,  # $0.0002 per 1000 tokens
        completion_tokens_cost=0.0002  # $0.0002 per 1000 tokens
    ),
    MetaModels.SALESFORCE_LLAMA_RANK_V1_8B: ModelPricing(
        prompt_tokens_cost=0.0001,  # $0.0001 per 1000 tokens
        completion_tokens_cost=0.0001  # $0.0001 per 1000 tokens
    ),

    # AWS Models (pricing per 1000 tokens)
    AWSModels.AMAZON_NOVA_MICRO: ModelPricing(
        prompt_tokens_cost=0.035,  # $0.035 per 1000 tokens
        completion_tokens_cost=0.14  # $0.14 per 1000 tokens
    ),
    AWSModels.AMAZON_NOVA_LITE: ModelPricing(
        prompt_tokens_cost=0.06,  # $0.06 per 1000 tokens
        completion_tokens_cost=0.24  # $0.24 per 1000 tokens
    ),
    AWSModels.AMAZON_NOVA_PRO: ModelPricing(
        prompt_tokens_cost=0.8,  # $0.8 per 1000 tokens
        completion_tokens_cost=3.2  # $3.2 per 1000 tokens
    ),

    # Mistral AI Models (pricing per 1000 tokens)
    MistralAIModels.MISTRAL_7B_INSTRUCT: ModelPricing(
        prompt_tokens_cost=0.028,  # $0.028 per 1000 tokens
        completion_tokens_cost=0.054  # $0.054 per 1000 tokens
    ),
    MistralAIModels.MISTRAL_LARGE: ModelPricing(
        prompt_tokens_cost=2.0,  # $2.00 per 1000 tokens
        completion_tokens_cost=6.0  # $6.00 per 1000 tokens
    ),
    MistralAIModels.MISTRAL_SMALL: ModelPricing(
        prompt_tokens_cost=0.2,  # $0.20 per 1000 tokens
        completion_tokens_cost=0.6  # $0.60 per 1000 tokens
    ),
    MistralAIModels.MISTRAL_MEDIUM: ModelPricing(
        prompt_tokens_cost=0.4,  # $0.40 per 1000 tokens
        completion_tokens_cost=2.0  # $2.00 per 1000 tokens
    ),

    # Cohere Models (pricing per 1000 tokens)
    CohereModels.COMMAND_R7B: ModelPricing(
        prompt_tokens_cost=0.0000375,  # $0.0000375 per 1000 tokens
        completion_tokens_cost=0.00015  # $0.00015 per 1000 tokens
    ),
    CohereModels.COMMAND_R: ModelPricing(
        prompt_tokens_cost=0.00015,  # $0.00015 per 1000 tokens
        completion_tokens_cost=0.0006  # $0.0006 per 1000 tokens
    ),
    CohereModels.COMMAND_R_PLUS: ModelPricing(
        prompt_tokens_cost=0.00250,  # $0.00250 per 1000 tokens
        completion_tokens_cost=0.01  # $0.01 per 1000 tokens
    ),
    CohereModels.COMMAND_A: ModelPricing(
        prompt_tokens_cost=0.001,  # $0.001 per 1000 tokens
        completion_tokens_cost=0.002  # $0.002 per 1000 tokens
    ),
    CohereModels.AYA_EXPANSE_8B_32B: ModelPricing(
        prompt_tokens_cost=0.00050,  # $0.00050 per 1000 tokens
        completion_tokens_cost=0.00150  # $0.00150 per 1000 tokens
    ),

    # DeepSeek Models (pricing per 1000 tokens)
    DeepSeekModels.DEEPSEEK_CHAT: ModelPricing(
        prompt_tokens_cost=0.00007,  # $0.00007 per 1000 tokens
        completion_tokens_cost=0.00027  # $0.00027 per 1000 tokens
    ),
    DeepSeekModels.DEEPSEEK_REASONER: ModelPricing(
        prompt_tokens_cost=0.00014,  # $0.00014 per 1000 tokens
        completion_tokens_cost=0.00219  # $0.00219 per 1000 tokens
    ),
    DeepSeekModels.DEEPSEEK_R1_GLOBAL: ModelPricing(
        prompt_tokens_cost=0.00135,  # $0.00135 per 1000 tokens
        completion_tokens_cost=0.0054  # $0.0054 per 1000 tokens
    ),
    DeepSeekModels.DEEPSEEK_R1_DATAZONE: ModelPricing(
        prompt_tokens_cost=0.001485,  # $0.001485 per 1000 tokens
        completion_tokens_cost=0.00594  # $0.00594 per 1000 tokens
    ),
    DeepSeekModels.DEEPSEEK_V3_2_EXP: ModelPricing(
        prompt_tokens_cost=0.000028,  # $0.000028 per 1000 tokens
        completion_tokens_cost=0.00042  # $0.00042 per 1000 tokens
    ),
}
