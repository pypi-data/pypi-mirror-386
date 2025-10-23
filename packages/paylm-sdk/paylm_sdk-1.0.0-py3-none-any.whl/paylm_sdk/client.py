"""
Main client implementation for the Paylm SDK.
"""

import json
import logging
import time
from typing import Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    import tiktoken
except ImportError:
    tiktoken = None

from .models import UsageData, UsageDataWithStrings, APIRequest, ModelPricing, MODEL_PRICING


class Client:
    """Paylm SDK client for tracking usage and costs for AI models."""

    def __init__(self, api_key: str, base_url: str = "http://13.201.118.45:8080"):
        """
        Initialize the Paylm SDK client.

        Args:
            api_key: Your Paylm API key
            base_url: Base URL for the Paylm API (default: http://13.201.118.45:8080)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        
        # Setup logging
        self.logger = logging.getLogger(f"paylm_sdk.{id(self)}")
        self.logger.setLevel(logging.INFO)
        
        # Add console handler if no handlers exist
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Setup HTTP client with retry strategy
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default timeout
        self.session.timeout = 30

    @classmethod
    def new_client(cls, api_key: str) -> 'Client':
        """
        Create a new Paylm SDK client with the default API URL.
        
        Args:
            api_key: Your Paylm API key
            
        Returns:
            Client instance
        """
        return cls(api_key)

    @classmethod
    def new_client_with_url(cls, api_key: str, base_url: str) -> 'Client':
        """
        Create a new Paylm SDK client with a custom base URL.
        
        Args:
            api_key: Your Paylm API key
            base_url: Custom base URL for the Paylm API
            
        Returns:
            Client instance
        """
        return cls(api_key, base_url)

    def _calculate_cost(self, model: str, usage_data: UsageData) -> float:
        """
        Calculate the cost based on model and usage data.
        
        Args:
            model: The AI model name
            usage_data: Usage data containing token counts
            
        Returns:
            Calculated cost in USD
        """
        pricing = MODEL_PRICING.get(model)
        if not pricing:
            self.logger.warning(f"Unknown model '{model}', using default pricing")
            # Use default pricing for unknown models (per 1000 tokens)
            pricing = ModelPricing(
                prompt_tokens_cost=0.0001,  # $0.10 per 1000 tokens
                completion_tokens_cost=0.0001  # $0.10 per 1000 tokens
            )

        # Calculate cost per 1000 tokens
        prompt_cost = (usage_data.prompt_tokens / 1000.0) * pricing.prompt_tokens_cost
        completion_cost = (usage_data.completion_tokens / 1000.0) * pricing.completion_tokens_cost
        total_cost = prompt_cost + completion_cost

        self.logger.debug(
            f"Cost calculation for model '{model}': "
            f"prompt_tokens={usage_data.prompt_tokens} ({prompt_cost:.6f}), "
            f"completion_tokens={usage_data.completion_tokens} ({completion_cost:.6f}), "
            f"total={total_cost:.6f}"
        )

        return total_cost

    def send_usage(
        self, 
        agent_id: str, 
        customer_id: str, 
        indicator: str, 
        usage_data: UsageData
    ) -> None:
        """
        Send usage data to the Paylm API.
        
        Args:
            agent_id: Unique identifier for the agent
            customer_id: Unique identifier for the customer
            indicator: Indicator for the usage event
            usage_data: Usage data containing model and token information
            
        Raises:
            requests.RequestException: If the HTTP request fails
            ValueError: If the usage data is invalid
        """
        self.logger.info(
            f"Starting sendUsage for agentID={agent_id}, customerID={customer_id}, "
            f"indicator={indicator}, model={usage_data.model}"
        )

        # Calculate cost
        try:
            cost = self._calculate_cost(usage_data.model, usage_data)
        except Exception as e:
            self.logger.error(f"Failed to calculate cost: {e}")
            raise ValueError(f"Failed to calculate cost: {e}") from e

        self.logger.info(f"Calculated cost: {cost:.6f} for model {usage_data.model}")

        # Prepare API request
        api_request = APIRequest(
            agent_id=agent_id,
            customer_id=customer_id,
            indicator=indicator,
            amount=cost
        )

        # Prepare request data
        request_data = {
            "agentId": api_request.agent_id,
            "customerId": api_request.customer_id,
            "indicator": api_request.indicator,
            "amount": api_request.amount,
            "inputToken": usage_data.prompt_tokens,
            "outputToken": usage_data.completion_tokens,
            "model": usage_data.model,
            "serviceProvider": usage_data.service_provider
        }

        self.logger.debug(f"API request body: {json.dumps(request_data)}")

        # Create HTTP request
        url = urljoin(self.base_url, "/api/v1/usage")
        
        headers = {
            "Content-Type": "application/json",
            "paylm-api-key": self.api_key
        }

        self.logger.debug(f"Making HTTP POST request to: {url}")

        try:
            # Make HTTP request
            response = self.session.post(
                url,
                json=request_data,
                headers=headers,
                timeout=30
            )
            
            self.logger.debug(
                f"API response status: {response.status_code}, "
                f"body: {response.text}"
            )

            # Check response status
            if 200 <= response.status_code < 300:
                self.logger.info(
                    f"Successfully sent usage data for agentID={agent_id}, "
                    f"customerID={customer_id}, cost={cost:.6f}"
                )
                return

            # Handle error response
            self.logger.error(
                f"API request failed with status {response.status_code}: {response.text}"
            )
            response.raise_for_status()

        except requests.RequestException as e:
            self.logger.error(f"HTTP request failed: {e}")
            raise

    def set_log_level(self, level: int) -> None:
        """
        Set the logging level for the client.
        
        Args:
            level: Logging level (e.g., logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR)
        """
        self.logger.setLevel(level)

    def get_logger(self) -> logging.Logger:
        """
        Get the logger instance for custom logging.
        
        Returns:
            Logger instance
        """
        return self.logger

    def _get_token_count(self, model: str, text: str) -> int:
        """
        Get token count for a given model and text.
        Supports OpenAI, Anthropic, Google, Meta, AWS, Mistral, Cohere, DeepSeek
        
        Args:
            model: The AI model name
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        if not text:
            return 0

        if not tiktoken:
            self.logger.warning("tiktoken not available, using fallback token counting")
            return self._fallback_token_count(text)

        model_lower = model.lower()

        try:
            # OpenAI GPT models
            if model_lower.startswith("gpt-"):
                encoding = tiktoken.encoding_for_model(model)
                return len(encoding.encode(text))
            
            # Anthropic Claude models
            elif model_lower.startswith("claude-"):
                encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(text))
            
            # Google DeepMind Gemini models
            elif model_lower.startswith("gemini-"):
                encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(text))
            
            # Meta Llama models
            elif model_lower.startswith("llama-"):
                encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(text))
            
            # AWS Titan models
            elif model_lower.startswith("titan-"):
                encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(text))
            
            # Mistral models
            elif model_lower.startswith("mistral-"):
                encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(text))
            
            # Cohere models
            elif model_lower.startswith("command"):
                encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(text))
            
            # DeepSeek models
            elif model_lower.startswith("deepseek-"):
                encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(text))
            
            # Default fallback
            else:
                self.logger.warning(f"Unknown model '{model}', using cl100k_base encoding")
                encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(text))

        except Exception as e:
            self.logger.warning(f"Failed to get token count for model {model}: {e}, using fallback")
            return self._fallback_token_count(text)

    def _fallback_token_count(self, text: str) -> int:
        """
        Fallback token counting method using word-based estimation.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated number of tokens
        """
        # Simple word-based estimation: 1.3 tokens per word
        word_count = len(text.split())
        return int(word_count * 1.3)

    def _calculate_cost_from_strings(self, model: str, usage_data: UsageDataWithStrings) -> float:
        """
        Calculate the cost based on model and usage data with strings.
        
        Args:
            model: The AI model name
            usage_data: Usage data containing prompt and output strings
            
        Returns:
            Calculated cost in USD
        """
        # Count tokens
        prompt_tokens = self._get_token_count(model, usage_data.prompt_string)
        completion_tokens = self._get_token_count(model, usage_data.output_string)
        total_tokens = prompt_tokens + completion_tokens

        self.logger.debug(
            f"Token counting for model '{model}': "
            f"prompt_tokens={prompt_tokens}, completion_tokens={completion_tokens}, "
            f"total_tokens={total_tokens}"
        )

        # Create UsageData for cost calculation
        usage_data_obj = UsageData(
            service_provider=usage_data.service_provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )

        return self._calculate_cost(model, usage_data_obj)

    def send_usage_with_token_string(
        self, 
        agent_id: str, 
        customer_id: str, 
        indicator: str, 
        usage_data: UsageDataWithStrings
    ) -> None:
        """
        Send usage data to the Paylm API using prompt and output strings.
        The function automatically counts tokens using proper tokenizers for each model provider and calculates costs.
        
        Args:
            agent_id: Unique identifier for the agent
            customer_id: Unique identifier for the customer
            indicator: Indicator for the usage event
            usage_data: Usage data containing prompt and output strings
            
        Raises:
            requests.RequestException: If the HTTP request fails
            ValueError: If the usage data is invalid
        """
        self.logger.info(
            f"Starting sendUsageWithTokenString for agentID={agent_id}, customerID={customer_id}, "
            f"indicator={indicator}, serviceProvider={usage_data.service_provider}, model={usage_data.model}"
        )

        # Calculate cost from strings
        try:
            cost = self._calculate_cost_from_strings(usage_data.model, usage_data)
        except Exception as e:
            self.logger.error(f"Failed to calculate cost from strings: {e}")
            raise ValueError(f"Failed to calculate cost from strings: {e}") from e

        self.logger.info(f"Calculated cost: {cost:.6f} for model {usage_data.model} from strings")

        # Calculate token counts for API request
        prompt_tokens = self._get_token_count(usage_data.model, usage_data.prompt_string)
        completion_tokens = self._get_token_count(usage_data.model, usage_data.output_string)

        # Prepare API request
        api_request = APIRequest(
            agent_id=agent_id,
            customer_id=customer_id,
            indicator=indicator,
            amount=cost
        )

        # Prepare request data
        request_data = {
            "agentId": api_request.agent_id,
            "customerId": api_request.customer_id,
            "indicator": api_request.indicator,
            "amount": api_request.amount,
            "inputToken": prompt_tokens,
            "outputToken": completion_tokens,
            "model": usage_data.model,
            "serviceProvider": usage_data.service_provider
        }

        self.logger.debug(f"API request body: {json.dumps(request_data)}")

        # Create HTTP request
        url = urljoin(self.base_url, "/api/v1/usage")
        
        headers = {
            "Content-Type": "application/json",
            "paylm-api-key": self.api_key
        }

        self.logger.debug(f"Making HTTP POST request to: {url}")

        try:
            # Make HTTP request
            response = self.session.post(
                url,
                json=request_data,
                headers=headers,
                timeout=30
            )
            
            self.logger.debug(
                f"API response status: {response.status_code}, "
                f"body: {response.text}"
            )

            # Check response status
            if 200 <= response.status_code < 300:
                self.logger.info(
                    f"Successfully sent usage data from strings for agentID={agent_id}, "
                    f"customerID={customer_id}, cost={cost:.6f}"
                )
                return

            # Handle error response
            self.logger.error(
                f"API request failed with status {response.status_code}: {response.text}"
            )
            response.raise_for_status()

        except requests.RequestException as e:
            self.logger.error(f"HTTP request failed: {e}")
            raise
