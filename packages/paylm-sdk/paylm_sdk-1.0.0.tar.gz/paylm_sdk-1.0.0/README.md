# Paylm SDK for Python

A Python SDK for integrating with the Paylm API to track usage and costs for AI models.

## Installation

```bash
pip install paylm-sdk-python
```

## Usage

### Basic Usage

```python
import logging
from paylm_sdk import Client, UsageData

def main():
    # Create a new client with your API key
    client = Client.new_client("your-paylm-api-key")
    
    # Set log level (optional)
    client.set_log_level(logging.INFO)
    
    # Define usage data
    usage_data = UsageData(
        model="llama",
        prompt_tokens=756,
        completion_tokens=244,
        total_tokens=1000
    )
    
    # Send usage data
    try:
        client.send_usage("agent-123", "customer-456", "email-sent", usage_data)
        print("Usage data sent successfully!")
    except Exception as e:
        print(f"Failed to send usage: {e}")

if __name__ == "__main__":
    main()
```

### Using SendUsageWithTokenString

```python
import logging
from paylm_sdk import Client, UsageDataWithStrings

def main():
    # Create a new client
    client = Client.new_client_with_url("your-api-key", "http://localhost:8080")
    client.set_log_level(logging.INFO)
    
    # Define usage data with prompt and output strings
    usage_data = UsageDataWithStrings(
        service_provider="OpenAI",
        model="gpt-4",
        prompt_string="What is the capital of France? Please provide a detailed explanation.",
        output_string="The capital of France is Paris. Paris is located in the north-central part of France and is the country's largest city and economic center."
    )
    
    # Send usage data (tokens will be automatically counted)
    try:
        client.send_usage_with_token_string("agent-123", "customer-456", "question-answer", usage_data)
        print("Usage data sent successfully!")
    except Exception as e:
        print(f"Failed to send usage: {e}")

if __name__ == "__main__":
    main()
```

### Using Model Constants

The SDK provides predefined constants for all supported models and service providers:

```python
import logging
from paylm_sdk import (
    Client, 
    UsageData,
    OpenAIModels,
    AnthropicModels,
    ServiceProvider,
    is_model_supported
)

def main():
    client = Client.new_client("your-api-key")
    
    # Use model constants
    usage_data = UsageData(
        service_provider=ServiceProvider.OPENAI,
        model=OpenAIModels.GPT_4O,
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500
    )
    
    client.send_usage("agent-123", "customer-456", "chat-completion", usage_data)
    
    # Check if a model is supported
    if is_model_supported(OpenAIModels.GPT_5):
        print("GPT-5 is supported!")

if __name__ == "__main__":
    main()
```

#### Available Model Constants

- **OpenAI**: `OpenAIModels.GPT_5`, `OpenAIModels.GPT_4O`, `OpenAIModels.GPT_4O_MINI`, `OpenAIModels.O1`, `OpenAIModels.O3`, etc.
- **Anthropic**: `AnthropicModels.SONNET_4_5`, `AnthropicModels.HAIKU_4_5`, `AnthropicModels.OPUS_4_1`, etc.
- **Google DeepMind**: `GoogleDeepMindModels.GEMINI_2_5_PRO`, `GoogleDeepMindModels.GEMINI_2_5_FLASH`, etc.
- **Meta**: `MetaModels.LLAMA_4_MAVERICK`, `MetaModels.LLAMA_3_1_405B_INSTRUCT_TURBO`, etc.
- **AWS**: `AWSModels.AMAZON_NOVA_PRO`, `AWSModels.AMAZON_NOVA_LITE`, etc.
- **Mistral AI**: `MistralAIModels.MISTRAL_LARGE`, `MistralAIModels.MISTRAL_MEDIUM`, etc.
- **Cohere**: `CohereModels.COMMAND_R_PLUS`, `CohereModels.COMMAND_R`, etc.
- **DeepSeek**: `DeepSeekModels.DEEPSEEK_R1_GLOBAL`, `DeepSeekModels.DEEPSEEK_REASONER`, etc.

### Advanced Usage

```python
import logging
from paylm_sdk import Client, UsageData, UsageDataWithStrings

def main():
    # Create client with custom base URL
    client = Client.new_client_with_url("your-api-key", "https://custom-api.paylm.com")
    
    # Set debug logging
    client.set_log_level(logging.DEBUG)
    
    # Get logger for custom logging
    logger = client.get_logger()
    logger.info("Starting usage tracking...")
    
    # Method 1: Send usage data with pre-calculated tokens
    usage_data = UsageData(
        model="gpt-4",
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500
    )
    
    try:
        client.send_usage("agent-789", "customer-101", "chat-completion", usage_data)
        logger.info("Usage data sent successfully!")
    except Exception as e:
        logger.error(f"Failed to send usage: {e}")
    
    # Method 2: Send usage data with automatic token counting
    usage_data_strings = UsageDataWithStrings(
        service_provider="Anthropic",
        model="claude-3-sonnet",
        prompt_string="Hello, how are you?",
        output_string="I'm doing well, thank you for asking!"
    )
    
    try:
        client.send_usage_with_token_string("agent-789", "customer-101", "greeting", usage_data_strings)
        logger.info("Usage data with token strings sent successfully!")
    except Exception as e:
        logger.error(f"Failed to send usage with token strings: {e}")

if __name__ == "__main__":
    main()
```

## API Reference

### Client

#### `Client.new_client(api_key: str) -> Client`
Creates a new Paylm SDK client with the default API URL.

#### `Client.new_client_with_url(api_key: str, base_url: str) -> Client`
Creates a new Paylm SDK client with a custom base URL.

#### `send_usage(agent_id: str, customer_id: str, indicator: str, usage_data: UsageData) -> None`
Sends usage data to the Paylm API with pre-calculated token counts. Raises an exception if the request fails.

#### `send_usage_with_token_string(agent_id: str, customer_id: str, indicator: str, usage_data: UsageDataWithStrings) -> None`
Sends usage data to the Paylm API using prompt and output strings. The function automatically counts tokens using proper tokenizers for each model provider and calculates costs. Raises an exception if the request fails.

#### `set_log_level(level: int) -> None`
Sets the logging level for the client.

#### `get_logger() -> logging.Logger`
Returns the logger instance for custom logging.

### Types

#### `UsageData`
```python
@dataclass
class UsageData:
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
```

#### `UsageDataWithStrings`
```python
@dataclass
class UsageDataWithStrings:
    service_provider: str
    model: str
    prompt_string: str
    output_string: str
```

## Supported Models

The SDK includes built-in pricing for models from the following providers:

### OpenAI
- `gpt-3.5-turbo` - $1.50 prompt, $2.00 completion (per 1000 tokens)
- `gpt-3.5-turbo-16k` - $3.00 prompt, $4.00 completion (per 1000 tokens)
- `gpt-4` - $30.00 prompt, $60.00 completion (per 1000 tokens)
- `gpt-4-turbo` - $10.00 prompt, $30.00 completion (per 1000 tokens)
- `gpt-4o` - $5.00 prompt, $15.00 completion (per 1000 tokens)
- `gpt-4o-mini` - $0.15 prompt, $0.60 completion (per 1000 tokens)

### Anthropic
- `claude-3-haiku` - $0.25 prompt, $1.25 completion (per 1000 tokens)
- `claude-3-sonnet` - $3.00 prompt, $15.00 completion (per 1000 tokens)
- `claude-3-opus` - $15.00 prompt, $75.00 completion (per 1000 tokens)
- `claude-3.5-sonnet` - $3.00 prompt, $15.00 completion (per 1000 tokens)

### Google DeepMind
- `gemini-pro` - $0.50 prompt, $1.50 completion (per 1000 tokens)
- `gemini-1.5-pro` - $1.25 prompt, $5.00 completion (per 1000 tokens)
- `gemini-1.5-flash` - $0.075 prompt, $0.30 completion (per 1000 tokens)

### Meta
- `llama-2-7b` - $0.10 per 1000 tokens
- `llama-2-13b` - $0.20 per 1000 tokens
- `llama-2-70b` - $0.70 per 1000 tokens
- `llama-3-8b` - $0.10 per 1000 tokens
- `llama-3-70b` - $0.70 per 1000 tokens

### AWS
- `claude-3-haiku-aws` - $0.25 prompt, $1.25 completion (per 1000 tokens)
- `claude-3-sonnet-aws` - $3.00 prompt, $15.00 completion (per 1000 tokens)
- `titan-text-express` - $0.80 prompt, $1.60 completion (per 1000 tokens)

### Mistral AI
- `mistral-7b` - $0.10 per 1000 tokens
- `mistral-large` - $2.00 prompt, $6.00 completion (per 1000 tokens)

### Cohere
- `command` - $1.50 prompt, $2.00 completion (per 1000 tokens)
- `command-r-plus` - $3.00 prompt, $15.00 completion (per 1000 tokens)

### DeepSeek
- `deepseek-chat` - $0.10 prompt, $0.20 completion (per 1000 tokens)

For unknown models, the SDK will use default pricing of $0.10 per 1000 tokens.

## Token Counting

The SDK uses accurate token counting for different model providers:

- **OpenAI GPT models**: Uses the official tiktoken library with model-specific encodings
- **Anthropic Claude models**: Uses cl100k_base encoding (same as GPT-4)
- **Google Gemini models**: Uses cl100k_base encoding as approximation
- **Meta Llama models**: Uses cl100k_base encoding as approximation
- **Mistral models**: Uses cl100k_base encoding as approximation
- **Cohere models**: Uses cl100k_base encoding as approximation
- **DeepSeek models**: Uses cl100k_base encoding as approximation
- **AWS Titan models**: Uses cl100k_base encoding as approximation
- **Unknown models**: Falls back to word-based estimation (1.3 tokens per word)

The token counting is performed automatically when using `send_usage_with_token_string()`.

## Logging

The SDK uses Python's built-in logging module. You can control the log level and access the logger for custom logging.

```python
import logging

# Set log level
client.set_log_level(logging.DEBUG)

# Get logger for custom logging
logger = client.get_logger()
logger.info("Custom log message")
```

## Authentication

The SDK uses the `paylm-api-key` header for authentication. Make sure to provide a valid API key when creating the client.

## Error Handling

The SDK raises appropriate exceptions for various failure scenarios:

- `requests.RequestException` - Network and HTTP errors
- `ValueError` - Invalid usage data or cost calculation errors

```python
try:
    client.send_usage("agent-123", "customer-456", "test", usage_data)
except requests.RequestException as e:
    print(f"Network error: {e}")
except ValueError as e:
    print(f"Invalid data: {e}")
```

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Running Examples

```bash
# Basic usage
python examples/basic_usage.py

# Advanced usage
python examples/advanced_usage.py
```

## License

MIT
