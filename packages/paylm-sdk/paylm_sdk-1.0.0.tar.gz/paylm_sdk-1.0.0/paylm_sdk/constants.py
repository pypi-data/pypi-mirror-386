"""
Model constants for the Paylm SDK.

This module provides predefined constants for AI models and service providers
to make it easier for users to reference models without hardcoding strings.

For the Go SDK equivalent, see: https://github.com/paylm/paylm-sdk-go
"""

# Service Provider Constants
class ServiceProvider:
    """Service provider constants for external access."""
    OPENAI = "OpenAI"
    ANTHROPIC = "Anthropic"
    GOOGLE_DEEPMIND = "Google DeepMind"
    META = "Meta"
    AWS = "AWS"
    MISTRAL_AI = "Mistral AI"
    COHERE = "Cohere"
    DEEPSEEK = "DeepSeek"
    CUSTOM = "Custom"


# OpenAI Models
class OpenAIModels:
    """OpenAI model constants."""
    # GPT-5 Series
    GPT_5 = "gpt-5"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5_NANO = "gpt-5-nano"
    GPT_5_CHAT_LATEST = "gpt-5-chat-latest"
    GPT_5_CODEX = "gpt-5-codex"
    GPT_5_PRO = "gpt-5-pro"
    GPT_5_SEARCH_API = "gpt-5-search-api"
    
    # GPT-4.1 Series
    GPT_4_1 = "gpt-4.1"
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1_NANO = "gpt-4.1-nano"
    
    # GPT-4o Series
    GPT_4O = "gpt-4o"
    GPT_4O_2024_05_13 = "gpt-4o-2024-05-13"
    GPT_4O_MINI = "gpt-4o-mini"
    
    # Realtime Models
    GPT_REALTIME = "gpt-realtime"
    GPT_REALTIME_MINI = "gpt-realtime-mini"
    GPT_4O_REALTIME_PREVIEW = "gpt-4o-realtime-preview"
    GPT_4O_MINI_REALTIME_PREVIEW = "gpt-4o-mini-realtime-preview"
    
    # Audio Models
    GPT_AUDIO = "gpt-audio"
    GPT_AUDIO_MINI = "gpt-audio-mini"
    GPT_4O_AUDIO_PREVIEW = "gpt-4o-audio-preview"
    GPT_4O_MINI_AUDIO_PREVIEW = "gpt-4o-mini-audio-preview"
    
    # O-Series Models
    O1 = "o1"
    O1_PRO = "o1-pro"
    O3_PRO = "o3-pro"
    O3 = "o3"
    O3_DEEP_RESEARCH = "o3-deep-research"
    O4_MINI = "o4-mini"
    O4_MINI_DEEP_RESEARCH = "o4-mini-deep-research"
    O3_MINI = "o3-mini"
    O1_MINI = "o1-mini"
    
    # Other Models
    CODEX_MINI_LATEST = "codex-mini-latest"
    GPT_4O_MINI_SEARCH_PREVIEW = "gpt-4o-mini-search-preview"
    GPT_4O_SEARCH_PREVIEW = "gpt-4o-search-preview"
    COMPUTER_USE_PREVIEW = "computer-use-preview"
    CHATGPT_4O_LATEST = "chatgpt-4o-latest"
    
    # GPT-4 Turbo
    GPT_4_TURBO_2024_04_09 = "gpt-4-turbo-2024-04-09"
    GPT_4_0125_PREVIEW = "gpt-4-0125-preview"
    GPT_4_1106_PREVIEW = "gpt-4-1106-preview"
    GPT_4_1106_VISION_PREVIEW = "gpt-4-1106-vision-preview"
    GPT_4_0613 = "gpt-4-0613"
    GPT_4_0314 = "gpt-4-0314"
    GPT_4_32K = "gpt-4-32k"
    
    # GPT-3.5 Series
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_3_5_TURBO_0125 = "gpt-3.5-turbo-0125"
    GPT_3_5_TURBO_1106 = "gpt-3.5-turbo-1106"
    GPT_3_5_TURBO_0613 = "gpt-3.5-turbo-0613"
    GPT_3_5_0301 = "gpt-3.5-0301"
    GPT_3_5_TURBO_INSTRUCT = "gpt-3.5-turbo-instruct"
    GPT_3_5_TURBO_16K_0613 = "gpt-3.5-turbo-16k-0613"
    
    # Legacy Models
    DAVINCI_002 = "davinci-002"
    BABBAGE_002 = "babbage-002"


# Anthropic Models
class AnthropicModels:
    """Anthropic model constants."""
    SONNET_4_5 = "Sonnet 4.5"
    HAIKU_4_5 = "Haiku 4.5"
    OPUS_4_1 = "Opus 4.1"
    SONNET_4 = "Sonnet 4"
    OPUS_4 = "Opus 4"
    SONNET_3_7 = "Sonnet 3.7"
    HAIKU_3_5 = "Haiku 3.5"
    OPUS_3 = "Opus 3"
    HAIKU_3 = "Haiku 3"


# Google DeepMind Models
class GoogleDeepMindModels:
    """Google DeepMind model constants."""
    GEMINI_2_5_PRO = "Gemini 2.5 Pro"
    GEMINI_2_5_FLASH = "Gemini 2.5 Flash"
    GEMINI_2_5_FLASH_PREVIEW = "Gemini 2.5 Flash Preview"
    GEMINI_2_5_FLASH_LITE = "Gemini 2.5 Flash-Lite"
    GEMINI_2_5_FLASH_LITE_PREVIEW = "Gemini 2.5 Flash-Lite Preview"
    GEMINI_2_5_FLASH_NATIVE_AUDIO = "Gemini 2.5 Flash Native Audio"
    GEMINI_2_5_FLASH_IMAGE = "Gemini 2.5 Flash Image"
    GEMINI_2_5_FLASH_PREVIEW_TTS = "Gemini 2.5 Flash Preview TTS"
    GEMINI_2_5_PRO_PREVIEW_TTS = "Gemini 2.5 Pro Preview TTS"
    GEMINI_2_5_COMPUTER_USE_PREVIEW = "Gemini 2.5 Computer Use Preview"


# Meta Models
class MetaModels:
    """Meta model constants."""
    # Llama 4 Series
    LLAMA_4_MAVERICK = "Llama 4 Maverick"
    LLAMA_4_SCOUT = "Llama 4 Scout"
    
    # Llama 3.3 Series
    LLAMA_3_3_70B_INSTRUCT_TURBO = "Llama 3.3 70B Instruct-Turbo"
    
    # Llama 3.2 Series
    LLAMA_3_2_3B_INSTRUCT_TURBO = "Llama 3.2 3B Instruct Turbo"
    
    # Llama 3.1 Series
    LLAMA_3_1_405B_INSTRUCT_TURBO = "Llama 3.1 405B Instruct Turbo"
    LLAMA_3_1_70B_INSTRUCT_TURBO = "Llama 3.1 70B Instruct Turbo"
    LLAMA_3_1_8B_INSTRUCT_TURBO = "Llama 3.1 8B Instruct Turbo"
    
    # Llama 3 Series
    LLAMA_3_70B_INSTRUCT_TURBO = "Llama 3 70B Instruct Turbo"
    LLAMA_3_70B_INSTRUCT_REFERENCE = "Llama 3 70B Instruct Reference"
    LLAMA_3_8B_INSTRUCT_LITE = "Llama 3 8B Instruct Lite"
    
    # Llama 2
    LLAMA_2 = "LLaMA-2"
    
    # Llama Guard Series
    LLAMA_GUARD_4_12B = "Llama Guard 4 12B"
    LLAMA_GUARD_3_11B_VISION_TURBO = "Llama Guard 3 11B Vision Turbo"
    LLAMA_GUARD_3_8B = "Llama Guard 3 8B"
    LLAMA_GUARD_2_8B = "Llama Guard 2 8B"
    
    # Salesforce
    SALESFORCE_LLAMA_RANK_V1_8B = "Salesforce Llama Rank V1 (8B)"


# AWS Models
class AWSModels:
    """AWS model constants."""
    AMAZON_NOVA_MICRO = "Amazon Nova Micro"
    AMAZON_NOVA_LITE = "Amazon Nova Lite"
    AMAZON_NOVA_PRO = "Amazon Nova Pro"


# Mistral AI Models
class MistralAIModels:
    """Mistral AI model constants."""
    MISTRAL_7B_INSTRUCT = "Mistral 7B Instruct"
    MISTRAL_LARGE = "Mistral Large"
    MISTRAL_SMALL = "Mistral Small"
    MISTRAL_MEDIUM = "Mistral Medium"


# Cohere Models
class CohereModels:
    """Cohere model constants."""
    COMMAND_R7B = "Command R7B"
    COMMAND_R = "Command R"
    COMMAND_R_PLUS = "Command R+"
    COMMAND_A = "Command A"
    AYA_EXPANSE_8B_32B = "Aya Expanse (8B/32B)"


# DeepSeek Models
class DeepSeekModels:
    """DeepSeek model constants."""
    DEEPSEEK_CHAT = "DeepSeek Chat"
    DEEPSEEK_REASONER = "DeepSeek Reasoner"
    DEEPSEEK_R1_GLOBAL = "DeepSeek R1 Global"
    DEEPSEEK_R1_DATAZONE = "DeepSeek R1 DataZone"
    DEEPSEEK_V3_2_EXP = "DeepSeek V3.2-Exp"






def is_model_supported(model: str) -> bool:
    """
    Check if a model is supported by the SDK.
    
    Args:
        model: The model name
        
    Returns:
        True if the model is supported, False otherwise
    """
    # Import here to avoid circular dependency
    from .models import MODEL_PRICING
    return model in MODEL_PRICING
