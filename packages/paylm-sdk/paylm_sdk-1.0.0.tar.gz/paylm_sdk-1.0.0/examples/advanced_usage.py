"""
Advanced usage example for the Paylm SDK with token string functionality.
"""

import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from paylm_sdk import (
    Client, 
    UsageData, 
    UsageDataWithStrings,
    ServiceProvider,
    OpenAIModels,
    AnthropicModels,
    GoogleModels,
    MetaModels,
    MistralModels
)

def main():
    """Advanced usage example with both token counting methods."""
    # Create a new client with your API key
    client = Client.new_client_with_url(
        "pk_e0ea0d11bb7f0d174caf578d665454acff97bdb1f85c235af547ccd9a733ef35",
        "http://localhost:8080"
    )
    
    print("Example 1: Basic Usage with Pre-calculated Tokens")
    
    # Define usage data with pre-calculated tokens using constants
    usage_data = UsageData(
        service_provider=ServiceProvider.OPENAI,
        model=OpenAIModels.GPT_4,
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500
    )
    
    # Send usage data
    try:
        client.send_usage("agent-123", "customer-456", "chat-completion", usage_data)
        print("✓ Usage data sent successfully!")
    except Exception as e:
        print(f"✗ Failed to send usage: {e}")
    
    print("\nExample 2: Advanced Usage with Token String Counting")
    
    # Define usage data with prompt and output strings using constants
    usage_data_with_strings = UsageDataWithStrings(
        service_provider=ServiceProvider.OPENAI,
        model=OpenAIModels.GPT_3_5_TURBO,
        prompt_string="What is the capital of France? Please provide a detailed explanation.",
        output_string="The capital of France is Paris. Paris is located in the north-central part of France and is the country's largest city and economic center. It serves as the political, economic, and cultural hub of the nation."
    )
    
    # Send usage data (tokens will be automatically counted)
    try:
        client.send_usage_with_token_string(
            "agent-789", 
            "customer-101", 
            "question-answer", 
            usage_data_with_strings
        )
        print("✓ Usage data with token strings sent successfully!")
    except Exception as e:
        print(f"✗ Failed to send usage with token strings: {e}")
    
    print("\nExample 3: Different AI Models")
    
    # Test different AI models using constants
    models_to_test = [
        (AnthropicModels.CLAUDE_3_SONNET, ServiceProvider.ANTHROPIC, "Anthropic"),
        (GoogleModels.GEMINI_PRO, ServiceProvider.GOOGLE, "Google"),
        (MetaModels.LLAMA_3_8B, ServiceProvider.META, "Meta"),
        (MistralModels.MISTRAL_LARGE, ServiceProvider.MISTRAL, "Mistral")
    ]
    
    for model, provider, provider_name in models_to_test:
        usage_data_test = UsageDataWithStrings(
            service_provider=provider,
            model=model,
            prompt_string="Hello, how are you?",
            output_string="I'm doing well, thank you for asking! How can I help you today?"
        )
        
        try:
            client.send_usage_with_token_string(
                f"agent-{model.replace('-', '_')}", 
                "customer-test", 
                "greeting", 
                usage_data_test
            )
            print(f"✓ {provider_name} {model} usage sent successfully!")
        except Exception as e:
            print(f"✗ Failed to send usage for {provider_name} {model}: {e}")

if __name__ == "__main__":
    main()