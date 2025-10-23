"""
Paylm SDK for Python

A Python SDK for integrating with the Paylm API to track usage and costs for AI models.

For the Go SDK equivalent, see: https://github.com/paylm/paylm-sdk-go
"""

from .client import Client
from .models import UsageData, UsageDataWithStrings, APIRequest, ModelPricing, MODEL_PRICING
from .constants import (
    ServiceProvider,
    OpenAIModels,
    AnthropicModels,
    GoogleDeepMindModels,
    MetaModels,
    AWSModels,
    MistralAIModels,
    CohereModels,
    DeepSeekModels,
    is_model_supported
)

__version__ = "1.0.0"
__all__ = [
    # Core classes
    "Client",
    "UsageData", 
    "UsageDataWithStrings", 
    "APIRequest", 
    "ModelPricing",
    "MODEL_PRICING",
    
    # Constants
    "ServiceProvider",
    "OpenAIModels",
    "AnthropicModels", 
    "GoogleDeepMindModels",
    "MetaModels",
    "AWSModels",
    "MistralAIModels",
    "CohereModels",
    "DeepSeekModels",
    
    # Utility functions
    "is_model_supported"
]
